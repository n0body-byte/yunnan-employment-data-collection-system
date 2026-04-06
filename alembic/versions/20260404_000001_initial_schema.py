"""initial schema

Revision ID: 20260404_000001
Revises:
Create Date: 2026-04-04 22:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260404_000001"
down_revision = None
branch_labels = None
depends_on = None


user_role_enum = sa.Enum("PROVINCE", "CITY", "ENTERPRISE", name="user_role_enum", native_enum=False)
filing_status_enum = sa.Enum("PENDING", "APPROVED", "REJECTED", name="filing_status_enum", native_enum=False)
review_status_enum = sa.Enum(
    "DRAFT",
    "PENDING_CITY_REVIEW",
    "PENDING_PROVINCE_REVIEW",
    "REJECTED",
    "ARCHIVED",
    name="review_status_enum",
    native_enum=False,
)
reduction_type_enum = sa.Enum(
    "关闭破产",
    "停业整顿",
    "经济性裁员",
    "业务转移",
    "自然减员",
    "正常解除或终止劳动合同",
    "国际因素变化影响",
    "自然灾害",
    "重大事件影响",
    "其他",
    name="reduction_type_enum",
    native_enum=False,
)
reduction_reason_primary_enum = sa.Enum(
    "产业结构调整",
    "重大技术改革",
    "节能减排、淘汰落后产能",
    "订单不足",
    "原材料涨价",
    "工资、社保等用工成本上升",
    "自然减员",
    "经营资金困难",
    "税收政策变化（包括税负增加或出口退税减少等）",
    "季节性用工",
    "其他",
    "自行离职",
    "工作调动、企业内部调剂",
    "劳动关系转移、劳务派遣",
    name="primary_reduction_reason_enum",
    native_enum=False,
)
reduction_reason_secondary_enum = sa.Enum(
    "产业结构调整",
    "重大技术改革",
    "节能减排、淘汰落后产能",
    "订单不足",
    "原材料涨价",
    "工资、社保等用工成本上升",
    "自然减员",
    "经营资金困难",
    "税收政策变化（包括税负增加或出口退税减少等）",
    "季节性用工",
    "其他",
    "自行离职",
    "工作调动、企业内部调剂",
    "劳动关系转移、劳务派遣",
    name="secondary_reduction_reason_enum",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    op.create_table(
        "reporting_window_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_month", sa.String(length=7), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("report_month", name="uq_reporting_window_configs_report_month"),
        sa.CheckConstraint("start_at < end_at", name="ck_reporting_window_configs_start_before_end"),
    )
    op.create_index("ix_reporting_window_configs_report_month", "reporting_window_configs", ["report_month"], unique=False)

    op.create_table(
        "enterprises",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("organization_code", sa.String(length=9), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("nature", sa.String(length=100), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=False),
        sa.Column("main_business", sa.Text(), nullable=False),
        sa.Column("contact_person", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("postal_code", sa.String(length=6), nullable=False),
        sa.Column("fax", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("filing_status", filing_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_code", name="uq_enterprises_organization_code"),
        sa.UniqueConstraint("owner_user_id", name="uq_enterprises_owner_user_id"),
    )

    op.create_table(
        "employment_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("enterprise_id", sa.Integer(), nullable=False),
        sa.Column("baseline_employees", sa.Integer(), nullable=False),
        sa.Column("current_employees", sa.Integer(), nullable=False),
        sa.Column("reduction_type", reduction_type_enum, nullable=True),
        sa.Column("primary_reason", reduction_reason_primary_enum, nullable=True),
        sa.Column("primary_reason_detail", sa.String(length=500), nullable=True),
        sa.Column("secondary_reason", reduction_reason_secondary_enum, nullable=True),
        sa.Column("secondary_reason_detail", sa.String(length=500), nullable=True),
        sa.Column("report_month", sa.String(length=7), nullable=False),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["enterprise_id"], ["enterprises.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("enterprise_id", "report_month", name="uq_employment_reports_enterprise_month"),
        sa.CheckConstraint("baseline_employees >= 0", name="ck_employment_reports_baseline_non_negative"),
        sa.CheckConstraint("current_employees >= 0", name="ck_employment_reports_current_non_negative"),
    )
    op.create_index("ix_employment_reports_enterprise_id", "employment_reports", ["enterprise_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("publisher_id", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["publisher_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_publisher_id", "notifications", ["publisher_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_publisher_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_employment_reports_enterprise_id", table_name="employment_reports")
    op.drop_table("employment_reports")
    op.drop_table("enterprises")
    op.drop_index("ix_reporting_window_configs_report_month", table_name="reporting_window_configs")
    op.drop_table("reporting_window_configs")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    reduction_reason_secondary_enum.drop(op.get_bind(), checkfirst=False)
    reduction_reason_primary_enum.drop(op.get_bind(), checkfirst=False)
    reduction_type_enum.drop(op.get_bind(), checkfirst=False)
    review_status_enum.drop(op.get_bind(), checkfirst=False)
    filing_status_enum.drop(op.get_bind(), checkfirst=False)
    user_role_enum.drop(op.get_bind(), checkfirst=False)
