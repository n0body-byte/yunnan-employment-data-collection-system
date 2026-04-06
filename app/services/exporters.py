from __future__ import annotations

from io import BytesIO
from typing import Any, Iterable


def export_enterprise_filings_to_xlsx(enterprises: Iterable[Any]) -> bytes:
    """Export enterprise filing records to an XLSX binary."""
    try:
        from openpyxl import Workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl is required to export xlsx files") from exc

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Enterprise Filings"

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
        ])

    column_widths = {
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
        "M": 14,
    }
    for column, width in column_widths.items():
        worksheet.column_dimensions[column].width = width

    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
