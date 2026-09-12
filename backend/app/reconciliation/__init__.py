"""
Reconciliation Module for Salary Slips vs Bank Transactions (Phase 4).
"""

from app.reconciliation.constants import (
    BONUS_RATIO_THRESHOLD,
    DEFAULT_RECONCILIATION_TOLERANCE_ABSOLUTE,
    DEFAULT_RECONCILIATION_TOLERANCE_PERCENT,
    FLAG_TYPE_BONUS_VARIABLE_PAY,
    FLAG_TYPE_MISMATCHED_AMOUNT,
    FLAG_TYPE_MISSING_BANK_CREDIT,
    FLAG_TYPE_MISSING_SALARY_SLIP,
    FLAG_TYPE_UNEXPLAINED_CREDIT,
    STATUS_IGNORED,
    STATUS_PENDING,
    STATUS_RESOLVED,
    VALID_FLAG_TYPES,
    VALID_STATUSES,
)
from app.reconciliation.matcher import (
    compute_reconciliation_tolerance,
    filter_credits_for_month,
    get_month_credit_window,
    is_salary_credit_narration,
    reconcile_month,
    reconcile_salary_and_bank,
)
from app.reconciliation.schemas import (
    BankCreditItem,
    MonthReconciliationResult,
    ReconciliationFlagItem,
    ReconciliationReport,
    SalarySlipItem,
)
from app.reconciliation.self_transfer import (
    detect_and_update_self_transfers_db,
    detect_self_transfers,
)
from app.reconciliation.service import (
    get_user_reconciliation_flags,
    resolve_reconciliation_flag,
    run_reconciliation_pipeline,
)

__all__ = [
    "BONUS_RATIO_THRESHOLD",
    "BankCreditItem",
    "DEFAULT_RECONCILIATION_TOLERANCE_ABSOLUTE",
    "DEFAULT_RECONCILIATION_TOLERANCE_PERCENT",
    "FLAG_TYPE_BONUS_VARIABLE_PAY",
    "FLAG_TYPE_MISMATCHED_AMOUNT",
    "FLAG_TYPE_MISSING_BANK_CREDIT",
    "FLAG_TYPE_MISSING_SALARY_SLIP",
    "FLAG_TYPE_UNEXPLAINED_CREDIT",
    "MonthReconciliationResult",
    "ReconciliationFlagItem",
    "ReconciliationReport",
    "STATUS_IGNORED",
    "STATUS_PENDING",
    "STATUS_RESOLVED",
    "SalarySlipItem",
    "VALID_FLAG_TYPES",
    "VALID_STATUSES",
    "compute_reconciliation_tolerance",
    "detect_and_update_self_transfers_db",
    "detect_self_transfers",
    "filter_credits_for_month",
    "get_month_credit_window",
    "get_user_reconciliation_flags",
    "is_salary_credit_narration",
    "reconcile_month",
    "reconcile_salary_and_bank",
    "resolve_reconciliation_flag",
    "run_reconciliation_pipeline",
]
