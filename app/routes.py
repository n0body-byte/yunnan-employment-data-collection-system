
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.enums import (
    AnalysisDimension,
    AuditAction,
    ExchangeDirection,
    FilingStatus,
    PermissionCode,
    ReviewStatus,
    UserRole,
)
from app.models import (
    DataExchangeLog,
    Enterprise,
    EmploymentReport,
    EmploymentReportRevision,
    ManagedRole,
    Notification,
    Permission,
    ReportingWindowConfig,
    User,
)
from app.schemas import (
    ComparisonAnalysisRequest,
    ComparisonAnalysisRowRead,
    DataExchangeLogRead,
    EmploymentReportAuditRequest,
    EmploymentReportRead,
    EmploymentReportRevisionCreate,
    EmploymentReportRevisionRead,
    EmploymentReportSubmit,
    EnterpriseFilingSubmit,
    EnterpriseRead,
    FilingAuditRequest,
    LoginRequest,
    LoginResponse,
    ManagedRoleCreate,
    ManagedRoleRead,
    ManagedRoleUpdate,
    MonthlyJobChangeTrendRead,
    NotificationCreate,
    NotificationRead,
    NotificationUpdate,
    PasswordChangeRequest,
    PermissionRead,
    ProvinceAggregateSummaryRead,
    ProvinceCityStatisticsRead,
    ReportingWindowConfigRead,
    ReportingWindowConfigUpsert,
    SystemMonitorRead,
    UserCreate,
    UserQueryExportRead,
    UserRead,
    UserUpdate,
)
from app.security import create_access_token, hash_password, verify_password
from app.services.exporters import (
    export_enterprise_filings_to_xlsx,
    export_report_list_to_xlsx,
    export_user_list_to_xlsx,
)

router = APIRouter(prefix="/api", tags=["core-business"])

DEFAULT_PERMISSION_MAP: dict[UserRole, set[PermissionCode]] = {
    UserRole.PROVINCE: {
        PermissionCode.PASSWORD_CHANGE,
        PermissionCode.PROVINCE_FILING_REVIEW,
        PermissionCode.PROVINCE_ENTERPRISE_QUERY,
        PermissionCode.PROVINCE_REPORT_MANAGE,
        PermissionCode.PROVINCE_DATA_MODIFY,
        PermissionCode.PROVINCE_DATA_DELETE,
        PermissionCode.PROVINCE_DATA_SUMMARY,
        PermissionCode.PROVINCE_DATA_EXPORT,
        PermissionCode.PROVINCE_MULTI_ANALYSIS,
        PermissionCode.PROVINCE_CHART_ANALYSIS,
        PermissionCode.NOTICE_BROWSE,
        PermissionCode.NOTICE_MANAGE,
        PermissionCode.REPORTING_WINDOW_MANAGE,
        PermissionCode.USER_MANAGE,
        PermissionCode.ROLE_MANAGE,
        PermissionCode.SYSTEM_MONITOR,
        PermissionCode.NATIONAL_EXCHANGE,
    },
    UserRole.CITY: {
        PermissionCode.PASSWORD_CHANGE,
        PermissionCode.CITY_REPORT_AUDIT,
        PermissionCode.CITY_NOTICE_MANAGE,
        PermissionCode.NOTICE_BROWSE,
    },
    UserRole.ENTERPRISE: {
        PermissionCode.PASSWORD_CHANGE,
        PermissionCode.ENTERPRISE_INFO_EDIT,
        PermissionCode.ENTERPRISE_FILING_SUBMIT,
        PermissionCode.ENTERPRISE_REPORT_SUBMIT,
        PermissionCode.ENTERPRISE_REPORT_QUERY,
        PermissionCode.NOTICE_BROWSE,
    },
}

PERMISSION_DESCRIPTIONS: dict[PermissionCode, str] = {
    PermissionCode.ENTERPRISE_INFO_EDIT: "Edit enterprise profile information",
    PermissionCode.ENTERPRISE_FILING_SUBMIT: "Submit enterprise filing",
    PermissionCode.ENTERPRISE_REPORT_SUBMIT: "Submit employment reports",
    PermissionCode.ENTERPRISE_REPORT_QUERY: "Query own historical reports",
    PermissionCode.PASSWORD_CHANGE: "Change own password",
    PermissionCode.CITY_REPORT_AUDIT: "Audit reports at city level",
    PermissionCode.CITY_NOTICE_MANAGE: "Create and manage city notifications",
    PermissionCode.PROVINCE_FILING_REVIEW: "Review enterprise filings",
    PermissionCode.PROVINCE_ENTERPRISE_QUERY: "Query filed enterprises",
    PermissionCode.PROVINCE_REPORT_MANAGE: "Manage province reports",
    PermissionCode.PROVINCE_DATA_MODIFY: "Modify reported data with revision logs",
    PermissionCode.PROVINCE_DATA_DELETE: "Delete historical data",
    PermissionCode.PROVINCE_DATA_SUMMARY: "View province aggregate summaries",
    PermissionCode.PROVINCE_DATA_EXPORT: "Export enterprise and report data",
    PermissionCode.PROVINCE_MULTI_ANALYSIS: "View sample distribution analysis",
    PermissionCode.PROVINCE_CHART_ANALYSIS: "View chart comparison and trend analysis",
    PermissionCode.NOTICE_BROWSE: "Browse notifications",
    PermissionCode.NOTICE_MANAGE: "Create and manage notifications",
    PermissionCode.REPORTING_WINDOW_MANAGE: "Maintain reporting windows",
    PermissionCode.USER_MANAGE: "Manage users",
    PermissionCode.ROLE_MANAGE: "Manage roles and permissions",
    PermissionCode.SYSTEM_MONITOR: "View system monitoring data",
    PermissionCode.NATIONAL_EXCHANGE: "Exchange data with national system",
}

