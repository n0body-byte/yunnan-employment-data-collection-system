from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums import AuditAction, FilingStatus, ReductionReason, ReductionType, ReviewStatus, UserRole

ORGANIZATION_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{9}$")
PHONE_PATTERN = re.compile(r"^(?:1[3-9]\d{9}|\(?0\d{2,3}\)?-?\d{7,8})$")
FAX_PATTERN = re.compile(r"^(?:\(?0\d{2,3}\)?-?\d{7,8})$")
POSTAL_CODE_PATTERN = re.compile(r"^\d{6}$")
REPORT_MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ORMBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    region: str


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: UserRole
    region: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    role: Optional[UserRole] = None
    region: Optional[str] = Field(None, min_length=2, max_length=100)


class UserRead(ORMBaseSchema):
    id: int
    username: str
    role: UserRole
    region: str
    created_at: datetime
    updated_at: datetime


class EnterpriseBase(BaseModel):
    organization_code: str = Field(..., description="9-character alphanumeric organization code")
    name: str = Field(..., min_length=2, max_length=200)
    nature: str = Field(..., min_length=2, max_length=100)
    industry: str = Field(..., min_length=2, max_length=100)
    main_business: str = Field(..., min_length=2, max_length=2000)
    contact_person: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., max_length=20)
    region: str = Field(..., min_length=2, max_length=100)
    address: str = Field(..., min_length=2, max_length=255)
    postal_code: str = Field(..., max_length=6)
    fax: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    filing_status: FilingStatus = FilingStatus.PENDING

    @field_validator("organization_code")
    @classmethod
    def validate_organization_code(cls, value: str) -> str:
        if not ORGANIZATION_CODE_PATTERN.fullmatch(value):
            raise ValueError("organization_code must be exactly 9 alphanumeric characters")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not PHONE_PATTERN.fullmatch(value):
            raise ValueError("phone must be a mobile number or landline with area code")
        return value

    @field_validator("fax")
    @classmethod
    def validate_fax(cls, value: Optional[str]) -> Optional[str]:
        if value and not FAX_PATTERN.fullmatch(value):
            raise ValueError("fax must be a landline number with area code")
        return value

    @field_validator("postal_code")
    @classmethod
    def validate_postal_code(cls, value: str) -> str:
        if not POSTAL_CODE_PATTERN.fullmatch(value):
            raise ValueError("postal_code must be exactly 6 digits")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value and not EMAIL_PATTERN.fullmatch(value):
            raise ValueError("email must be a valid email address")
        return value


class EnterpriseCreate(EnterpriseBase):
    owner_user_id: int


class EnterpriseFilingSubmit(EnterpriseBase):
    pass


class FilingAuditRequest(BaseModel):
    action: AuditAction


class EnterpriseUpdate(BaseModel):
    organization_code: Optional[str] = None
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    nature: Optional[str] = Field(None, min_length=2, max_length=100)
    industry: Optional[str] = Field(None, min_length=2, max_length=100)
    main_business: Optional[str] = Field(None, min_length=2, max_length=2000)
    contact_person: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    region: Optional[str] = Field(None, min_length=2, max_length=100)
    address: Optional[str] = Field(None, min_length=2, max_length=255)
    postal_code: Optional[str] = None
    fax: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = None
    filing_status: Optional[FilingStatus] = None

    _validate_organization_code = field_validator("organization_code")(EnterpriseBase.validate_organization_code)
    _validate_phone = field_validator("phone")(EnterpriseBase.validate_phone)
    _validate_fax = field_validator("fax")(EnterpriseBase.validate_fax)
    _validate_postal_code = field_validator("postal_code")(EnterpriseBase.validate_postal_code)
    _validate_email = field_validator("email")(EnterpriseBase.validate_email)


class EnterpriseRead(ORMBaseSchema):
    id: int
    owner_user_id: int
    organization_code: str
    name: str
    nature: str
    industry: str
    main_business: str
    contact_person: str
    phone: str
    region: str
    address: str
    postal_code: str
    fax: Optional[str]
    email: Optional[str]
    filing_status: FilingStatus
    created_at: datetime
    updated_at: datetime


class EmploymentReportBase(BaseModel):
    baseline_employees: int = Field(..., ge=0)
    current_employees: int = Field(..., ge=0)
    reduction_type: Optional[ReductionType] = None
    primary_reason: Optional[ReductionReason] = None
    primary_reason_detail: Optional[str] = Field(None, max_length=500)
    secondary_reason: Optional[ReductionReason] = None
    secondary_reason_detail: Optional[str] = Field(None, max_length=500)
    report_month: str
    review_status: ReviewStatus = ReviewStatus.DRAFT

    @field_validator("report_month")
    @classmethod
    def validate_report_month(cls, value: str) -> str:
        if not REPORT_MONTH_PATTERN.fullmatch(value):
            raise ValueError("report_month must use YYYY-MM format")
        return value

    @model_validator(mode="after")
    def validate_reduction_fields(self) -> "EmploymentReportBase":
        if self.current_employees < self.baseline_employees:
            missing_fields = []
            if self.reduction_type is None:
                missing_fields.append("reduction_type")
            if self.primary_reason is None:
                missing_fields.append("primary_reason")
            if not self.primary_reason_detail:
                missing_fields.append("primary_reason_detail")
            if missing_fields:
                joined = ", ".join(missing_fields)
                raise ValueError(
                    f"When current_employees is less than baseline_employees, the following fields are required: {joined}"
                )
        return self


