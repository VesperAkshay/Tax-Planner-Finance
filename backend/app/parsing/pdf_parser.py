from datetime import date, datetime
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from app.parsing.constants import (
    AMOUNT_HEADER_PATTERNS,
    BALANCE_HEADER_PATTERNS,
    COMMON_DATE_FORMATS,
    CREDIT_HEADER_PATTERNS,
    DATE_HEADER_PATTERNS,
    DEBIT_HEADER_PATTERNS,
    DEFAULT_REVIEW_THRESHOLD,
    DESCRIPTION_HEADER_PATTERNS,
    REF_NO_HEADER_PATTERNS,
)
from app.parsing.schemas import ParsedTransactionRow, StatementParseResult


def clean_header(header: Any) -> str:
    """Normalize header text for robust matching."""
    if header is None:
        return ""
    text = str(header).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def parse_date(val: Any) -> Optional[date]:
    """Attempts to parse a string or cell value into a datetime.date."""
    if val is None or pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str:
        return None

    # Clean any surrounding noise (e.g. quotes, brackets)
    val_str = re.sub(r"^[^\w]+|[^\w]+$", "", val_str)

    # First check standard formats
    for fmt in COMMON_DATE_FORMATS:
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            continue

    # Try regex extraction of DD/MM/YYYY or DD-MM-YYYY within string
    match = re.search(r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})", val_str)
    if match:
        d, m, y = match.groups()
        if len(y) == 2:
            y = f"20{y}"
        try:
            return date(int(y), int(m), int(d))
        except ValueError:
            pass

    return None