DEFAULT_MANAGED_ROLES: dict[str, dict[str, object]] = {
    "Province Administrator": {
        "scope_role": UserRole.PROVINCE,
        "description": "Default province-level administrator role",
        "permissions": sorted(DEFAULT_PERMISSION_MAP[UserRole.PROVINCE], key=lambda item: item.value),
    },
    "City Auditor": {
        "scope_role": UserRole.CITY,
        "description": "Default city-level auditing role",
        "permissions": sorted(DEFAULT_PERMISSION_MAP[UserRole.CITY], key=lambda item: item.value),
    },
    "Enterprise Operator": {
        "scope_role": UserRole.ENTERPRISE,
        "description": "Default enterprise operator role",
        "permissions": sorted(DEFAULT_PERMISSION_MAP[UserRole.ENTERPRISE], key=lambda item: item.value),
    },
}


@dataclass
class EffectiveReportData:
    report_id: int
    enterprise_id: int
    enterprise_name: str
    region: str
    nature: str
    industry: str
    baseline_employees: int
    current_employees: int
    report_month: str
    review_status: ReviewStatus
    reduction_type: object | None
    primary_reason: object | None
    primary_reason_detail: str | None
    secondary_reason: object | None
    secondary_reason_detail: str | None
    third_reason: object | None
    third_reason_detail: str | None
    return_remark: str | None
    submitted_at: datetime | None
    city_audited_at: datetime | None
    province_audited_at: datetime | None
    reported_to_ministry_at: datetime | None
    deleted_at: datetime | None
    delete_remark: str | None
    created_at: datetime
    updated_at: datetime


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _region_is_manageable(manager_region: str, target_region: str) -> bool:
    manager_region = manager_region.strip()
    target_region = target_region.strip()
    return target_region == manager_region or target_region.startswith(f"{manager_region}/") or target_region.startswith(manager_region)


def _region_scope_expression(region_column, region: str):
    return or_(region_column == region, region_column.startswith(region), region_column.startswith(f"{region}/"))


def _ensure_acl_seeded(db: Session) -> None:
    existing_permissions = {item.code for item in db.scalars(select(Permission)).all()}
    for code, description in PERMISSION_DESCRIPTIONS.items():
        if code not in existing_permissions:
            db.add(Permission(code=code, description=description))
    db.flush()

    existing_roles = {item.name: item for item in db.scalars(select(ManagedRole).options(selectinload(ManagedRole.permissions))).all()}
    changed = False
    for name, config in DEFAULT_MANAGED_ROLES.items():
        role = existing_roles.get(name)
        if role is None:
            role = ManagedRole(
                name=name,
                description=config["description"],
                scope_role=config["scope_role"],
                is_system=True,
            )
            db.add(role)
            db.flush()
            changed = True
        permission_codes = list(config["permissions"])
        permissions = db.scalars(select(Permission).where(Permission.code.in_(permission_codes))).all()
        current_codes = {item.code for item in role.permissions}
        if current_codes != set(permission_codes):
            role.permissions = permissions
            changed = True
    if changed:
        db.commit()

def _get_user_permissions(db: Session, user: User) -> set[PermissionCode]:
    _ensure_acl_seeded(db)
    permissions = set(DEFAULT_PERMISSION_MAP.get(user.role, set()))
    if user.managed_role_id is not None:
        managed_role = db.scalar(
            select(ManagedRole)
            .options(selectinload(ManagedRole.permissions))
            .where(ManagedRole.id == user.managed_role_id)
        )
        if managed_role is not None:
            permissions.update(item.code for item in managed_role.permissions)
    return permissions


