"""expand schema for full specification

Revision ID: 20260407_000002
Revises: 20260404_000001
Create Date: 2026-04-07 20:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260407_000002"
down_revision = "20260404_000001"
branch_labels = None
depends_on = None


permission_code_enum = sa.Enum(
    "ENTERPRISE_INFO_EDIT",
    "ENTERPRISE_FILING_SUBMIT",
    "ENTERPRISE_REPORT_SUBMIT",
    "ENTERPRISE_REPORT_QUERY",
    "PASSWORD_CHANGE",
    "CITY_REPORT_AUDIT",
    "CITY_NOTICE_MANAGE",
    "PROVINCE_FILING_REVIEW",
    "PROVINCE_ENTERPRISE_QUERY",
    "PROVINCE_REPORT_MANAGE",
    "PROVINCE_DATA_MODIFY",
    "PROVINCE_DATA_DELETE",
    "PROVINCE_DATA_SUMMARY",
    "PROVINCE_DATA_EXPORT",
    "PROVINCE_MULTI_ANALYSIS",
    "PROVINCE_CHART_ANALYSIS",
    "NOTICE_BROWSE",
    "NOTICE_MANAGE",
    "REPORTING_WINDOW_MANAGE",
    "USER_MANAGE",
    "ROLE_MANAGE",
    "SYSTEM_MONITOR",
    "NATIONAL_EXCHANGE",
    name="permission_code_enum",
    native_enum=False,
)
managed_role_scope_enum = sa.Enum("PROVINCE", "CITY", "ENTERPRISE", name="managed_role_scope_enum", native_enum=False)
exchange_direction_enum = sa.Enum("EXPORT", "IMPORT", name="exchange_direction_enum", native_enum=False)
revision_reduction_type_enum = sa.Enum(
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
    name="revision_reduction_type_enum",
    native_enum=False,
)
reduction_reason_values = [
    "产业结构调整",
    "重大技术改革",
    "节能减排、淘汰落后产能",
    "订单不足",
    "原材料涨价",
    "工资、社保等用工成本上升",
    "经营资金困难",
    "税收政策变化（包括税负增加或出口退税减少等）",
    "季节性用工",
    "其他",
    "自行离职",
    "工作调动、企业内部调剂",
    "劳动关系转移、劳务派遣",
    "退休",
    "退职",
    "死亡",
    "自然减员",
    "国际因素变化",
    "招不上人来",
]
third_reduction_reason_enum = sa.Enum(*reduction_reason_values, name="third_reduction_reason_enum", native_enum=False)
revision_primary_reduction_reason_enum = sa.Enum(*reduction_reason_values, name="revision_primary_reduction_reason_enum", native_enum=False)
revision_secondary_reduction_reason_enum = sa.Enum(*reduction_reason_values, name="revision_secondary_reduction_reason_enum", native_enum=False)
revision_third_reduction_reason_enum = sa.Enum(*reduction_reason_values, name="revision_third_reduction_reason_enum", native_enum=False)


def upgrade() -> None:
    bind = op.get_bind()
    permission_code_enum.create(bind, checkfirst=True)
    managed_role_scope_enum.create(bind, checkfirst=True)
    exchange_direction_enum.create(bind, checkfirst=True)
    revision_reduction_type_enum.create(bind, checkfirst=True)
    third_reduction_reason_enum.create(bind, checkfirst=True)
    revision_primary_reduction_reason_enum.create(bind, checkfirst=True)
    revision_secondary_reduction_reason_enum.create(bind, checkfirst=True)
    revision_third_reduction_reason_enum.create(bind, checkfirst=True)

    op.create_table(
        "permissions",
        sa.Column("code", permission_code_enum, primary_key=True),
        sa.Column("description", sa.String(length=255), nullable=False),
    )
    op.create_table(
        "managed_roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("scope_role", managed_role_scope_enum, nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("name", name="uq_managed_roles_name"),
    )
    op.create_index("ix_managed_roles_name", "managed_roles", ["name"], unique=False)
    op.create_table(
        "managed_role_permissions",
        sa.Column("managed_role_id", sa.Integer(), nullable=False),
        sa.Column("permission_code", permission_code_enum, nullable=False),
        sa.ForeignKeyConstraint(["managed_role_id"], ["managed_roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_code"], ["permissions.code"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("managed_role_id", "permission_code"),
    )
    op.create_table(
        "employment_report_revisions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("baseline_employees", sa.Integer(), nullable=False),
        sa.Column("current_employees", sa.Integer(), nullable=False),
        sa.Column("reduction_type", revision_reduction_type_enum, nullable=True),
        sa.Column("primary_reason", revision_primary_reduction_reason_enum, nullable=True),
        sa.Column("primary_reason_detail", sa.String(length=500), nullable=True),
        sa.Column("secondary_reason", revision_secondary_reduction_reason_enum, nullable=True),
        sa.Column("secondary_reason_detail", sa.String(length=500), nullable=True),
        sa.Column("third_reason", revision_third_reduction_reason_enum, nullable=True),
        sa.Column("third_reason_detail", sa.String(length=500), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=False),
        sa.Column("modified_by_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["employment_reports.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["modified_by_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_employment_report_revisions_report_id", "employment_report_revisions", ["report_id"], unique=False)
    op.create_table(
        "data_exchange_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("report_month", sa.String(length=7), nullable=False),
        sa.Column("direction", exchange_direction_enum, nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("initiated_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["initiated_by_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_data_exchange_logs_report_month", "data_exchange_logs", ["report_month"], unique=False)

    op.add_column("users", sa.Column("managed_role_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")))

    op.add_column("enterprises", sa.Column("filing_audit_remark", sa.String(length=500), nullable=True))

    op.add_column("employment_reports", sa.Column("third_reason", third_reduction_reason_enum, nullable=True))
    op.add_column("employment_reports", sa.Column("third_reason_detail", sa.String(length=500), nullable=True))
    op.add_column("employment_reports", sa.Column("return_remark", sa.String(length=500), nullable=True))
    op.add_column("employment_reports", sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("employment_reports", sa.Column("city_audited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("employment_reports", sa.Column("province_audited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("employment_reports", sa.Column("reported_to_ministry_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("employment_reports", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("employment_reports", sa.Column("deleted_by", sa.Integer(), nullable=True))
    op.add_column("employment_reports", sa.Column("delete_remark", sa.String(length=500), nullable=True))

    op.add_column("notifications", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))
    op.add_column("notifications", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))


def downgrade() -> None:
    op.drop_column("notifications", "updated_at")
    op.drop_column("notifications", "created_at")

    op.drop_column("employment_reports", "delete_remark")
    op.drop_column("employment_reports", "deleted_by")
    op.drop_column("employment_reports", "deleted_at")
    op.drop_column("employment_reports", "reported_to_ministry_at")
    op.drop_column("employment_reports", "province_audited_at")
    op.drop_column("employment_reports", "city_audited_at")
    op.drop_column("employment_reports", "submitted_at")
    op.drop_column("employment_reports", "return_remark")
    op.drop_column("employment_reports", "third_reason_detail")
    op.drop_column("employment_reports", "third_reason")

    op.drop_column("enterprises", "filing_audit_remark")
    op.drop_column("users", "is_active")
    op.drop_column("users", "managed_role_id")

    op.drop_index("ix_data_exchange_logs_report_month", table_name="data_exchange_logs")
    op.drop_table("data_exchange_logs")
    op.drop_index("ix_employment_report_revisions_report_id", table_name="employment_report_revisions")
    op.drop_table("employment_report_revisions")
    op.drop_table("managed_role_permissions")
    op.drop_index("ix_managed_roles_name", table_name="managed_roles")
    op.drop_table("managed_roles")
    op.drop_table("permissions")

    bind = op.get_bind()
    revision_third_reduction_reason_enum.drop(bind, checkfirst=True)
    revision_secondary_reduction_reason_enum.drop(bind, checkfirst=True)
    revision_primary_reduction_reason_enum.drop(bind, checkfirst=True)
    third_reduction_reason_enum.drop(bind, checkfirst=True)
    revision_reduction_type_enum.drop(bind, checkfirst=True)
    exchange_direction_enum.drop(bind, checkfirst=True)
    managed_role_scope_enum.drop(bind, checkfirst=True)
    permission_code_enum.drop(bind, checkfirst=True)
