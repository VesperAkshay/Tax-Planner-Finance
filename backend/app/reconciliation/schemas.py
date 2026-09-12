"""
Pydantic Schemas for Salary Slip vs Bank Reconciliation (Phase 4).
"""

from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.reconciliation.constants import (
    DEFAULT_RECONCILIATION_TOLERANCE_ABSOLUTE,
    DEFAULT_RECONCILIATION_TOLERANCE_PERCENT,
    STATUS_PENDING,
)


class SalarySlipItem(BaseModel):
    id: Optional[int] = None
    month: int
    year: int
    net_pay: float
    gross_pay: float
    file_name: Optional[str] = None


class BankCreditItem(BaseModel):
    id: Optional[int] = None
    date: date
    amount: float
    description: str
    is_salary: bool = True
    account_id: Optional[int] = None


class ReconciliationFlagItem(BaseModel):
    salary_slip_id: Optional[int] = None
    transaction_id: Optional[int] = None
    month: int
    year: int
    flag_type: str
    expected_amount: Optional[float] = None
    actual_amount: Optional[float] = None
    difference: Optional[float] = None
    tolerance_applied: float = 0.0
    status: str = STATUS_PENDING
    details: str = ""


class MonthReconciliationResult(BaseModel):
    month: int
    year: int
    status: str  # matched, mismatched, missing_slip, missing_credit, bonus_detected
    slip: Optional[SalarySlipItem] = None
    credits: List[BankCreditItem] = []
    flags: List[ReconciliationFlagItem] = []
    is_reconciled: bool = False


class ReconciliationReport(BaseModel):
    user_id: int
    months_evaluated: int
    matched_months_count: int
    flagged_months_count: int
    total_flags: int
    flags: List[ReconciliationFlagItem]
    month_results: List[MonthReconciliationResult]