def require_role(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        if not current_user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
        return current_user

    return dependency


def require_permission(*permission_codes: PermissionCode):
    def dependency(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> User:
        if not current_user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
        current_permissions = _get_user_permissions(db, current_user)
        missing = [code.value for code in permission_codes if code not in current_permissions]
        if missing:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permissions: {', '.join(missing)}")
        return current_user

    return dependency


def _get_enterprise_for_user(db: Session, user_id: int) -> Enterprise | None:
    return db.scalar(select(Enterprise).where(Enterprise.owner_user_id == user_id))


def _get_reporting_window(db: Session, report_month: str) -> ReportingWindowConfig | None:
    return db.scalar(select(ReportingWindowConfig).where(ReportingWindowConfig.report_month == report_month))


def _ensure_reporting_window_open(db: Session, report_month: str) -> None:
    config = _get_reporting_window(db, report_month)
    if config is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Reporting window is not configured for this month")
    now = _now_utc()
    start_at = config.start_at if config.start_at.tzinfo else config.start_at.replace(tzinfo=UTC)
    end_at = config.end_at if config.end_at.tzinfo else config.end_at.replace(tzinfo=UTC)
    if now < start_at or now > end_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Current time is outside the configured reporting window")


def _get_report_or_404(db: Session, report_id: int) -> EmploymentReport:
    report = db.scalar(
        select(EmploymentReport)
        .options(selectinload(EmploymentReport.enterprise), selectinload(EmploymentReport.revisions))
        .where(EmploymentReport.id == report_id)
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


def _latest_active_revision(report: EmploymentReport) -> EmploymentReportRevision | None:
    active = [item for item in report.revisions if item.is_active]
    if not active:
        return None
    return sorted(active, key=lambda item: (item.created_at, item.id), reverse=True)[0]


def _build_effective_report_data(report: EmploymentReport) -> EffectiveReportData:
    effective = _latest_active_revision(report) or report
    enterprise = report.enterprise
    return EffectiveReportData(
        report_id=report.id,
        enterprise_id=report.enterprise_id,
        enterprise_name=enterprise.name,
        region=enterprise.region,
        nature=enterprise.nature,
        industry=enterprise.industry,
        baseline_employees=effective.baseline_employees,
        current_employees=effective.current_employees,
        report_month=report.report_month,
        review_status=report.review_status,
        reduction_type=effective.reduction_type,
        primary_reason=effective.primary_reason,
        primary_reason_detail=effective.primary_reason_detail,
        secondary_reason=effective.secondary_reason,
        secondary_reason_detail=effective.secondary_reason_detail,
        third_reason=getattr(effective, "third_reason", None),
        third_reason_detail=getattr(effective, "third_reason_detail", None),
        return_remark=report.return_remark,
        submitted_at=report.submitted_at,
        city_audited_at=report.city_audited_at,
        province_audited_at=report.province_audited_at,
        reported_to_ministry_at=report.reported_to_ministry_at,
        deleted_at=report.deleted_at,
        delete_remark=report.delete_remark,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def _serialize_report(report: EmploymentReport) -> EmploymentReportRead:
    data = _build_effective_report_data(report)
    return EmploymentReportRead(
        id=data.report_id,
        enterprise_id=data.enterprise_id,
        baseline_employees=data.baseline_employees,
        current_employees=data.current_employees,
        reduction_type=data.reduction_type,
        primary_reason=data.primary_reason,
        primary_reason_detail=data.primary_reason_detail,
        secondary_reason=data.secondary_reason,
        secondary_reason_detail=data.secondary_reason_detail,
        third_reason=data.third_reason,
        third_reason_detail=data.third_reason_detail,
        report_month=data.report_month,
        review_status=data.review_status,
        return_remark=data.return_remark,
        submitted_at=data.submitted_at,
        city_audited_at=data.city_audited_at,
        province_audited_at=data.province_audited_at,
        reported_to_ministry_at=data.reported_to_ministry_at,
        deleted_at=data.deleted_at,
        delete_remark=data.delete_remark,
        created_at=data.created_at,
        updated_at=data.updated_at,
    )


def _apply_enterprise_scope(statement, current_user: User):
    if current_user.role == UserRole.PROVINCE:
        return statement
    if current_user.role == UserRole.CITY:
        return statement.where(_region_scope_expression(Enterprise.region, current_user.region))
    if current_user.role == UserRole.ENTERPRISE:
        return statement.where(Enterprise.owner_user_id == current_user.id)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported role")


def _apply_report_scope(statement, current_user: User):
    statement = statement.join(Enterprise, Enterprise.id == EmploymentReport.enterprise_id)
    if current_user.role == UserRole.PROVINCE:
        return statement
    if current_user.role == UserRole.CITY:
        return statement.where(_region_scope_expression(Enterprise.region, current_user.region))
    if current_user.role == UserRole.ENTERPRISE:
        return statement.where(Enterprise.owner_user_id == current_user.id)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported role")


def _load_reports_for_analysis(db: Session, report_months: list[str] | None = None) -> list[EmploymentReport]:
    statement = select(EmploymentReport).options(selectinload(EmploymentReport.enterprise), selectinload(EmploymentReport.revisions))
    statement = statement.where(EmploymentReport.deleted_at.is_(None))
    if report_months:
        statement = statement.where(EmploymentReport.report_month.in_(report_months))
    return db.scalars(statement).all()


def _query_visible_notifications(db: Session, current_user: User) -> list[Notification]:
    notifications = db.scalars(select(Notification).options(selectinload(Notification.publisher)).order_by(Notification.published_at.desc(), Notification.id.desc())).all()
    visible: list[Notification] = []
    for item in notifications:
        publisher = item.publisher
        if current_user.role == UserRole.PROVINCE or publisher.role == UserRole.PROVINCE:
            visible.append(item)
            continue
        if current_user.role == UserRole.CITY and publisher.role == UserRole.CITY and _region_is_manageable(current_user.region, publisher.region):
            visible.append(item)
            continue
        if current_user.role == UserRole.ENTERPRISE:
            if publisher.role == UserRole.CITY and _region_is_manageable(publisher.region, current_user.region):
                visible.append(item)
                continue
            if publisher.id == current_user.id:
                visible.append(item)
    return visible


@router.post("/auth/login", response_model=LoginResponse, status_code=status.HTTP_200_OK, summary="Login and issue JWT token")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    _ensure_acl_seeded(db)
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or user.role != payload.role or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username, password, or role")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    access_token = create_access_token(subject=str(user.id), role=user.role.value, region=user.region)
    return LoginResponse(access_token=access_token, role=user.role, region=user.region, managed_role_id=user.managed_role_id)


@router.post("/auth/change-password", status_code=status.HTTP_200_OK, summary="Change password")
def change_password(payload: PasswordChangeRequest, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PASSWORD_CHANGE))) -> dict[str, str]:
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.get("/permissions", response_model=list[PermissionRead], summary="List available permissions")
def list_permissions(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.ROLE_MANAGE))) -> list[Permission]:
    _ensure_acl_seeded(db)
    return db.scalars(select(Permission).order_by(Permission.code)).all()


@router.get("/roles", response_model=list[ManagedRoleRead], summary="List managed roles")
def list_roles(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.ROLE_MANAGE))) -> list[ManagedRole]:
    _ensure_acl_seeded(db)
    return db.scalars(select(ManagedRole).options(selectinload(ManagedRole.permissions)).order_by(ManagedRole.id)).all()


