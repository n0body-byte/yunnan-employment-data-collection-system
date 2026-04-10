from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.enums import ExchangeDirection, FilingStatus, ReductionReason, ReductionType, ReviewStatus, UserRole
from app.models import (
    Base,
    DataExchangeLog,
    Enterprise,
    EmploymentReport,
    EmploymentReportRevision,
    ManagedRole,
    Notification,
    ReportingWindowConfig,
    User,
)
from app.routes import _ensure_acl_seeded
from app.security import hash_password


RNG = random.Random(20260410)
NOW = datetime.now(UTC)


@dataclass(frozen=True)
class CitySeed:
    region: str
    username: str
    password: str


@dataclass(frozen=True)
class EnterpriseTemplate:
    suffix: str
    nature: str
    industry: str
    main_business: str
    contact_person: str
    address_suffix: str
    baseline_range: tuple[int, int]


CITIES: list[CitySeed] = [
    CitySeed("昆明市", "kunming_city", "City12345"),
    CitySeed("曲靖市", "qujing_city", "City12345"),
    CitySeed("玉溪市", "yuxi_city", "City12345"),
    CitySeed("大理州", "dali_city", "City12345"),
    CitySeed("楚雄州", "chuxiong_city", "City12345"),
    CitySeed("红河州", "honghe_city", "City12345"),
]

ENTERPRISE_TEMPLATES: list[EnterpriseTemplate] = [
    EnterpriseTemplate(
        suffix="云岭装备制造有限公司",
        nature="民营企业",
        industry="制造业/装备制造",
        main_business="智能矿山装备、自动化产线和专用机加工设备生产",
        contact_person="李晓峰",
        address_suffix="高新区科创路88号",
        baseline_range=(220, 420),
    ),
    EnterpriseTemplate(
        suffix="高原生物医药有限公司",
        nature="股份制企业",
        industry="制造业/医药制造",
        main_business="中成药、植物提取物和功能性健康产品研发生产",
        contact_person="张敏",
        address_suffix="生物医药产业园6号",
        baseline_range=(180, 360),
    ),
    EnterpriseTemplate(
        suffix="滇中现代服务有限公司",
        nature="民营企业",
        industry="居民服务业/居民服务",
        main_business="人力资源外包、物业服务和园区综合后勤保障",
        contact_person="杨倩",
        address_suffix="商务核心区A座12层",
        baseline_range=(90, 180),
    ),
    EnterpriseTemplate(
        suffix="滇云食品加工有限公司",
        nature="民营企业",
        industry="制造业/食品加工",
        main_business="农特产品深加工、冷链包装和品牌食品供应",
        contact_person="王海",
        address_suffix="绿色食品产业园18号",
        baseline_range=(130, 240),
    ),
    EnterpriseTemplate(
        suffix="苍洱文旅服务有限公司",
        nature="其他企业",
        industry="住宿和餐饮业/住宿业",
        main_business="景区住宿运营、会议接待和文旅配套服务",
        contact_person="赵雪",
        address_suffix="文旅产业园3号楼",
        baseline_range=(80, 160),
    ),
    EnterpriseTemplate(
        suffix="滇南物流发展有限公司",
        nature="国有企业",
        industry="批发和零售业/批发业",
        main_business="区域仓配、商贸流通和供应链配送服务",
        contact_person="陈波",
        address_suffix="综合保税物流园22号",
        baseline_range=(150, 300),
    ),
]

PROVINCE_NOTICES = [
    ("关于做好月度就业失业数据填报工作的通知", "请各地严格按照上报时限组织企业完成月报填报，确保数据真实、完整、及时。"),
    ("关于进一步加强备案信息审核的提示", "省级审核时将重点核查组织机构代码、行业类别、联系人信息和企业地址的一致性。"),
    ("关于开展重点行业岗位变动监测的通知", "请重点关注制造业、文旅服务业和物流行业企业的岗位变化情况，及时掌握减员趋势。"),
    ("关于系统维护窗口的说明", "系统已完成基础性能优化，建议各级用户使用统一工作台办理备案审核、月报审核和系统维护业务。"),
]