def parse_numeric(val: Any) -> Optional[float]:
    """Cleans currency strings into floats (e.g. '₹ 1,234.50' -> 1234.50)."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()
    if not s or s.lower() in ("-", "nil", "na", "n/a", "none"):
        return None

    # Remove currency symbols and formatting
    s = re.sub(r"[₹$€£\s,]", "", s)

    # Handle parenthesis negative e.g. (100.0)
    if s.startswith("(") and s.endswith(")"):
        s = f"-{s[1:-1]}"

    # Handle Dr / Cr suffixes e.g. 500.00Dr
    s = re.sub(r"(?i)(dr|cr)", "", s).strip()

    try:
        return float(s)
    except ValueError:
        return None


class DoclingPDFParser:
    """
    Unified parser for text-based and scanned/image PDF bank statements using Docling.
    Both text and OCR pipelines flow through the exact same row normalization logic,
    returning identical StatementParseResult and ParsedTransactionRow formats (Tasks 2.1 & 2.2).
    """

    def __init__(self, ocr_mode: Union[str, bool] = "auto"):
        """
        ocr_mode:
            - 'auto' (default): tries text extraction first; if 0 rows detected, retries with OCR.
            - 'force_ocr' or True: always uses Docling built-in OCR.
            - 'never' or False: text-only extraction without OCR fallback.
        """
        if isinstance(ocr_mode, bool):
            self.ocr_mode = "force_ocr" if ocr_mode else "never"
        else:
            self.ocr_mode = ocr_mode.lower()

        self._text_converter: Optional[DocumentConverter] = None
        self._ocr_converter: Optional[DocumentConverter] = None

    def _get_converter(self, use_ocr: bool) -> DocumentConverter:
        """Lazily initialize converters to conserve memory and startup time."""
        if use_ocr:
            if self._ocr_converter is None:
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_table_structure = True
                pipeline_options.do_ocr = True
                pipeline_options.ocr_options = RapidOcrOptions()

                self._ocr_converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                    }
                )
            return self._ocr_converter
        else:
            if self._text_converter is None:
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_table_structure = True
                pipeline_options.do_ocr = False

                self._text_converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                    }
                )
            return self._text_converter

    def _find_matching_column(
        self, columns: List[str], patterns: List[str]
    ) -> Optional[str]:
        """Finds the first column whose normalized name matches any of the patterns."""
        for col in columns:
            clean_col = clean_header(col)
            for pat in patterns:
                if pat == clean_col or pat in clean_col:
                    return col
        return None

    def _identify_columns(self, df: pd.DataFrame) -> Dict[str, Optional[str]]:
        """Maps detected DataFrame columns to standard schema fields."""
        cols = [str(c) for c in df.columns]
        mapping = {
            "date": self._find_matching_column(cols, DATE_HEADER_PATTERNS),
            "description": self._find_matching_column(cols, DESCRIPTION_HEADER_PATTERNS),
            "ref_no": self._find_matching_column(cols, REF_NO_HEADER_PATTERNS),
            "debit": self._find_matching_column(cols, DEBIT_HEADER_PATTERNS),
            "credit": self._find_matching_column(cols, CREDIT_HEADER_PATTERNS),
            "amount": self._find_matching_column(cols, AMOUNT_HEADER_PATTERNS),
            "balance": self._find_matching_column(cols, BALANCE_HEADER_PATTERNS),
        }
        return mapping

    def _is_transaction_table(self, col_map: Dict[str, Optional[str]]) -> bool:
        """Determines whether a table represents transactions."""
        has_date = col_map["date"] is not None
        has_desc = col_map["description"] is not None
        has_amount_info = (
            (col_map["debit"] is not None or col_map["credit"] is not None)
            or col_map["amount"] is not None
        )
        return has_date and (has_desc or has_amount_info)

    def _parse_dataframe_transactions(
        self, df: pd.DataFrame, col_map: Dict[str, Optional[str]], is_ocr: bool = False
    ) -> List[ParsedTransactionRow]:
        """Parses rows from a validated transaction table DataFrame."""
        rows: List[ParsedTransactionRow] = []

        date_col = col_map["date"]
        desc_col = col_map["description"]
        ref_col = col_map["ref_no"]
        debit_col = col_map["debit"]
        credit_col = col_map["credit"]
        amount_col = col_map["amount"]
        bal_col = col_map["balance"]

        # Base confidence: 0.95 for direct text, 0.90 for OCR
        base_confidence = 0.90 if is_ocr else 0.95

        for _, raw_row in df.iterrows():
            txn_date = parse_date(raw_row.get(date_col)) if date_col else None
            if not txn_date:
                continue

            raw_desc = str(raw_row.get(desc_col, "")).strip() if desc_col else ""
            if not raw_desc or raw_desc.lower() in ("nan", "none", ""):
                raw_desc = "Unknown Narration"

            ref_no = None
            if ref_col:
                val = str(raw_row.get(ref_col, "")).strip()
                if val and val.lower() not in ("nan", "none", "-", ""):
                    ref_no = val

            amount = 0.0
            txn_type = "debit"
            confidence = base_confidence

            debit_val = parse_numeric(raw_row.get(debit_col)) if debit_col else None
            credit_val = parse_numeric(raw_row.get(credit_col)) if credit_col else None

            if debit_val is not None and debit_val > 0:
                amount = debit_val
                txn_type = "debit"
            elif credit_val is not None and credit_val > 0:
                amount = credit_val
                txn_type = "credit"
            elif amount_col:
                raw_amt = parse_numeric(raw_row.get(amount_col))
                if raw_amt is not None:
                    amount = abs(raw_amt)
                    raw_str = str(raw_row.get(amount_col, "")).lower()
                    if "cr" in raw_str or raw_amt > 0:
                        txn_type = "credit"
                    else:
                        txn_type = "debit"
                    confidence = round(base_confidence - 0.07, 2)

            if amount <= 0:
                continue

            balance_val = parse_numeric(raw_row.get(bal_col)) if bal_col else None

            rows.append(
                ParsedTransactionRow(
                    date=txn_date,
                    description=raw_desc,
                    amount=round(amount, 2),
                    transaction_type=txn_type,
                    balance=round(balance_val, 2) if balance_val is not None else None,
                    reference_number=ref_no,
                    parse_confidence=confidence,
                    raw_row=dict(raw_row.dropna()) if hasattr(raw_row, "dropna") else None,
                )
            )

        return rows

    def _convert_and_extract(
        self, file_path: Path, use_ocr: bool
    ) -> Tuple[List[ParsedTransactionRow], int, List[str]]:
        """Converts the PDF using the specified pipeline and extracts table rows."""
        converter = self._get_converter(use_ocr=use_ocr)
        conv_res = converter.convert(str(file_path))
        doc = conv_res.document

        extracted_rows: List[ParsedTransactionRow] = []
        tables_found = 0
        warnings: List[str] = []

        for table_item in doc.tables:
            tables_found += 1
            try:
                df = table_item.export_to_dataframe(doc=doc)
            except Exception as e:
                warnings.append(f"Could not export table: {e}")
                continue

            if df is None or df.empty:
                continue

            col_map = self._identify_columns(df)
            if self._is_transaction_table(col_map):
                table_rows = self._parse_dataframe_transactions(df, col_map, is_ocr=use_ocr)
                extracted_rows.extend(table_rows)

        return extracted_rows, tables_found, warnings

    def parse(
        self, file_path: Union[str, Path]
    ) -> StatementParseResult:
        """
        Parses a PDF bank statement file using Docling.
        Handles both text-based PDFs and scanned/image PDFs (using built-in OCR path).
        Returns a structured StatementParseResult with all extracted transactions.
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Statement file not found: {path}")

        use_ocr = (self.ocr_mode == "force_ocr")
        rows, tables_found, warnings = [], 0, []

        try:
            # First pass
            rows, tables_found, warnings = self._convert_and_extract(path, use_ocr=use_ocr)

            # Auto-fallback to OCR if 0 rows detected and mode is 'auto'
            if not rows and self.ocr_mode == "auto" and not use_ocr:
                use_ocr = True
                ocr_rows, ocr_tables, ocr_warnings = self._convert_and_extract(path, use_ocr=True)
                if ocr_rows:
                    rows = ocr_rows
                    tables_found = ocr_tables
                    warnings = ocr_warnings
        except Exception as exc:
            warnings.append(f"Conversion failed: {exc}")

        result = StatementParseResult(
            file_path=str(path),
            file_name=path.name,
            file_type="pdf_scanned" if use_ocr else "pdf_text",
            is_scanned=use_ocr,
            rows=rows,
            raw_tables_count=tables_found,
            warnings=warnings,
        )

        if rows:
            result.rows.sort(key=lambda r: r.date)
            result.statement_start_date = result.rows[0].date
            result.statement_end_date = result.rows[-1].date

            result.total_credits = round(
                sum(r.amount for r in result.rows if r.transaction_type == "credit"), 2
            )
            result.total_debits = round(
                sum(r.amount for r in result.rows if r.transaction_type == "debit"), 2
            )

            avg_row_confidence = sum(r.parse_confidence for r in result.rows) / len(result.rows)
            result.parse_confidence = round(avg_row_confidence, 3)

            first_bal = result.rows[0].balance
            last_bal = result.rows[-1].balance
            if first_bal is not None:
                if result.rows[0].transaction_type == "credit":
                    result.opening_balance = round(first_bal - result.rows[0].amount, 2)
                else:
                    result.opening_balance = round(first_bal + result.rows[0].amount, 2)
            if last_bal is not None:
                result.closing_balance = round(last_bal, 2)
        else:
            result.parse_confidence = 0.0
            result.warnings.append("No transaction rows detected in statement.")

        result.needs_review = result.parse_confidence < DEFAULT_REVIEW_THRESHOLD
        return result