@router.post("/roles", response_model=ManagedRoleRead, status_code=status.HTTP_201_CREATED, summary="Create managed role")
def create_role(payload: ManagedRoleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.ROLE_MANAGE))) -> ManagedRole:
    role = ManagedRole(name=payload.name, description=payload.description, scope_role=payload.scope_role, is_system=False)
    role.permissions = db.scalars(select(Permission).where(Permission.code.in_(payload.permission_codes))).all()
    db.add(role)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role name already exists") from exc
    db.refresh(role)
    return db.scalar(select(ManagedRole).options(selectinload(ManagedRole.permissions)).where(ManagedRole.id == role.id))

@router.put("/roles/{role_id}", response_model=ManagedRoleRead, summary="Update managed role")
def update_role(role_id: int, payload: ManagedRoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.ROLE_MANAGE))) -> ManagedRole:
    role = db.scalar(select(ManagedRole).options(selectinload(ManagedRole.permissions)).where(ManagedRole.id == role_id))
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if payload.name is not None:
        role.name = payload.name
    if payload.description is not None:
        role.description = payload.description
    if payload.scope_role is not None:
        role.scope_role = payload.scope_role
    if payload.permission_codes is not None:
        role.permissions = db.scalars(select(Permission).where(Permission.code.in_(payload.permission_codes))).all()
    db.commit()
    db.refresh(role)
    return db.scalar(select(ManagedRole).options(selectinload(ManagedRole.permissions)).where(ManagedRole.id == role.id))


@router.delete("/roles/{role_id}", status_code=status.HTTP_200_OK, summary="Delete managed role")
def delete_role(role_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.ROLE_MANAGE))) -> dict[str, str]:
    role = db.get(ManagedRole, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    for user in db.scalars(select(User).where(User.managed_role_id == role_id)).all():
        user.managed_role_id = None
    db.delete(role)
    db.commit()
    return {"message": "Role deleted successfully"}


@router.get("/users", response_model=list[UserQueryExportRead], summary="List users")
def list_users(
    username: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    region: str | None = Query(default=None),
    enterprise_name: str | None = Query(default=None),
    filing_status: FilingStatus | None = Query(default=None),
    nature: str | None = Query(default=None),
    industry: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.USER_MANAGE)),
) -> list[User]:
    statement = select(User).outerjoin(Enterprise, Enterprise.owner_user_id == User.id)
    if username:
        statement = statement.where(User.username.contains(username))
    if role is not None:
        statement = statement.where(User.role == role)
    if region:
        statement = statement.where(_region_scope_expression(User.region, region))
    if enterprise_name:
        statement = statement.where(Enterprise.name.contains(enterprise_name))
    if filing_status is not None:
        statement = statement.where(Enterprise.filing_status == filing_status)
    if nature:
        statement = statement.where(Enterprise.nature.contains(nature))
    if industry:
        statement = statement.where(Enterprise.industry.contains(industry))
    if is_active is not None:
        statement = statement.where(User.is_active == is_active)
    if start_date is not None:
        statement = statement.where(User.created_at >= start_date)
    if end_date is not None:
        statement = statement.where(User.created_at <= end_date)
    return db.scalars(statement.order_by(User.created_at.desc(), User.id.desc())).unique().all()


@router.get("/users/export", status_code=status.HTTP_200_OK, summary="Export user query results")
def export_users(
    username: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    region: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.PROVINCE_DATA_EXPORT, PermissionCode.USER_MANAGE)),
) -> StreamingResponse:
    statement = select(User).order_by(User.created_at.desc(), User.id.desc())
    if username:
        statement = statement.where(User.username.contains(username))
    if role is not None:
        statement = statement.where(User.role == role)
    if region:
        statement = statement.where(_region_scope_expression(User.region, region))
    users = db.scalars(statement).all()
    file_content = export_user_list_to_xlsx(users)
    return StreamingResponse(BytesIO(file_content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": 'attachment; filename="users.xlsx"'})


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Create user")
def create_user(payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.USER_MANAGE))) -> User:
    user = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role, region=payload.region, managed_role_id=payload.managed_role_id, is_active=payload.is_active)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists") from exc
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserRead, summary="Update user")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.USER_MANAGE))) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.username is not None:
        user.username = payload.username
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    if payload.role is not None:
        user.role = payload.role
    if payload.region is not None:
        user.region = payload.region
    if payload.managed_role_id is not None:
        user.managed_role_id = payload.managed_role_id
    if payload.is_active is not None:
        user.is_active = payload.is_active
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists") from exc
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK, summary="Delete user")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.USER_MANAGE))) -> dict[str, str]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    enterprise = _get_enterprise_for_user(db, user.id)
    if enterprise is not None and db.scalar(select(EmploymentReport.id).where(EmploymentReport.enterprise_id == enterprise.id)) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User has reported data and cannot be deleted")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.get("/system/reporting-windows", response_model=list[ReportingWindowConfigRead], summary="List reporting windows")
def list_reporting_windows(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.REPORTING_WINDOW_MANAGE))) -> list[ReportingWindowConfig]:
    return db.scalars(select(ReportingWindowConfig).order_by(ReportingWindowConfig.report_month.desc())).all()


@router.get("/system/reporting-windows/{report_month}", response_model=ReportingWindowConfigRead, summary="Get one reporting window")
def get_reporting_window(report_month: str, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.PROVINCE, UserRole.CITY, UserRole.ENTERPRISE))) -> ReportingWindowConfig:
    config = _get_reporting_window(db, report_month)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reporting window was not found")
    return config