class EmploymentReportCreate(EmploymentReportBase):
    enterprise_id: int


class EmploymentReportSubmit(BaseModel):
    baseline_employees: int = Field(..., ge=0)
    current_employees: int = Field(..., ge=0)
    reduction_type: Optional[ReductionType] = None
    primary_reason: Optional[ReductionReason] = None
    primary_reason_detail: Optional[str] = Field(None, max_length=500)
    secondary_reason: Optional[ReductionReason] = None
    secondary_reason_detail: Optional[str] = Field(None, max_length=500)
    report_month: str

    @field_validator("report_month")
    @classmethod
    def validate_report_month(cls, value: str) -> str:
        if not REPORT_MONTH_PATTERN.fullmatch(value):
            raise ValueError("report_month must use YYYY-MM format")
        return value

    @model_validator(mode="after")
    def validate_reduction_fields(self) -> "EmploymentReportSubmit":
        EmploymentReportBase(
            baseline_employees=self.baseline_employees,
            current_employees=self.current_employees,
            reduction_type=self.reduction_type,
            primary_reason=self.primary_reason,
            primary_reason_detail=self.primary_reason_detail,
            secondary_reason=self.secondary_reason,
            secondary_reason_detail=self.secondary_reason_detail,
            report_month=self.report_month,
        )
        return self


class EmploymentReportUpdate(BaseModel):
    baseline_employees: Optional[int] = Field(None, ge=0)
    current_employees: Optional[int] = Field(None, ge=0)
    reduction_type: Optional[ReductionType] = None
    primary_reason: Optional[ReductionReason] = None
    primary_reason_detail: Optional[str] = Field(None, max_length=500)
    secondary_reason: Optional[ReductionReason] = None
    secondary_reason_detail: Optional[str] = Field(None, max_length=500)
    report_month: Optional[str] = None
    review_status: Optional[ReviewStatus] = None

    @field_validator("report_month")
    @classmethod
    def validate_report_month(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not REPORT_MONTH_PATTERN.fullmatch(value):
            raise ValueError("report_month must use YYYY-MM format")
        return value

    @model_validator(mode="after")
    def validate_partial_reduction_fields(self) -> "EmploymentReportUpdate":
        if (
            self.baseline_employees is not None
            and self.current_employees is not None
            and self.current_employees < self.baseline_employees
        ):
            missing_fields = []
            if self.reduction_type is None:
                missing_fields.append("reduction_type")
            if self.primary_reason is None:
                missing_fields.append("primary_reason")
            if not self.primary_reason_detail:
                missing_fields.append("primary_reason_detail")
            if missing_fields:
                joined = ", ".join(missing_fields)
                raise ValueError(
                    f"When current_employees is less than baseline_employees, the following fields are required: {joined}"
                )
        return self


class EmploymentReportAuditRequest(BaseModel):
    action: AuditAction


class EmploymentReportRead(ORMBaseSchema):
    id: int
    enterprise_id: int
    baseline_employees: int
    current_employees: int
    reduction_type: Optional[ReductionType]
    primary_reason: Optional[ReductionReason]
    primary_reason_detail: Optional[str]
    secondary_reason: Optional[ReductionReason]
    secondary_reason_detail: Optional[str]
    report_month: str
    review_status: ReviewStatus
    created_at: datetime
    updated_at: datetime


class ReportingWindowConfigBase(BaseModel):
    report_month: str
    start_at: datetime
    end_at: datetime

    @field_validator("report_month")
    @classmethod
    def validate_report_month(cls, value: str) -> str:
        if not REPORT_MONTH_PATTERN.fullmatch(value):
            raise ValueError("report_month must use YYYY-MM format")
        return value

    @model_validator(mode="after")
    def validate_time_range(self) -> "ReportingWindowConfigBase":
        if self.start_at >= self.end_at:
            raise ValueError("start_at must be earlier than end_at")
        return self


class ReportingWindowConfigUpsert(ReportingWindowConfigBase):
    pass


class ReportingWindowConfigRead(ORMBaseSchema):
    id: int
    report_month: str
    start_at: datetime
    end_at: datetime
    created_at: datetime
    updated_at: datetime


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class NotificationCreate(NotificationBase):
    publisher_id: int


class NotificationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)


class NotificationRead(ORMBaseSchema):
    id: int
    title: str
    content: str
    publisher_id: int
    published_at: datetime


class ProvinceCityStatisticsRead(BaseModel):
    city: str
    enterprise_count: int
    total_employment: int
    total_job_changes: int


class MonthlyJobChangeTrendRead(BaseModel):
    report_month: str
    total_job_changes: int


class SystemMonitorRead(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_bytes: int
    memory_total_bytes: int
