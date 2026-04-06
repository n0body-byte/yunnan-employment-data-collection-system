from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import CheckConstraint, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.enums import FilingStatus, ReductionReason, ReductionType, ReviewStatus, UserRole


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def enum_column(enum_cls: type[Enum], name: str) -> SQLEnum:
    return SQLEnum(
        enum_cls,
        name=name,
        native_enum=False,
        validate_strings=True,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(enum_column(UserRole, "user_role_enum"), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)

    enterprise: Mapped[Optional["Enterprise"]] = relationship(
        back_populates="owner_user",
        uselist=False,
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="publisher",
        cascade="all, delete-orphan",
    )


class Enterprise(TimestampMixin, Base):
    __tablename__ = "enterprises"
    __table_args__ = (
        UniqueConstraint("organization_code", name="uq_enterprises_organization_code"),
        UniqueConstraint("owner_user_id", name="uq_enterprises_owner_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_code: Mapped[str] = mapped_column(String(9), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    nature: Mapped[str] = mapped_column(String(100), nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    main_business: Mapped[str] = mapped_column(Text, nullable=False)
    contact_person: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(6), nullable=False)
    fax: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    filing_status: Mapped[FilingStatus] = mapped_column(
        enum_column(FilingStatus, "filing_status_enum"),
        default=FilingStatus.PENDING,
        server_default=FilingStatus.PENDING.value,
        nullable=False,
    )

    owner_user: Mapped[User] = relationship(back_populates="enterprise")
    employment_reports: Mapped[List["EmploymentReport"]] = relationship(
        back_populates="enterprise",
        cascade="all, delete-orphan",
    )


class EmploymentReport(TimestampMixin, Base):
    __tablename__ = "employment_reports"
    __table_args__ = (
        CheckConstraint("baseline_employees >= 0", name="ck_employment_reports_baseline_non_negative"),
        CheckConstraint("current_employees >= 0", name="ck_employment_reports_current_non_negative"),
        UniqueConstraint("enterprise_id", "report_month", name="uq_employment_reports_enterprise_month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    baseline_employees: Mapped[int] = mapped_column(Integer, nullable=False)
    current_employees: Mapped[int] = mapped_column(Integer, nullable=False)
    reduction_type: Mapped[Optional[ReductionType]] = mapped_column(
        enum_column(ReductionType, "reduction_type_enum"),
        nullable=True,
    )
    primary_reason: Mapped[Optional[ReductionReason]] = mapped_column(
        enum_column(ReductionReason, "primary_reduction_reason_enum"),
        nullable=True,
    )
    primary_reason_detail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    secondary_reason: Mapped[Optional[ReductionReason]] = mapped_column(
        enum_column(ReductionReason, "secondary_reduction_reason_enum"),
        nullable=True,
    )
    secondary_reason_detail: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    report_month: Mapped[str] = mapped_column(String(7), nullable=False)
    review_status: Mapped[ReviewStatus] = mapped_column(
        enum_column(ReviewStatus, "review_status_enum"),
        default=ReviewStatus.DRAFT,
        server_default=ReviewStatus.DRAFT.value,
        nullable=False,
    )

    enterprise: Mapped[Enterprise] = relationship(back_populates="employment_reports")


class ReportingWindowConfig(TimestampMixin, Base):
    __tablename__ = "reporting_window_configs"
    __table_args__ = (
        UniqueConstraint("report_month", name="uq_reporting_window_configs_report_month"),
        CheckConstraint("start_at < end_at", name="ck_reporting_window_configs_start_before_end"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    publisher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    publisher: Mapped[User] = relationship(back_populates="notifications")