@router.post("/system/reporting-windows", response_model=ReportingWindowConfigRead, summary="Create or update reporting window")
def upsert_reporting_window(payload: ReportingWindowConfigUpsert, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.REPORTING_WINDOW_MANAGE))) -> ReportingWindowConfig:
    config = _get_reporting_window(db, payload.report_month)
    if config is None:
        config = ReportingWindowConfig(**payload.model_dump())
        db.add(config)
    else:
        config.start_at = payload.start_at
        config.end_at = payload.end_at
    db.commit()
    db.refresh(config)
    return config


@router.get("/system/monitor", response_model=SystemMonitorRead, summary="System resource monitor")
def get_system_monitor(current_user: User = Depends(require_permission(PermissionCode.SYSTEM_MONITOR))) -> SystemMonitorRead:
    try:
        import psutil
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="psutil is required") from exc
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return SystemMonitorRead(
        cpu_percent=float(psutil.cpu_percent(interval=0.3)),
        memory_percent=float(memory.percent),
        memory_used_bytes=int(memory.used),
        memory_total_bytes=int(memory.total),
        disk_percent=float(disk.percent),
        disk_used_bytes=int(disk.used),
        disk_total_bytes=int(disk.total),
        app_title=settings.app_title,
        current_time=_now_utc(),
    )


@router.get("/enterprises/me", response_model=EnterpriseRead, summary="Get current enterprise profile")
def get_current_enterprise(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.ENTERPRISE_INFO_EDIT))) -> Enterprise:
    enterprise = _get_enterprise_for_user(db, current_user.id)
    if enterprise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise filing was not found")
    return enterprise


@router.get("/enterprises", response_model=list[EnterpriseRead], summary="List enterprises with filters")
def list_enterprises(
    filing_status: FilingStatus | None = Query(default=None),
    region: str | None = Query(default=None),
    name: str | None = Query(default=None),
    organization_code: str | None = Query(default=None),
    report_month: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE, UserRole.CITY, UserRole.ENTERPRISE)),
) -> list[Enterprise]:
    statement = select(Enterprise)
    if report_month:
        statement = statement.join(EmploymentReport, EmploymentReport.enterprise_id == Enterprise.id).where(EmploymentReport.report_month == report_month)
    statement = _apply_enterprise_scope(statement, current_user)
    if filing_status is not None:
        statement = statement.where(Enterprise.filing_status == filing_status)
    if region:
        statement = statement.where(_region_scope_expression(Enterprise.region, region))
    if name:
        statement = statement.where(Enterprise.name.contains(name))
    if organization_code:
        statement = statement.where(Enterprise.organization_code.contains(organization_code))
    return db.scalars(statement.order_by(Enterprise.region, Enterprise.name)).unique().all()


@router.post("/enterprises/filing/submit", response_model=EnterpriseRead, summary="Submit enterprise filing")
def submit_enterprise_filing(payload: EnterpriseFilingSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.ENTERPRISE_INFO_EDIT, PermissionCode.ENTERPRISE_FILING_SUBMIT))) -> Enterprise:
    if payload.region != current_user.region:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Region must match current enterprise user")
    enterprise = _get_enterprise_for_user(db, current_user.id)
    enterprise_data = payload.model_dump()
    enterprise_data["region"] = current_user.region
    if enterprise is None:
        enterprise = Enterprise(owner_user_id=current_user.id, **enterprise_data)
        db.add(enterprise)
    else:
        for field, value in enterprise_data.items():
            setattr(enterprise, field, value)
    enterprise.filing_status = FilingStatus.PENDING
    enterprise.filing_audit_remark = None
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization code already exists") from exc
    db.refresh(enterprise)
    return enterprise


@router.post("/enterprises/{enterprise_id}/filing-audit", response_model=EnterpriseRead, summary="Province filing audit")
def audit_enterprise_filing(enterprise_id: int, payload: FilingAuditRequest, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_FILING_REVIEW))) -> Enterprise:
    enterprise = db.get(Enterprise, enterprise_id)
    if enterprise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    if enterprise.filing_status != FilingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enterprise filing is not pending")
    enterprise.filing_status = FilingStatus.APPROVED if payload.action == AuditAction.APPROVE else FilingStatus.REJECTED
    enterprise.filing_audit_remark = payload.remark
    db.commit()
    db.refresh(enterprise)
    return enterprise

@router.get("/employment-reports", response_model=list[EmploymentReportRead], summary="List employment reports")
def list_employment_reports(
    report_month: str | None = Query(default=None),
    review_status: ReviewStatus | None = Query(default=None),
    enterprise_name: str | None = Query(default=None),
    include_deleted: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE, UserRole.CITY, UserRole.ENTERPRISE)),
) -> list[EmploymentReportRead]:
    statement = select(EmploymentReport).options(selectinload(EmploymentReport.enterprise), selectinload(EmploymentReport.revisions))
    statement = _apply_report_scope(statement, current_user)
    if report_month is not None:
        statement = statement.where(EmploymentReport.report_month == report_month)
    if review_status is not None:
        statement = statement.where(EmploymentReport.review_status == review_status)
    if enterprise_name:
        statement = statement.where(Enterprise.name.contains(enterprise_name))
    if not include_deleted:
        statement = statement.where(EmploymentReport.deleted_at.is_(None))
    reports = db.scalars(statement.order_by(EmploymentReport.report_month.desc(), EmploymentReport.id.desc())).unique().all()
    return [_serialize_report(report) for report in reports]


@router.get("/employment-reports/{report_id}", response_model=EmploymentReportRead, summary="Get one employment report")
def get_employment_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.PROVINCE, UserRole.CITY, UserRole.ENTERPRISE))) -> EmploymentReportRead:
    report = _get_report_or_404(db, report_id)
    if current_user.role == UserRole.CITY and not _region_is_manageable(current_user.region, report.enterprise.region):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Report is outside your region")
    if current_user.role == UserRole.ENTERPRISE and report.enterprise.owner_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Report is outside your scope")
    return _serialize_report(report)


