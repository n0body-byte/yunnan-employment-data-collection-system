from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.enums import AuditAction, FilingStatus, ReviewStatus, UserRole
from app.models import Enterprise, EmploymentReport, ReportingWindowConfig, User
from app.schemas import (
    EmploymentReportAuditRequest,
    EmploymentReportRead,
    EmploymentReportSubmit,
    EnterpriseFilingSubmit,
    EnterpriseRead,
    FilingAuditRequest,
    LoginRequest,
    LoginResponse,
    MonthlyJobChangeTrendRead,
    ProvinceCityStatisticsRead,
    ReportingWindowConfigRead,
    ReportingWindowConfigUpsert,
    SystemMonitorRead,
)
from app.security import create_access_token, verify_password
from app.services.exporters import export_enterprise_filings_to_xlsx

router = APIRouter(prefix="/api", tags=["core-business"])


def require_role(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


def _region_is_manageable(manager_region: str, target_region: str) -> bool:
    manager_region = manager_region.strip()
    target_region = target_region.strip()
    return target_region == manager_region or target_region.startswith(manager_region)


def _region_scope_expression(region_column, region: str):
    return or_(region_column == region, region_column.startswith(region))


def _get_enterprise_for_user(db: Session, user_id: int) -> Enterprise | None:
    return db.scalar(select(Enterprise).where(Enterprise.owner_user_id == user_id))


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


def _get_reporting_window(db: Session, report_month: str) -> ReportingWindowConfig | None:
    return db.scalar(select(ReportingWindowConfig).where(ReportingWindowConfig.report_month == report_month))


def _ensure_reporting_window_open(db: Session, report_month: str) -> None:
    config = _get_reporting_window(db, report_month)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reporting window is not configured for this month",
        )

    now = datetime.now(timezone.utc)
    start_at = config.start_at if config.start_at.tzinfo else config.start_at.replace(tzinfo=timezone.utc)
    end_at = config.end_at if config.end_at.tzinfo else config.end_at.replace(tzinfo=timezone.utc)
    if now < start_at or now > end_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current time is outside the configured reporting window",
        )


@router.post(
    "/auth/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and issue JWT token",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or user.role != payload.role or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username, password, or role")

    access_token = create_access_token(subject=str(user.id), role=user.role.value, region=user.region)
    return LoginResponse(access_token=access_token, role=user.role, region=user.region)


@router.post(
    "/system/reporting-windows",
    response_model=ReportingWindowConfigRead,
    status_code=status.HTTP_200_OK,
    summary="Create or update reporting window",
)
def upsert_reporting_window(
    payload: ReportingWindowConfigUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE)),
) -> ReportingWindowConfig:
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


@router.get(
    "/system/reporting-windows",
    response_model=list[ReportingWindowConfigRead],
    status_code=status.HTTP_200_OK,
    summary="List reporting windows",
)
def list_reporting_windows(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE)),
) -> list[ReportingWindowConfig]:
    return db.scalars(select(ReportingWindowConfig).order_by(ReportingWindowConfig.report_month.desc())).all()


@router.get(
    "/system/monitor",
    response_model=SystemMonitorRead,
    status_code=status.HTTP_200_OK,
    summary="System resource monitor",
)
def get_system_monitor(
    current_user: User = Depends(require_role(UserRole.PROVINCE)),
) -> SystemMonitorRead:
    try:
        import psutil
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="psutil is required") from exc

    memory = psutil.virtual_memory()
    return SystemMonitorRead(
        cpu_percent=float(psutil.cpu_percent(interval=0.5)),
        memory_percent=float(memory.percent),
        memory_used_bytes=int(memory.used),
        memory_total_bytes=int(memory.total),
    )