CITY_NOTICE_TEMPLATE = "请本地区企业于规定时限内完成{report_month}月就业失业数据上报，若出现岗位减少，请准确填写减少类型和主要原因。"


def month_strings(count: int) -> list[str]:
    result: list[str] = []
    year = NOW.year
    month = NOW.month
    for offset in range(count - 1, -1, -1):
        target_month = month - offset
        target_year = year
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        result.append(f"{target_year:04d}-{target_month:02d}")
    return result


def month_start(report_month: str) -> datetime:
    year = int(report_month[:4])
    month = int(report_month[5:7])
    return datetime(year, month, 1, 8, 30, tzinfo=UTC)


def make_org_code(index: int) -> str:
    return f"YN{index:07d}"


def make_phone(index: int) -> str:
    return f"138{index:08d}"[:11]


def enterprise_username(city: CitySeed, template_index: int) -> str:
    region_prefix = city.username.replace("_city", "")
    return f"{region_prefix}_enterprise_{template_index + 1}"


def choose_reduction_reason() -> ReductionReason:
    weighted = [
        ReductionReason.INSUFFICIENT_ORDERS,
        ReductionReason.RAW_MATERIAL_PRICE_RISE,
        ReductionReason.LABOR_COST_RISE,
        ReductionReason.FUNDING_DIFFICULTY,
        ReductionReason.SEASONAL_EMPLOYMENT,
        ReductionReason.INDUSTRIAL_RESTRUCTURING,
        ReductionReason.RECRUITMENT_DIFFICULTY,
    ]
    return RNG.choice(weighted)


def choose_reduction_type(reason: ReductionReason) -> ReductionType:
    mapping = {
        ReductionReason.INDUSTRIAL_RESTRUCTURING: ReductionType.BUSINESS_TRANSFER,
        ReductionReason.INSUFFICIENT_ORDERS: ReductionType.ECONOMIC_LAYOFF,
        ReductionReason.RAW_MATERIAL_PRICE_RISE: ReductionType.ECONOMIC_LAYOFF,
        ReductionReason.LABOR_COST_RISE: ReductionType.ECONOMIC_LAYOFF,
        ReductionReason.FUNDING_DIFFICULTY: ReductionType.SUSPENSION_REORGANIZATION,
        ReductionReason.SEASONAL_EMPLOYMENT: ReductionType.NATURAL_ATTRITION,
        ReductionReason.RECRUITMENT_DIFFICULTY: ReductionType.NATURAL_ATTRITION,
    }
    return mapping.get(reason, ReductionType.OTHER)


def upsert_user(
    db: Session,
    *,
    username: str,
    password: str,
    role: UserRole,
    region: str,
    managed_role_name: str,
) -> User:
    user = db.scalar(select(User).where(User.username == username))
    managed_role = db.scalar(select(ManagedRole).where(ManagedRole.name == managed_role_name))
    if user is None:
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            region=region,
            managed_role_id=managed_role.id if managed_role else None,
            is_active=True,
        )
        db.add(user)
        db.flush()
        return user

    user.password_hash = hash_password(password)
    user.role = role
    user.region = region
    user.managed_role_id = managed_role.id if managed_role else None
    user.is_active = True
    db.flush()
    return user


def upsert_enterprise(
    db: Session,
    *,
    owner_user: User,
    organization_code: str,
    name: str,
    nature: str,
    industry: str,
    main_business: str,
    contact_person: str,
    phone: str,
    region: str,
    address: str,
    postal_code: str,
    email: str,
    filing_status: FilingStatus,
) -> Enterprise:
    enterprise = db.scalar(select(Enterprise).where(Enterprise.owner_user_id == owner_user.id))
    if enterprise is None:
        enterprise = Enterprise(
            owner_user_id=owner_user.id,
            organization_code=organization_code,
            name=name,
            nature=nature,
            industry=industry,
            main_business=main_business,
            contact_person=contact_person,
            phone=phone,
            region=region,
            address=address,
            postal_code=postal_code,
            fax=None,
            email=email,
            filing_status=filing_status,
        )
        db.add(enterprise)
        db.flush()
        return enterprise

    enterprise.organization_code = organization_code
    enterprise.name = name
    enterprise.nature = nature
    enterprise.industry = industry
    enterprise.main_business = main_business
    enterprise.contact_person = contact_person
    enterprise.phone = phone
    enterprise.region = region
    enterprise.address = address
    enterprise.postal_code = postal_code
    enterprise.email = email
    enterprise.filing_status = filing_status
    enterprise.filing_audit_remark = None
    db.flush()
    return enterprise


