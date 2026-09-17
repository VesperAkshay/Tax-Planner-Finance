"""
Document Pre-Classification, Encryption Check, and Forex Detection (v1.1 Phase 16: Tasks 16.1, 16.2, 16.5).

Provides:
- 16.1: Pre-classification before full parsing: detects non-financial documents (e.g. essays, invoices, contracts)
        before running the Docling pipeline.
- 16.2: Explicit password/encryption detection for PDFs.
- 16.5: Forex transaction detection (non-INR currency markers, forex markup, overseas spending).
"""

from pathlib import Path
import re
from typing import List, Optional, Tuple, Union

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None


# Forex regex matching major currencies, symbols, and forex transaction markers
FOREX_REGEX = re.compile(
    r"\b(USD|EUR|GBP|AED|SGD|CAD|AUD|JPY|THB|CHF|FOREX|FX\s+MARKUP|FCY|CROSS\s+CURRENCY|INTL\s+POS|OVERSEAS|INTERNATIONAL\s+TXN|FOREIGN\s+CURRENCY)\b|[\$€£¥]",
    re.IGNORECASE,
)


def is_forex_transaction(description: str) -> bool:
    """
    Task 16.5: Detects if a transaction description indicates a foreign currency
    or cross-border card transaction rather than domestic INR.
    """
    if not description:
        return False
    return bool(FOREX_REGEX.search(description))


def is_pdf_password_protected(file_path: Union[str, Path], raw_bytes: Optional[bytes] = None) -> bool:
    """
    Task 16.2: Explicitly checks if a PDF is password-protected or encrypted.
    Uses both bytecode /Encrypt marker inspection and pypdfium2 authorization test.
    """
    path = Path(file_path).resolve()
    content = raw_bytes
    if content is None and path.exists():
        with open(path, "rb") as f:
            content = f.read()

    if content and b"/Encrypt" in content:
        # Check if it can open without password using pypdfium2
        if pdfium is not None:
            try:
                doc = pdfium.PdfDocument(str(path))
                # If opening first page fails or raises, it is password-locked
                _ = doc[0]
                return False
            except Exception as e:
                err_str = str(e).lower()
                if "password" in err_str or "unauthorized" in err_str or "encrypt" in err_str or "locked" in err_str:
                    return True
                # If pypdfium threw any error when /Encrypt is present, treat as encrypted
                return True
        return True

    return False


def pre_classify_pdf_structure(file_path: Union[str, Path]) -> str:
    """
    Task 16.1: Quickly inspects the first few pages of a PDF to classify its structure:
    Returns:
    - 'bank_statement'
    - 'salary_slip'
    - 'non_financial' (reject early before expensive OCR)
    - 'unreadable'
    """
    path = Path(file_path).resolve()
    if not path.exists():
        return "unreadable"

    if pdfium is None:
        return "bank_statement"  # Fallback if pdfium unavailable

    try:
        doc = pdfium.PdfDocument(str(path))
        extracted_text = ""
        for i in range(min(3, len(doc))):
            extracted_text += " " + doc[i].get_textpage().get_text_range()
    except Exception:
        return "unreadable"

    text_lower = extracted_text.lower()

    bank_keywords = [
        "statement", "account", "balance", "deposit", "withdrawal", "credit", "debit",
        "transaction", "narration", "particulars", "chq", "cheque", "ifsc", "opening bal",
        "closing bal", "savings a/c", "current a/c", "bank"
    ]
    salary_keywords = [
        "salary", "payslip", "pay slip", "earnings", "deductions", "basic", "hra",
        "gross pay", "net pay", "provident fund", "pf", "epf", "allowance", "ctc"
    ]

    bank_matches = sum(1 for kw in bank_keywords if kw in text_lower)
    salary_matches = sum(1 for kw in salary_keywords if kw in text_lower)

    if salary_matches >= 3 and salary_matches >= bank_matches:
        return "salary_slip"
    elif bank_matches >= 2:
        return "bank_statement"
    else:
        return "non_financial"


def pre_classify_csv_structure(content_str: str) -> bool:
    """
    Task 16.1: Checks if CSV header and top lines resemble a financial statement.
    Returns True if valid financial indicators found, False otherwise.
    """
    lines = [line.strip() for line in content_str.splitlines() if line.strip()]
    if not lines:
        return False

    sample = " ".join(lines[:15]).lower()
    financial_indicators = [
        "date", "amount", "balance", "debit", "credit", "withdrawal", "deposit",
        "description", "narration", "particulars", "trans", "txn", "chq", "ref"
    ]
    matches = sum(1 for ind in financial_indicators if ind in sample)
    return matches >= 2
