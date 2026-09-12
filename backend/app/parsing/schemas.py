from datetime import date as dt_date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ParsedTransactionRow(BaseModel):
    date: dt_date
    description: str
    amount: float = Field(ge=0.0)
    transaction_type: str = Field(pattern="^(credit|debit)$")
    balance: Optional[float] = None
    reference_number: Optional[str] = None
    parse_confidence: float = Field(ge=0.0, le=1.0, default=0.95)
    raw_row: Optional[Dict[str, Any]] = None


class StatementParseResult(BaseModel):
    file_path: str
    file_name: str
    file_type: str = "pdf_text"
    rows: List[ParsedTransactionRow] = []
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    statement_start_date: Optional[dt_date] = None
    statement_end_date: Optional[dt_date] = None
    total_credits: float = 0.0
    total_debits: float = 0.0
    parse_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    balance_reconciled: bool = False
    parse_status: str = "pending"  # pending, completed, failed, needs_review
    expected_closing_balance: Optional[float] = None
    balance_discrepancy: Optional[float] = None
    needs_review: bool = False
    is_scanned: bool = False
    warnings: List[str] = []
    raw_tables_count: int = 0

    def to_statement_upload_dict(
        self, user_id: Optional[int] = None, account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Converts result into a dict matching StatementUpload model attributes."""
        return {
            "user_id": user_id,
            "account_id": account_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "parse_status": self.parse_status,
            "parse_confidence": self.parse_confidence,
            "balance_reconciled": self.balance_reconciled,
            "opening_balance": self.opening_balance,
            "closing_balance": self.closing_balance,
            "statement_start_date": self.statement_start_date,
            "statement_end_date": self.statement_end_date,
            "needs_review": self.needs_review,
            "raw_metadata": {
                "total_credits": self.total_credits,
                "total_debits": self.total_debits,
                "expected_closing_balance": self.expected_closing_balance,
                "balance_discrepancy": self.balance_discrepancy,
                "raw_tables_count": self.raw_tables_count,
                "warnings": self.warnings,
            },
        }



class SalarySlipParseResult(BaseModel):
    """
    Structured extraction result for a salary slip PDF/image,
    conforming directly to the salary_slips database schema (Task 2.5 & 2.6).
    """
    file_path: str = ""
    file_name: str = ""
    month: int = Field(ge=1, le=12, default=4)
    year: int = Field(ge=2000, le=2100, default=2024)
    financial_year: str = Field(default="2024-2025")

    # Earnings
    basic: float = 0.0
    hra: float = 0.0
    lta: float = 0.0
    special_allowance: float = 0.0
    other_allowances: float = 0.0
    gross_pay: float = 0.0

    # Deductions
    employee_pf: float = 0.0
    employer_pf: float = 0.0
    professional_tax: float = 0.0
    tds: float = 0.0
    other_deductions: float = 0.0
    total_deductions: float = 0.0
    net_pay: float = 0.0

    # Validation & Confidence (Task 2.6 & 2.9)
    calculated_gross: float = 0.0
    gross_discrepancy: float = 0.0
    calculated_net: float = 0.0
    is_gross_valid: bool = True
    extraction_confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    needs_review: bool = False
    warnings: List[str] = []
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict_for_db(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Converts result into a dict matching SalarySlip model attributes."""
        return {
            "user_id": user_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "month": self.month,
            "year": self.year,
            "financial_year": self.financial_year,
            "basic": self.basic,
            "hra": self.hra,
            "lta": self.lta,
            "special_allowance": self.special_allowance,
            "other_allowances": self.other_allowances,
            "gross_pay": self.gross_pay,
            "employee_pf": self.employee_pf,
            "employer_pf": self.employer_pf,
            "professional_tax": self.professional_tax,
            "tds": self.tds,
            "other_deductions": self.other_deductions,
            "total_deductions": self.total_deductions,
            "net_pay": self.net_pay,
            "extraction_confidence": self.extraction_confidence,
            "is_gross_valid": self.is_gross_valid,
            "needs_review": self.needs_review,
            "raw_metadata": self.raw_metadata,
        }