def upsert_reporting_window(db: Session, report_month: str, order_index: int) -> None:
    start_at = month_start(report_month) + timedelta(hours=0)
    end_at = start_at + timedelta(days=19 if order_index == len(MONTHS) - 1 else 14, hours=9, minutes=30)
    config = db.scalar(select(ReportingWindowConfig).where(ReportingWindowConfig.report_month == report_month))
    if config is None:
        db.add(ReportingWindowConfig(report_month=report_month, start_at=start_at, end_at=end_at))
        return
    config.start_at = start_at
    config.end_at = end_at


def upsert_notification(db: Session, title: str, content: str, publisher_id: int, published_at: datetime) -> None:
    existing = db.scalar(select(Notification).where(Notification.title == title))
    if existing is None:
        db.add(Notification(title=title, content=content, publisher_id=publisher_id, published_at=published_at))
        return
    existing.content = content
    existing.publisher_id = publisher_id
    existing.published_at = published_at


def upsert_exchange_log(db: Session, report_month: str, initiated_by_id: int, rows: list[dict[str, object]]) -> None:
    payload = json.dumps({"report_month": report_month, "rows": rows}, ensure_ascii=False)
    existing = db.scalar(
        select(DataExchangeLog).where(
            DataExchangeLog.report_month == report_month,
            DataExchangeLog.direction == ExchangeDirection.EXPORT,
        )
    )
    if existing is None:
        db.add(
            DataExchangeLog(
                report_month=report_month,
                direction=ExchangeDirection.EXPORT,
                payload=payload,
                initiated_by_id=initiated_by_id,
            )
        )
        return
    existing.payload = payload
    existing.initiated_by_id = initiated_by_id


def report_status_for(month_index: int, enterprise_index: int) -> ReviewStatus:
    if month_index <= 1:
        return ReviewStatus.REPORTED_TO_MINISTRY
    if month_index == 2:
        return ReviewStatus.ARCHIVED
    if month_index == 3:
        return ReviewStatus.ARCHIVED if enterprise_index % 5 else ReviewStatus.REJECTED
    if month_index == 4:
        return ReviewStatus.PENDING_PROVINCE_REVIEW if enterprise_index % 3 else ReviewStatus.REJECTED
    return ReviewStatus.PENDING_CITY_REVIEW if enterprise_index % 4 else ReviewStatus.PENDING_PROVINCE_REVIEW


def build_report_values(baseline_hint: int, month_index: int, enterprise_index: int) -> tuple[int, int, ReductionType | None, ReductionReason | None, str | None]:
    baseline = max(35, baseline_hint + RNG.randint(-18, 22))
    trend_delta = RNG.randint(-28, 34)
    if month_index >= 4 and enterprise_index % 4 == 0:
        trend_delta = RNG.randint(-42, -8)
    if month_index == 5 and enterprise_index % 3 == 0:
        trend_delta = RNG.randint(-65, -18)
    current = max(0, baseline + trend_delta)

    if current >= baseline:
        return baseline, current, None, None, None

    reason = choose_reduction_reason()
    reduction_type = choose_reduction_type(reason)
    detail = f"受{reason.value}影响，企业在当月对部分岗位进行了阶段性优化调整。"
    return baseline, current, reduction_type, reason, detail


