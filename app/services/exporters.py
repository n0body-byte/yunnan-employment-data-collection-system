from __future__ import annotations

from io import BytesIO
from typing import Any, Iterable


def _create_workbook(title: str):
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl is required to export xlsx files") from exc

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = title
    return workbook, worksheet


def _save_workbook(workbook) -> bytes:
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def export_enterprise_filings_to_xlsx(enterprises: Iterable[Any]) -> bytes:
    workbook, worksheet = _create_workbook("Enterprise Filings")
    headers = [
        "Region",
        "Organization Code",
        "Enterprise Name",
        "Nature",
        "Industry",
        "Main Business",
        "Contact Person",
        "Phone",
        "Address",
        "Postal Code",
        "Fax",
        "Email",
        "Filing Status",
        "Audit Remark",
    ]
    worksheet.append(headers)

    for enterprise in enterprises:
        worksheet.append([
            getattr(enterprise, "region", ""),
            getattr(enterprise, "organization_code", ""),
            getattr(enterprise, "name", ""),
            getattr(enterprise, "nature", ""),
            getattr(enterprise, "industry", ""),
            getattr(enterprise, "main_business", ""),
            getattr(enterprise, "contact_person", ""),
            getattr(enterprise, "phone", ""),
            getattr(enterprise, "address", ""),
            getattr(enterprise, "postal_code", ""),
            getattr(enterprise, "fax", "") or "",
            getattr(enterprise, "email", "") or "",
            getattr(getattr(enterprise, "filing_status", ""), "value", getattr(enterprise, "filing_status", "")),
            getattr(enterprise, "filing_audit_remark", "") or "",
        ])

    for column, width in {
        "A": 16,
        "B": 18,
        "C": 24,
        "D": 16,
        "E": 20,
        "F": 30,
        "G": 14,
        "H": 18,
        "I": 30,
        "J": 12,
        "K": 18,
        "L": 24,
        "M": 16,
        "N": 28,
    }.items():
        worksheet.column_dimensions[column].width = width

    return _save_workbook(workbook)


def export_user_list_to_xlsx(users: Iterable[Any]) -> bytes:
    workbook, worksheet = _create_workbook("Users")
    worksheet.append([
        "Username",
        "Role",
        "Region",
        "Managed Role Id",
        "Is Active",
        "Created At",
    ])

    for user in users:
        worksheet.append([
            getattr(user, "username", ""),
            getattr(getattr(user, "role", ""), "value", getattr(user, "role", "")),
            getattr(user, "region", ""),
            getattr(user, "managed_role_id", "") or "",
            "Yes" if getattr(user, "is_active", False) else "No",
            str(getattr(user, "created_at", "") or ""),
        ])

    for column, width in {"A": 20, "B": 14, "C": 18, "D": 18, "E": 12, "F": 24}.items():
        worksheet.column_dimensions[column].width = width

    return _save_workbook(workbook)


def export_report_list_to_xlsx(reports: Iterable[Any]) -> bytes:
    workbook, worksheet = _create_workbook("Employment Reports")
    worksheet.append([
        "Enterprise Id",
        "Report Month",
        "Baseline Employees",
        "Current Employees",
        "Reduction Type",
        "Primary Reason",
        "Primary Reason Detail",
        "Secondary Reason",
        "Secondary Reason Detail",
        "Third Reason",
        "Third Reason Detail",
        "Review Status",
        "Return Remark",
        "Reported To Ministry At",
    ])

    for report in reports:
        worksheet.append([
            getattr(report, "enterprise_id", ""),
            getattr(report, "report_month", ""),
            getattr(report, "baseline_employees", ""),
            getattr(report, "current_employees", ""),
            getattr(getattr(report, "reduction_type", ""), "value", getattr(report, "reduction_type", "")),
            getattr(getattr(report, "primary_reason", ""), "value", getattr(report, "primary_reason", "")),
            getattr(report, "primary_reason_detail", "") or "",
            getattr(getattr(report, "secondary_reason", ""), "value", getattr(report, "secondary_reason", "")),
            getattr(report, "secondary_reason_detail", "") or "",
            getattr(getattr(report, "third_reason", ""), "value", getattr(report, "third_reason", "")),
            getattr(report, "third_reason_detail", "") or "",
            getattr(getattr(report, "review_status", ""), "value", getattr(report, "review_status", "")),
            getattr(report, "return_remark", "") or "",
            str(getattr(report, "reported_to_ministry_at", "") or ""),
        ])

    for column, width in {
        "A": 14,
        "B": 14,
        "C": 18,
        "D": 18,
        "E": 20,
        "F": 20,
        "G": 30,
        "H": 20,
        "I": 30,
        "J": 20,
        "K": 30,
        "L": 18,
        "M": 28,
        "N": 24,
    }.items():
        worksheet.column_dimensions[column].width = width

    return _save_workbook(workbook)