@router.post("/employment-reports/submit", response_model=EmploymentReportRead, summary="Submit monthly employment report")
def submit_employment_report(payload: EmploymentReportSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.ENTERPRISE_REPORT_SUBMIT))) -> EmploymentReportRead:
    enterprise = _get_enterprise_for_user(db, current_user.id)
    if enterprise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise filing was not found")
    if enterprise.filing_status != FilingStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Monthly reports require approved filing")
    _ensure_reporting_window_open(db, payload.report_month)
    report = db.scalar(select(EmploymentReport).options(selectinload(EmploymentReport.enterprise), selectinload(EmploymentReport.revisions)).where(EmploymentReport.enterprise_id == enterprise.id, EmploymentReport.report_month == payload.report_month))
    if report is not None and report.review_status in {ReviewStatus.PENDING_CITY_REVIEW, ReviewStatus.PENDING_PROVINCE_REVIEW, ReviewStatus.ARCHIVED, ReviewStatus.REPORTED_TO_MINISTRY}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Current report status does not allow resubmission")
    report_data = payload.model_dump()
    if report is None:
        report = EmploymentReport(enterprise_id=enterprise.id, **report_data)
        db.add(report)
    else:
        for field, value in report_data.items():
            setattr(report, field, value)
    report.review_status = ReviewStatus.PENDING_CITY_REVIEW
    report.return_remark = None
    report.deleted_at = None
    report.delete_remark = None
    report.deleted_by = None
    report.submitted_at = _now_utc()
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="One report per enterprise per month is allowed") from exc
    return _serialize_report(_get_report_or_404(db, report.id))


@router.post("/employment-reports/{report_id}/audit", response_model=EmploymentReportRead, summary="City audit")
def city_audit_report(report_id: int, payload: EmploymentReportAuditRequest, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.CITY_REPORT_AUDIT))) -> EmploymentReportRead:
    report = _get_report_or_404(db, report_id)
    if report.review_status != ReviewStatus.PENDING_CITY_REVIEW:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report is not pending city review")
    if not _region_is_manageable(current_user.region, report.enterprise.region):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot audit reports outside your region")
    report.review_status = ReviewStatus.PENDING_PROVINCE_REVIEW if payload.action == AuditAction.APPROVE else ReviewStatus.REJECTED
    report.return_remark = None if payload.action == AuditAction.APPROVE else payload.remark
    report.city_audited_at = _now_utc()
    db.commit()
    return _serialize_report(_get_report_or_404(db, report.id))


@router.post("/employment-reports/{report_id}/final-audit", response_model=EmploymentReportRead, summary="Province final audit")
def province_final_audit_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_REPORT_MANAGE))) -> EmploymentReportRead:
    report = _get_report_or_404(db, report_id)
    if report.review_status != ReviewStatus.PENDING_PROVINCE_REVIEW:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report is not pending province review")
    report.review_status = ReviewStatus.ARCHIVED
    report.province_audited_at = _now_utc()
    report.return_remark = None
    db.commit()
    return _serialize_report(_get_report_or_404(db, report.id))


@router.post("/employment-reports/{report_id}/province-return", response_model=EmploymentReportRead, summary="Province return for modification")
def province_return_report(report_id: int, payload: EmploymentReportAuditRequest, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_REPORT_MANAGE))) -> EmploymentReportRead:
    report = _get_report_or_404(db, report_id)
    if report.review_status != ReviewStatus.PENDING_PROVINCE_REVIEW:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report is not pending province review")
    if payload.action != AuditAction.REJECT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Province return endpoint only supports reject action")
    report.review_status = ReviewStatus.REJECTED
    report.return_remark = payload.remark
    report.province_audited_at = _now_utc()
    db.commit()
    return _serialize_report(_get_report_or_404(db, report.id))


@router.post("/employment-reports/{report_id}/report-to-ministry", response_model=EmploymentReportRead, summary="Report data to ministry")
def report_to_ministry(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.NATIONAL_EXCHANGE, PermissionCode.PROVINCE_REPORT_MANAGE))) -> EmploymentReportRead:
    report = _get_report_or_404(db, report_id)
    if report.review_status != ReviewStatus.ARCHIVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only archived reports can be submitted to ministry")
    report.review_status = ReviewStatus.REPORTED_TO_MINISTRY
    report.reported_to_ministry_at = _now_utc()
    db.commit()
    return _serialize_report(_get_report_or_404(db, report.id))


@router.post("/employment-reports/{report_id}/revisions", response_model=EmploymentReportRevisionRead, status_code=status.HTTP_201_CREATED, summary="Create data revision")
def create_report_revision(report_id: int, payload: EmploymentReportRevisionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_DATA_MODIFY))) -> EmploymentReportRevision:
    report = _get_report_or_404(db, report_id)
    for item in report.revisions:
        item.is_active = False
    revision = EmploymentReportRevision(report_id=report.id, modified_by_id=current_user.id, **payload.model_dump())
    db.add(revision)
    db.commit()
    db.refresh(revision)
    return revision


@router.get("/employment-reports/{report_id}/revisions", response_model=list[EmploymentReportRevisionRead], summary="List report revisions")
def list_report_revisions(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_DATA_MODIFY))) -> list[EmploymentReportRevision]:
    _get_report_or_404(db, report_id)
    return db.scalars(select(EmploymentReportRevision).where(EmploymentReportRevision.report_id == report_id).order_by(EmploymentReportRevision.created_at.desc(), EmploymentReportRevision.id.desc())).all()