def upsert_report(
    db: Session,
    *,
    enterprise: Enterprise,
    report_month: str,
    month_index: int,
    enterprise_index: int,
    baseline_hint: int,
) -> EmploymentReport:
    report = db.scalar(
        select(EmploymentReport).where(
            EmploymentReport.enterprise_id == enterprise.id,
            EmploymentReport.report_month == report_month,
        )
    )
    baseline, current, reduction_type, primary_reason, detail = build_report_values(baseline_hint, month_index, enterprise_index)
    secondary_reason = ReductionReason.LABOR_COST_RISE if primary_reason and primary_reason != ReductionReason.LABOR_COST_RISE and current < baseline - 12 else None
    third_reason = ReductionReason.RECRUITMENT_DIFFICULTY if primary_reason and current < baseline - 18 else None
    status = report_status_for(month_index, enterprise_index)

    submitted_at = month_start(report_month) + timedelta(days=RNG.randint(2, 8), hours=RNG.randint(1, 7))
    city_audited_at = submitted_at + timedelta(days=RNG.randint(1, 3)) if status != ReviewStatus.PENDING_CITY_REVIEW else None
    province_audited_at = city_audited_at + timedelta(days=RNG.randint(1, 4)) if status in {ReviewStatus.ARCHIVED, ReviewStatus.REPORTED_TO_MINISTRY} else None
    reported_to_ministry_at = province_audited_at + timedelta(days=RNG.randint(1, 2)) if status == ReviewStatus.REPORTED_TO_MINISTRY and province_audited_at else None
    return_remark = "主要原因填写不完整，请补充岗位减少说明后重新提交。" if status == ReviewStatus.REJECTED else None

    if report is None:
        report = EmploymentReport(
            enterprise_id=enterprise.id,
            report_month=report_month,
            baseline_employees=baseline,
            current_employees=current,
            reduction_type=reduction_type,
            primary_reason=primary_reason,
            primary_reason_detail=detail,
            secondary_reason=secondary_reason,
            secondary_reason_detail="叠加人工成本上涨因素。" if secondary_reason else None,
            third_reason=third_reason,
            third_reason_detail="部分岗位补员周期延长。" if third_reason else None,
            review_status=status,
            return_remark=return_remark,
            submitted_at=submitted_at,
            city_audited_at=city_audited_at,
            province_audited_at=province_audited_at,
            reported_to_ministry_at=reported_to_ministry_at,
        )
        db.add(report)
        db.flush()
        return report

    report.baseline_employees = baseline
    report.current_employees = current
    report.reduction_type = reduction_type
    report.primary_reason = primary_reason
    report.primary_reason_detail = detail
    report.secondary_reason = secondary_reason
    report.secondary_reason_detail = "叠加人工成本上涨因素。" if secondary_reason else None
    report.third_reason = third_reason
    report.third_reason_detail = "部分岗位补员周期延长。" if third_reason else None
    report.review_status = status
    report.return_remark = return_remark
    report.submitted_at = submitted_at
    report.city_audited_at = city_audited_at
    report.province_audited_at = province_audited_at
    report.reported_to_ministry_at = reported_to_ministry_at
    report.deleted_at = None
    report.deleted_by = None
    report.delete_remark = None
    db.flush()
    return report


def upsert_revision_if_needed(db: Session, report: EmploymentReport, modifier_id: int, note: str) -> None:
    if report.review_status not in {ReviewStatus.ARCHIVED, ReviewStatus.REPORTED_TO_MINISTRY}:
        return
    existing = db.scalar(
        select(EmploymentReportRevision).where(
            EmploymentReportRevision.report_id == report.id,
            EmploymentReportRevision.note == note,
        )
    )
    if existing is not None:
        return
    db.add(
        EmploymentReportRevision(
            report_id=report.id,
            baseline_employees=report.baseline_employees,
            current_employees=report.current_employees,
            reduction_type=report.reduction_type,
            primary_reason=report.primary_reason,
            primary_reason_detail=report.primary_reason_detail,
            secondary_reason=report.secondary_reason,
            secondary_reason_detail=report.secondary_reason_detail,
            third_reason=report.third_reason,
            third_reason_detail=report.third_reason_detail,
            note=note,
            modified_by_id=modifier_id,
            is_active=True,
        )
    )


MONTHS = month_strings(6)


