# Confidence threshold below which needs_review must be set to True (Task 2.9)
DEFAULT_REVIEW_THRESHOLD: float = 0.85

# Minimum confidence required for individual transaction row to be considered high quality
HIGH_CONFIDENCE_ROW_THRESHOLD: float = 0.90

# Header patterns for bank statement table column detection (case-insensitive)
DATE_HEADER_PATTERNS = [
    "date",
    "txn date",
    "transaction date",
    "trans date",
    "value date",
    "post date",
    "posting date",
]

DESCRIPTION_HEADER_PATTERNS = [
    "narration",
    "description",
    "particulars",
    "transaction details",
    "details",
    "remarks",
    "transaction remarks",
]

REF_NO_HEADER_PATTERNS = [
    "chq/ref no",
    "ref no",
    "cheque no",
    "chq no",
    "reference",
    "ref no.",
    "utr",
    "transaction id",
    "txn id",
]

DEBIT_HEADER_PATTERNS = [
    "debit",
    "withdrawal",
    "withdrawals",
    "dr",
    "dr amount",
    "debit amount",
    "withdrawal (dr)",
]

CREDIT_HEADER_PATTERNS = [
    "credit",
    "deposit",
    "deposits",
    "cr",
    "cr amount",
    "credit amount",
    "deposit (cr)",
]

AMOUNT_HEADER_PATTERNS = [
    "amount",
    "txn amount",
    "transaction amount",
]

BALANCE_HEADER_PATTERNS = [
    "balance",
    "closing balance",
    "running balance",
    "available balance",
    "bal",
]

# Supported date formats common in Indian bank statements
COMMON_DATE_FORMATS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d/%m/%y",
    "%d-%m-%y",
    "%d-%b-%Y",
    "%d-%b-%y",
    "%d %b %Y",
    "%Y-%m-%d",
    "%d.%m.%Y",
]
