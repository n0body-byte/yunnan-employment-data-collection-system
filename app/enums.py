from enum import Enum


class StrEnum(str, Enum):
    """String-backed enum for clean JSON serialization."""


class UserRole(StrEnum):
    PROVINCE = "PROVINCE"
    CITY = "CITY"
    ENTERPRISE = "ENTERPRISE"


class FilingStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReviewStatus(StrEnum):
    DRAFT = "DRAFT"
    PENDING_CITY_REVIEW = "PENDING_CITY_REVIEW"
    PENDING_PROVINCE_REVIEW = "PENDING_PROVINCE_REVIEW"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class AuditAction(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ReductionType(StrEnum):
    CLOSED_BANKRUPT = "\u5173\u95ed\u7834\u4ea7"
    SUSPENSION_REORGANIZATION = "\u505c\u4e1a\u6574\u987f"
    ECONOMIC_LAYOFF = "\u7ecf\u6d4e\u6027\u88c1\u5458"
    BUSINESS_TRANSFER = "\u4e1a\u52a1\u8f6c\u79fb"
    NATURAL_ATTRITION = "\u81ea\u7136\u51cf\u5458"
    NORMAL_CONTRACT_TERMINATION = "\u6b63\u5e38\u89e3\u9664\u6216\u7ec8\u6b62\u52b3\u52a8\u5408\u540c"
    INTERNATIONAL_FACTORS = "\u56fd\u9645\u56e0\u7d20\u53d8\u5316\u5f71\u54cd"
    NATURAL_DISASTER = "\u81ea\u7136\u707e\u5bb3"
    MAJOR_EVENT = "\u91cd\u5927\u4e8b\u4ef6\u5f71\u54cd"
    OTHER = "\u5176\u4ed6"


class ReductionReason(StrEnum):
    INDUSTRIAL_RESTRUCTURING = "\u4ea7\u4e1a\u7ed3\u6784\u8c03\u6574"
    TECHNOLOGICAL_REFORM = "\u91cd\u5927\u6280\u672f\u6539\u9769"
    ENERGY_SAVING_AND_CAPACITY_REDUCTION = "\u8282\u80fd\u51cf\u6392\u3001\u6dd8\u6c70\u843d\u540e\u4ea7\u80fd"
    INSUFFICIENT_ORDERS = "\u8ba2\u5355\u4e0d\u8db3"
    RAW_MATERIAL_PRICE_RISE = "\u539f\u6750\u6599\u6da8\u4ef7"
    LABOR_COST_RISE = "\u5de5\u8d44\u3001\u793e\u4fdd\u7b49\u7528\u5de5\u6210\u672c\u4e0a\u5347"
    NATURAL_ATTRITION = "\u81ea\u7136\u51cf\u5458"
    FUNDING_DIFFICULTY = "\u7ecf\u8425\u8d44\u91d1\u56f0\u96be"
    TAX_POLICY_CHANGE = "\u7a0e\u6536\u653f\u7b56\u53d8\u5316\uff08\u5305\u62ec\u7a0e\u8d1f\u589e\u52a0\u6216\u51fa\u53e3\u9000\u7a0e\u51cf\u5c11\u7b49\uff09"
    SEASONAL_EMPLOYMENT = "\u5b63\u8282\u6027\u7528\u5de5"
    OTHER = "\u5176\u4ed6"
    VOLUNTARY_RESIGNATION = "\u81ea\u884c\u79bb\u804c"
    JOB_TRANSFER_AND_INTERNAL_REALLOCATION = "\u5de5\u4f5c\u8c03\u52a8\u3001\u4f01\u4e1a\u5185\u90e8\u8c03\u5242"
    LABOR_RELATION_TRANSFER_AND_DISPATCH = "\u52b3\u52a8\u5173\u7cfb\u8f6c\u79fb\u3001\u52b3\u52a1\u6d3e\u9063"