@router.get(
    "/enterprises",
    response_model=list[EnterpriseRead],
    status_code=status.HTTP_200_OK,
    summary="List enterprises with RBAC scope",
)
def list_enterprises(
    filing_status: FilingStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE, UserRole.CITY, UserRole.ENTERPRISE)),
) -> list[Enterprise]:
    statement = select(Enterprise)
    statement = _apply_enterprise_scope(statement, current_user)
    if filing_status is not None:
        statement = statement.where(Enterprise.filing_status == filing_status)
    statement = statement.order_by(Enterprise.region, Enterprise.name)
    return db.scalars(statement).all()


@router.post(
    "/enterprises/{enterprise_id}/filing-audit",
    response_model=EnterpriseRead,
    status_code=status.HTTP_200_OK,
    summary="Province filing audit",
)
def audit_enterprise_filing(
    enterprise_id: int,
    payload: FilingAuditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE)),
) -> Enterprise:
    enterprise = db.get(Enterprise, enterprise_id)
    if enterprise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise not found")
    if enterprise.filing_status != FilingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enterprise filing is not pending")

    enterprise.filing_status = FilingStatus.APPROVED if payload.action == AuditAction.APPROVE else FilingStatus.REJECTED
    db.commit()
    db.refresh(enterprise)
    return enterprise


@router.post(
    "/enterprises/filing/submit",
    response_model=EnterpriseRead,
    status_code=status.HTTP_200_OK,
    summary="Submit enterprise filing",
)
def submit_enterprise_filing(
    payload: EnterpriseFilingSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ENTERPRISE)),
) -> Enterprise:
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

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization code already exists") from exc

    db.refresh(enterprise)
    return enterprise


@router.get(
    "/employment-reports",
    response_model=list[EmploymentReportRead],
    status_code=status.HTTP_200_OK,
    summary="List employment reports with RBAC scope",
)
def list_employment_reports(
    report_month: str | None = Query(default=None),
    review_status: ReviewStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE, UserRole.CITY, UserRole.ENTERPRISE)),
) -> list[EmploymentReport]:
    statement = select(EmploymentReport)
    statement = _apply_report_scope(statement, current_user)
    if report_month is not None:
        statement = statement.where(EmploymentReport.report_month == report_month)
    if review_status is not None:
        statement = statement.where(EmploymentReport.review_status == review_status)
    statement = statement.order_by(EmploymentReport.report_month.desc(), EmploymentReport.id.desc())
    return db.scalars(statement).all()


@router.post(
    "/employment-reports/submit",
    response_model=EmploymentReportRead,
    status_code=status.HTTP_200_OK,
    summary="Submit monthly employment report",
)
def submit_employment_report(
    payload: EmploymentReportSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ENTERPRISE)),
) -> EmploymentReport:
    enterprise = _get_enterprise_for_user(db, current_user.id)
    if enterprise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enterprise filing was not found")
    if enterprise.filing_status != FilingStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Monthly reports require approved filing")

    _ensure_reporting_window_open(db, payload.report_month)

    report = db.scalar(
        select(EmploymentReport).where(
            EmploymentReport.enterprise_id == enterprise.id,
            EmploymentReport.report_month == payload.report_month,
        )
    )

    if report is not None and report.review_status in {
        ReviewStatus.PENDING_CITY_REVIEW,
        ReviewStatus.PENDING_PROVINCE_REVIEW,
        ReviewStatus.ARCHIVED,
    }:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Current report status does not allow resubmission")

    report_data = payload.model_dump()
    if report is None:
        report = EmploymentReport(enterprise_id=enterprise.id, **report_data)
        db.add(report)
    else:
        for field, value in report_data.items():
            setattr(report, field, value)

    report.review_status = ReviewStatus.PENDING_CITY_REVIEW

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="One report per enterprise per month is allowed") from exc

    db.refresh(report)
    return report


