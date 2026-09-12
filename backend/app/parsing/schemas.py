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
    needs_review: bool = False
    is_scanned: bool = False
    warnings: List[str] = []
    raw_tables_count: int = 0