def seed_demo_data() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _ensure_acl_seeded(db)

        province_user = upsert_user(
            db,
            username="province_admin",
            password="Admin12345",
            role=UserRole.PROVINCE,
            region="云南省",
            managed_role_name="Province Administrator",
        )

        city_users: dict[str, User] = {}
        for city in CITIES:
            city_users[city.region] = upsert_user(
                db,
                username=city.username,
                password=city.password,
                role=UserRole.CITY,
                region=city.region,
                managed_role_name="City Auditor",
            )

        all_enterprises: list[Enterprise] = []
        enterprise_index = 1
        for city_index, city in enumerate(CITIES):
            for template_index in range(3):
                template = ENTERPRISE_TEMPLATES[(city_index * 2 + template_index) % len(ENTERPRISE_TEMPLATES)]
                username = "demo_enterprise" if city_index == 0 and template_index == 0 else enterprise_username(city, template_index)
                owner = upsert_user(
                    db,
                    username=username,
                    password="Enterprise12345",
                    role=UserRole.ENTERPRISE,
                    region=city.region,
                    managed_role_name="Enterprise Operator",
                )
                company_name = f"{city.region[:2]}{template.suffix}"
                enterprise = upsert_enterprise(
                    db,
                    owner_user=owner,
                    organization_code=make_org_code(enterprise_index),
                    name=company_name,
                    nature=template.nature,
                    industry=template.industry,
                    main_business=template.main_business,
                    contact_person=template.contact_person,
                    phone=make_phone(enterprise_index),
                    region=city.region,
                    address=f"{city.region}{template.address_suffix}",
                    postal_code="650000",
                    email=f"{username}@example.com",
                    filing_status=FilingStatus.APPROVED,
                )
                all_enterprises.append(enterprise)
                enterprise_index += 1

        for month_index, report_month in enumerate(MONTHS):
            upsert_reporting_window(db, report_month, month_index)

        province_role = db.scalar(select(ManagedRole).where(ManagedRole.name == "Province Administrator"))
        if province_role is not None:
            province_user.managed_role_id = province_role.id

        db.flush()

        exchange_rows_by_month: dict[str, list[dict[str, object]]] = {month: [] for month in MONTHS}
        for enterprise_idx, enterprise in enumerate(all_enterprises, start=1):
            baseline_hint = RNG.randint(*ENTERPRISE_TEMPLATES[(enterprise_idx - 1) % len(ENTERPRISE_TEMPLATES)].baseline_range)
            for month_index, report_month in enumerate(MONTHS):
                report = upsert_report(
                    db,
                    enterprise=enterprise,
                    report_month=report_month,
                    month_index=month_index,
                    enterprise_index=enterprise_idx,
                    baseline_hint=baseline_hint,
                )
                if enterprise_idx % 6 == 0 and month_index in {2, 3}:
                    upsert_revision_if_needed(db, report, province_user.id, "省级核查后修正了基期与调查期人数。")
                if report.review_status in {ReviewStatus.ARCHIVED, ReviewStatus.REPORTED_TO_MINISTRY} and month_index <= 2:
                    exchange_rows_by_month[report_month].append(
                        {
                            "report_id": report.id,
                            "enterprise_id": enterprise.id,
                            "enterprise_name": enterprise.name,
                            "region": enterprise.region,
                            "report_month": report.report_month,
                            "baseline_employees": report.baseline_employees,
                            "current_employees": report.current_employees,
                            "reduction_type": report.reduction_type.value if report.reduction_type else None,
                            "primary_reason": report.primary_reason.value if report.primary_reason else None,
                        }
                    )

        for offset, (title, content) in enumerate(PROVINCE_NOTICES):
            upsert_notification(
                db,
                title=title,
                content=content,
                publisher_id=province_user.id,
                published_at=NOW - timedelta(days=offset * 7 + 2),
            )

        latest_month = MONTHS[-1]
        for offset, city in enumerate(CITIES):
            city_user = city_users[city.region]
            upsert_notification(
                db,
                title=f"{city.region}{latest_month}月报填报提醒",
                content=CITY_NOTICE_TEMPLATE.format(report_month=latest_month),
                publisher_id=city_user.id,
                published_at=NOW - timedelta(days=offset + 1),
            )

        for report_month in MONTHS[:3]:
            if exchange_rows_by_month[report_month]:
                upsert_exchange_log(db, report_month, province_user.id, exchange_rows_by_month[report_month])

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
    print("Realistic demo data seeded successfully.")
