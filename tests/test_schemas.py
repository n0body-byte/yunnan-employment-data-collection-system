from __future__ import annotations

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from app.enums import AuditAction, FilingStatus, ReductionReason, ReductionType, ReviewStatus, UserRole
from app.schemas import (
    EmploymentReportAuditRequest,
    EmploymentReportSubmit,
    EnterpriseFilingSubmit,
    EnterpriseRead,
    NotificationRead,
    ReportingWindowConfigUpsert,
    UserRead,
)


class SchemaValidationTests(unittest.TestCase):
    def test_enterprise_filing_submit_accepts_valid_payload(self) -> None:
        payload = EnterpriseFilingSubmit(
            organization_code="A1B2C3D4E",
            name="Yunnan Test Enterprise",
            nature="Private Enterprise",
            industry="Manufacturing",
            main_business="Industrial product manufacturing",
            contact_person="Alice",
            phone="13800138000",
            region="Kunming",
            address="Kunming City",
            postal_code="650000",
            fax="0871-12345678",
            email="contact@example.com",
            filing_status=FilingStatus.PENDING,
        )
        self.assertEqual(payload.organization_code, "A1B2C3D4E")

    def test_enterprise_submit_rejects_invalid_phone(self) -> None:
        with self.assertRaises(ValidationError):
            EnterpriseFilingSubmit(
                organization_code="A1B2C3D4E",
                name="Yunnan Test Enterprise",
                nature="Private Enterprise",
                industry="Manufacturing",
                main_business="Industrial product manufacturing",
                contact_person="Alice",
                phone="123456",
                region="Kunming",
                address="Kunming City",
                postal_code="650000",
            )

    def test_employment_report_requires_reduction_reason_when_headcount_drops(self) -> None:
        with self.assertRaises(ValidationError):
            EmploymentReportSubmit(
                baseline_employees=100,
                current_employees=80,
                report_month="2023-10",
            )

    def test_employment_report_accepts_reduction_reason_when_headcount_drops(self) -> None:
        payload = EmploymentReportSubmit(
            baseline_employees=100,
            current_employees=80,
            reduction_type=ReductionType.ECONOMIC_LAYOFF,
            primary_reason=ReductionReason.INSUFFICIENT_ORDERS,
            primary_reason_detail="Quarterly orders declined significantly",
            secondary_reason=ReductionReason.LABOR_COST_RISE,
            secondary_reason_detail="Insurance costs increased",
            report_month="2023-10",
        )
        self.assertEqual(payload.report_month, "2023-10")

    def test_audit_request_accepts_only_enum_action(self) -> None:
        payload = EmploymentReportAuditRequest(action=AuditAction.APPROVE)
        self.assertEqual(payload.action, AuditAction.APPROVE)

        with self.assertRaises(ValidationError):
            EmploymentReportAuditRequest(action="pass")

    def test_reporting_window_requires_start_before_end(self) -> None:
        with self.assertRaises(ValidationError):
            ReportingWindowConfigUpsert(
                report_month="2026-04",
                start_at=datetime(2026, 4, 20, tzinfo=UTC),
                end_at=datetime(2026, 4, 10, tzinfo=UTC),
            )

    def test_read_schemas_support_from_attributes(self) -> None:
        now = datetime.now(UTC)

        class UserObj:
            id = 1
            username = "province_admin"
            role = UserRole.PROVINCE
            region = "Yunnan"
            created_at = now
            updated_at = now

        class EnterpriseObj:
            id = 2
            owner_user_id = 1
            organization_code = "A1B2C3D4E"
            name = "Yunnan Test Enterprise"
            nature = "State-Owned Enterprise"
            industry = "Manufacturing"
            main_business = "Industrial manufacturing"
            contact_person = "Bob"
            phone = "13800138000"
            region = "Kunming"
            address = "Panlong District"
            postal_code = "650000"
            fax = None
            email = "corp@example.com"
            filing_status = FilingStatus.APPROVED
            created_at = now
            updated_at = now

        class NotificationObj:
            id = 10
            title = "Submission Notice"
            content = "Please complete the monthly report on time."
            publisher_id = 1
            published_at = now

        user = UserRead.model_validate(UserObj())
        enterprise = EnterpriseRead.model_validate(EnterpriseObj())
        notification = NotificationRead.model_validate(NotificationObj())

        self.assertEqual(user.username, "province_admin")
        self.assertEqual(enterprise.filing_status, FilingStatus.APPROVED)
        self.assertEqual(notification.title, "Submission Notice")

    def test_review_status_contains_multi_level_workflow(self) -> None:
        self.assertEqual(ReviewStatus.PENDING_CITY_REVIEW, "PENDING_CITY_REVIEW")
        self.assertEqual(ReviewStatus.PENDING_PROVINCE_REVIEW, "PENDING_PROVINCE_REVIEW")
        self.assertEqual(ReviewStatus.ARCHIVED, "ARCHIVED")
        self.assertEqual(len(list(ReductionReason)), 14)
        self.assertEqual(len(list(ReductionType)), 10)


if __name__ == "__main__":
    unittest.main()