@router.delete("/employment-reports/{report_id}", status_code=status.HTTP_200_OK, summary="Soft delete historical report")
def delete_employment_report(report_id: int, remark: str = Query(..., min_length=1, max_length=500), db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_DATA_DELETE))) -> dict[str, str]:
    report = _get_report_or_404(db, report_id)
    report.deleted_at = _now_utc()
    report.deleted_by = current_user.id
    report.delete_remark = remark
    db.commit()
    return {"message": "Report deleted successfully"}


@router.get("/province/statistics/by-city", response_model=list[ProvinceCityStatisticsRead], summary="Province employment statistics by city")
def get_city_statistics(report_month: str | None = Query(default=None), db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_MULTI_ANALYSIS))) -> list[ProvinceCityStatisticsRead]:
    reports = _load_reports_for_analysis(db, [report_month] if report_month else None)
    buckets: dict[str, dict[str, int]] = {}
    for report in reports:
        if report.review_status not in {ReviewStatus.ARCHIVED, ReviewStatus.REPORTED_TO_MINISTRY}:
            continue
        data = _build_effective_report_data(report)
        bucket = buckets.setdefault(data.region, {"enterprise_count": 0, "total_employment": 0, "total_job_changes": 0})
        bucket["enterprise_count"] += 1
        bucket["total_employment"] += data.current_employees
        bucket["total_job_changes"] += abs(data.current_employees - data.baseline_employees)
    return [ProvinceCityStatisticsRead(city=city, enterprise_count=value["enterprise_count"], total_employment=value["total_employment"], total_job_changes=value["total_job_changes"]) for city, value in sorted(buckets.items())]


@router.get("/province/statistics/summary", response_model=ProvinceAggregateSummaryRead, summary="Province summary by report month")
def get_province_summary(report_month: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_DATA_SUMMARY))) -> ProvinceAggregateSummaryRead:
    reports = [item for item in _load_reports_for_analysis(db, [report_month]) if item.review_status in {ReviewStatus.ARCHIVED, ReviewStatus.REPORTED_TO_MINISTRY}]
    total_baseline_jobs = total_current_jobs = total_job_changes = total_job_reductions = 0
    for report in reports:
        data = _build_effective_report_data(report)
        total_baseline_jobs += data.baseline_employees
        total_current_jobs += data.current_employees
        total_job_changes += abs(data.current_employees - data.baseline_employees)
        if data.current_employees < data.baseline_employees:
            total_job_reductions += data.baseline_employees - data.current_employees
    ratio = 0.0 if total_baseline_jobs == 0 else round(total_job_changes / total_baseline_jobs, 4)
    return ProvinceAggregateSummaryRead(report_month=report_month, total_enterprises=len(reports), total_baseline_jobs=total_baseline_jobs, total_current_jobs=total_current_jobs, total_job_changes=total_job_changes, total_job_reductions=total_job_reductions, total_job_change_ratio=ratio)


@router.post("/province/statistics/compare", response_model=list[ComparisonAnalysisRowRead], summary="Compare two report months")
def compare_analysis(payload: ComparisonAnalysisRequest, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_CHART_ANALYSIS))) -> list[ComparisonAnalysisRowRead]:
    reports = _load_reports_for_analysis(db, [payload.start_month, payload.end_month])
    start_map: dict[str, dict[str, int]] = {}
    end_map: dict[str, dict[str, int]] = {}
    for report in reports:
        if report.review_status not in {ReviewStatus.ARCHIVED, ReviewStatus.REPORTED_TO_MINISTRY}:
            continue
        data = _build_effective_report_data(report)
        if payload.region and not _region_is_manageable(payload.region, data.region):
            continue
        key = data.region if payload.dimension == AnalysisDimension.REGION else data.nature if payload.dimension == AnalysisDimension.ENTERPRISE_NATURE else data.industry
        target = start_map if data.report_month == payload.start_month else end_map
        target.setdefault(key, {"count": 0, "jobs": 0})
        target[key]["count"] += 1
        target[key]["jobs"] += data.current_employees
    rows: list[ComparisonAnalysisRowRead] = []
    for key in sorted(set(start_map) | set(end_map)):
        start_value = start_map.get(key, {"count": 0, "jobs": 0})
        end_value = end_map.get(key, {"count": 0, "jobs": 0})
        baseline_jobs = int(start_value["jobs"])
        current_jobs = int(end_value["jobs"])
        change_total = abs(current_jobs - baseline_jobs)
        reduction_total = max(baseline_jobs - current_jobs, 0)
        ratio = 0.0 if baseline_jobs == 0 else round(change_total / baseline_jobs, 4)
        rows.append(ComparisonAnalysisRowRead(dimension_value=key, enterprise_count=max(int(start_value["count"]), int(end_value["count"])), baseline_jobs=baseline_jobs, current_jobs=current_jobs, job_change_total=change_total, job_reduction_total=reduction_total, job_change_ratio=ratio))
    return rows


@router.get("/province/statistics/job-change-trend", response_model=list[MonthlyJobChangeTrendRead], summary="Province recent monthly job change trend")
def get_job_change_trend(months: int = Query(default=6, ge=1, le=24), region: str | None = Query(default=None), db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_CHART_ANALYSIS))) -> list[MonthlyJobChangeTrendRead]:
    reports = _load_reports_for_analysis(db)
    buckets: dict[str, dict[str, int]] = {}
    for report in reports:
        if report.review_status not in {ReviewStatus.ARCHIVED, ReviewStatus.REPORTED_TO_MINISTRY}:
            continue
        data = _build_effective_report_data(report)
        if region and not _region_is_manageable(region, data.region):
            continue
        bucket = buckets.setdefault(data.report_month, {"baseline": 0, "changes": 0})
        bucket["baseline"] += data.baseline_employees
        bucket["changes"] += abs(data.current_employees - data.baseline_employees)
    selected_months = sorted(buckets.keys())[-months:]
    return [MonthlyJobChangeTrendRead(report_month=month, total_job_changes=buckets[month]["changes"], job_change_ratio=0.0 if buckets[month]["baseline"] == 0 else round(buckets[month]["changes"] / buckets[month]["baseline"], 4)) for month in selected_months]