@router.post(
    "/employment-reports/{report_id}/audit",
    response_model=EmploymentReportRead,
    status_code=status.HTTP_200_OK,
    summary="City audit",
)
def city_audit_report(
    report_id: int,
    payload: EmploymentReportAuditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CITY)),
) -> EmploymentReport:
    report = db.get(EmploymentReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.review_status != ReviewStatus.PENDING_CITY_REVIEW:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report is not pending city review")
    if not _region_is_manageable(current_user.region, report.enterprise.region):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot audit reports outside your region")

    report.review_status = (
        ReviewStatus.PENDING_PROVINCE_REVIEW
        if payload.action == AuditAction.APPROVE
        else ReviewStatus.REJECTED
    )
    db.commit()
    db.refresh(report)
    return report


@router.post(
    "/employment-reports/{report_id}/final-audit",
    response_model=EmploymentReportRead,
    status_code=status.HTTP_200_OK,
    summary="Province final audit",
)
def province_final_audit_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE)),
) -> EmploymentReport:
    report = db.get(EmploymentReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.review_status != ReviewStatus.PENDING_PROVINCE_REVIEW:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report is not pending province review")

    report.review_status = ReviewStatus.ARCHIVED
    db.commit()
    db.refresh(report)
    return report


@router.get(
    "/province/statistics/by-city",
    response_model=list[ProvinceCityStatisticsRead],
    status_code=status.HTTP_200_OK,
    summary="Province employment statistics by city",
)
def get_city_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE)),
) -> list[ProvinceCityStatisticsRead]:
    archived_current_employees = case(
        (EmploymentReport.review_status == ReviewStatus.ARCHIVED, EmploymentReport.current_employees),
        else_=0,
    )
    archived_job_changes = case(
        (
            EmploymentReport.review_status == ReviewStatus.ARCHIVED,
            func.abs(EmploymentReport.current_employees - EmploymentReport.baseline_employees),
        ),
        else_=0,
    )

    rows = db.execute(
        select(
            Enterprise.region.label("city"),
            func.count(func.distinct(Enterprise.id)).label("enterprise_count"),
            func.coalesce(func.sum(archived_current_employees), 0).label("total_employment"),
            func.coalesce(func.sum(archived_job_changes), 0).label("total_job_changes"),
        )
        .select_from(Enterprise)
        .outerjoin(EmploymentReport, EmploymentReport.enterprise_id == Enterprise.id)
        .group_by(Enterprise.region)
        .order_by(Enterprise.region)
    ).all()

    return [
        ProvinceCityStatisticsRead(
            city=row.city,
            enterprise_count=int(row.enterprise_count or 0),
            total_employment=int(row.total_employment or 0),
            total_job_changes=int(row.total_job_changes or 0),
        )
        for row in rows
    ]


@router.get(
    "/province/statistics/job-change-trend",
    response_model=list[MonthlyJobChangeTrendRead],
    status_code=status.HTTP_200_OK,
    summary="Province recent monthly job change trend",
)
def get_job_change_trend(
    months: int = Query(default=6, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE)),
) -> list[MonthlyJobChangeTrendRead]:
    rows = db.execute(
        select(
            EmploymentReport.report_month.label("report_month"),
            func.coalesce(
                func.sum(func.abs(EmploymentReport.current_employees - EmploymentReport.baseline_employees)),
                0,
            ).label("total_job_changes"),
        )
        .where(EmploymentReport.review_status == ReviewStatus.ARCHIVED)
        .group_by(EmploymentReport.report_month)
        .order_by(EmploymentReport.report_month.desc())
        .limit(months)
    ).all()

    return [
        MonthlyJobChangeTrendRead(
            report_month=row.report_month,
            total_job_changes=int(row.total_job_changes or 0),
        )
        for row in reversed(rows)
    ]


@router.get(
    "/province/enterprises/export",
    status_code=status.HTTP_200_OK,
    summary="Export enterprise filings to xlsx",
)
def export_enterprises_xlsx(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVINCE)),
) -> StreamingResponse:
    enterprises = db.scalars(select(Enterprise).order_by(Enterprise.region, Enterprise.name)).all()

    try:
        file_content = export_enterprise_filings_to_xlsx(enterprises)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    filename = "enterprise_filings.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        BytesIO(file_content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