@router.get("/province/enterprises/export", status_code=status.HTTP_200_OK, summary="Export enterprise filings to xlsx")
def export_enterprises_xlsx(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_DATA_EXPORT))) -> StreamingResponse:
    enterprises = db.scalars(select(Enterprise).order_by(Enterprise.region, Enterprise.name)).all()
    file_content = export_enterprise_filings_to_xlsx(enterprises)
    return StreamingResponse(BytesIO(file_content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": 'attachment; filename="enterprise_filings.xlsx"'})


@router.get("/province/reports/export", status_code=status.HTTP_200_OK, summary="Export employment reports to xlsx")
def export_reports_xlsx(report_month: str | None = Query(default=None), db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.PROVINCE_DATA_EXPORT))) -> StreamingResponse:
    statement = select(EmploymentReport).options(selectinload(EmploymentReport.enterprise), selectinload(EmploymentReport.revisions)).where(EmploymentReport.deleted_at.is_(None)).order_by(EmploymentReport.report_month.desc(), EmploymentReport.id.desc())
    if report_month:
        statement = statement.where(EmploymentReport.report_month == report_month)
    reports = db.scalars(statement).all()
    file_content = export_report_list_to_xlsx([_serialize_report(item) for item in reports])
    return StreamingResponse(BytesIO(file_content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": 'attachment; filename="employment_reports.xlsx"'})


@router.get("/notifications/manage", response_model=list[NotificationRead], summary="List notifications created by current user")
def list_own_notifications(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.NOTICE_MANAGE))) -> list[Notification]:
    return db.scalars(select(Notification).where(Notification.publisher_id == current_user.id).order_by(Notification.published_at.desc(), Notification.id.desc())).all()


@router.get("/notifications/browse", response_model=list[NotificationRead], summary="Browse visible notifications")
def browse_notifications(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.NOTICE_BROWSE))) -> list[Notification]:
    return _query_visible_notifications(db, current_user)


@router.post("/notifications", response_model=NotificationRead, status_code=status.HTTP_201_CREATED, summary="Create notification")
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.NOTICE_MANAGE))) -> Notification:
    if current_user.role not in {UserRole.PROVINCE, UserRole.CITY}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only province or city users can publish notifications")
    notification = Notification(title=payload.title, content=payload.content, publisher_id=current_user.id)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.put("/notifications/{notification_id}", response_model=NotificationRead, summary="Update notification")
def update_notification(notification_id: int, payload: NotificationUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.NOTICE_MANAGE))) -> Notification:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.publisher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot edit others' notifications")
    if payload.title is not None:
        notification.title = payload.title
    if payload.content is not None:
        notification.content = payload.content
    notification.published_at = _now_utc()
    db.commit()
    db.refresh(notification)
    return notification


@router.delete("/notifications/{notification_id}", status_code=status.HTTP_200_OK, summary="Delete notification")
def delete_notification(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.NOTICE_MANAGE))) -> dict[str, str]:
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.publisher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete others' notifications")
    db.delete(notification)
    db.commit()
    return {"message": "Notification deleted successfully"}


@router.get("/integration/exchange-logs", response_model=list[DataExchangeLogRead], summary="List national exchange logs")
def list_exchange_logs(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.NATIONAL_EXCHANGE))) -> list[DataExchangeLog]:
    return db.scalars(select(DataExchangeLog).order_by(DataExchangeLog.created_at.desc(), DataExchangeLog.id.desc())).all()


@router.get("/integration/ministry/export", summary="Export month payload for national system")
def export_to_national_system(report_month: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.NATIONAL_EXCHANGE))) -> dict[str, object]:
    reports = _load_reports_for_analysis(db, [report_month])
    payload_rows = []
    updated_report_ids: list[int] = []
    for report in reports:
        if report.review_status not in {ReviewStatus.ARCHIVED, ReviewStatus.REPORTED_TO_MINISTRY}:
            continue
        data = _build_effective_report_data(report)
        payload_rows.append({
            "report_id": data.report_id,
            "enterprise_id": data.enterprise_id,
            "enterprise_name": data.enterprise_name,
            "region": data.region,
            "report_month": data.report_month,
            "baseline_employees": data.baseline_employees,
            "current_employees": data.current_employees,
            "reduction_type": getattr(data.reduction_type, "value", data.reduction_type),
            "primary_reason": getattr(data.primary_reason, "value", data.primary_reason),
            "primary_reason_detail": data.primary_reason_detail,
        })
        if report.review_status == ReviewStatus.ARCHIVED:
            report.review_status = ReviewStatus.REPORTED_TO_MINISTRY
            report.reported_to_ministry_at = _now_utc()
            updated_report_ids.append(report.id)
    payload_json = json.dumps({"report_month": report_month, "rows": payload_rows}, ensure_ascii=False)
    db.add(DataExchangeLog(report_month=report_month, direction=ExchangeDirection.EXPORT, payload=payload_json, initiated_by_id=current_user.id))
    db.commit()
    return {"report_month": report_month, "row_count": len(payload_rows), "updated_report_ids": updated_report_ids, "payload": json.loads(payload_json)}
