import calendar
from datetime import datetime
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd

from app.parsing.constants import DEFAULT_REVIEW_THRESHOLD
from app.parsing.pdf_parser import clean_header, parse_numeric
from app.parsing.schemas import SalarySlipParseResult

# Gross pay tolerance settings (Task 2.6)
GROSS_TOLERANCE_ABSOLUTE: float = 5.0
GROSS_TOLERANCE_PERCENT: float = 0.01  # 1%

MONTH_NAME_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def calculate_financial_year(month: int, year: int) -> str:
    """Calculates the Indian Financial Year string (e.g. 2024-2025)."""
    if month >= 4:
        return f"{year}-{year + 1}"
    return f"{year - 1}-{year}"


def extract_period_from_text(text: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Extracts month and year from salary slip text/headers, and computes Indian financial year.
    Examples:
      'Payslip for the month of April 2024' -> (4, 2024, '2024-2025')
      'Pay Slip: 03/2025' -> (3, 2025, '2024-2025')
    """
    if not text:
        return None, None, None

    # Pattern 1: Month name followed or preceded by 4-digit year (e.g. 'April 2024' or '2024 April')
    month_names_regex = "|".join(MONTH_NAME_MAP.keys())
    m1 = re.search(rf"\b({month_names_regex})\b.*?(\b20\d{{2}}\b)", text, re.IGNORECASE)
    if m1:
        m_str, y_str = m1.group(1).lower(), m1.group(2)
        month = MONTH_NAME_MAP.get(m_str)
        year = int(y_str)
        if month:
            return month, year, calculate_financial_year(month, year)

    m1_rev = re.search(rf"(\b20\d{{2}}\b).*?\b({month_names_regex})\b", text, re.IGNORECASE)
    if m1_rev:
        y_str, m_str = m1_rev.group(1), m1_rev.group(2).lower()
        month = MONTH_NAME_MAP.get(m_str)
        year = int(y_str)
        if month:
            return month, year, calculate_financial_year(month, year)

    # Pattern 2: MM/YYYY or MM-YYYY
    m2 = re.search(r"\b(0?[1-9]|1[0-2])[/\-](20\d{2})\b", text)
    if m2:
        month = int(m2.group(1))
        year = int(m2.group(2))
        return month, year, calculate_financial_year(month, year)

    # Pattern 3: YYYY-MM
    m3 = re.search(r"\b(20\d{2})[/\-](0?[1-9]|1[0-2])\b", text)
    if m3:
        year = int(m3.group(1))
        month = int(m3.group(2))
        return month, year, calculate_financial_year(month, year)

    return None, None, None


# Regex patterns for salary slip component classification
EARNING_PATTERNS: Dict[str, List[str]] = {
    "basic": [
        r"\bbasic(?:\s+salary|\s+pay)?\b",
    ],
    "hra": [
        r"\bh\.?r\.?a\.?\b",
        r"\bhouse\s+rent\s+allowance\b",
    ],
    "lta": [
        r"\bl\.?t\.?[ac]\.?\b",
        r"\bleave\s+travel\s+allowance\b",
        r"\bleave\s+travel\s+concession\b",
    ],
    "special_allowance": [
        r"\bspecial\s+allowance\b",
        r"\bspl\.?\s*allowance\b",
        r"\bspl\.?\s*allow\b",
        r"\bspecial\s+allow\b",
    ],
    "other_allowances": [
        r"\bconveyance(?:\s+allowance)?\b",
        r"\btransport(?:\s+allowance)?\b",
        r"\bmedical(?:\s+allowance)?\b",
        r"\btelephone(?:\s+allowance)?\b",
        r"\bcommunication(?:\s+allowance)?\b",
        r"\bbooks(?:\s*&?\s*periodicals)?\b",
        r"\bvariable\s+pay\b",
        r"\bperformance\s+(?:pay|bonus|allowance)\b",
        r"\bstatutory\s+bonus\b",
        r"\bbonus\b",
        r"\bfuel(?:\s+allowance)?\b",
        r"\bchild\s+education(?:\s+allowance)?\b",
        r"\bmeal\s+allowance\b",
        r"\bfood\s+(?:coupon|card|allowance)\b",
        r"\bother\s+allowance(?:s)?\b",
        r"\bother\s+earnings\b",
        r"\buniform\s+allowance\b",
        r"\bdriver\s+salary\b",
        r"\bflexi(?:\s+benefit)?\b",
        r"\bshift\s+allowance\b",
        r"\bcity\s+compensatory\s+allowance\b",
        r"\bcca\b",
    ],
    "gross_pay": [
        r"\bgross\s+pay\b",
        r"\bgross\s+salary\b",
        r"\bgross\s+earnings\b",
        r"\btotal\s+earnings\b",
        r"\btotal\s+gross\b",
        r"\bgross\s+amount\b",
    ],
}

DEDUCTION_PATTERNS: Dict[str, List[str]] = {
    "employer_pf": [
        r"\bemployer\s+pf\b",
        r"\bemployer\s+epf\b",
        r"\bpf\s*\(employer\)\b",
        r"\bemployer(?:\s+contribution)?(?:\s+to)?\s+pf\b",
    ],
    "employee_pf": [
        r"\bemployee\s+pf\b",
        r"\bpf\s*\(employee\)\b",
        r"\bemployee(?:\s+contribution)?(?:\s+to)?\s+pf\b",
        r"\bprovident\s+fund\b",
        r"\bepf\b",
        r"\bpf\b",
    ],
    "professional_tax": [
        r"\bprofessional\s+tax\b",
        r"\bprof\.?\s*tax\b",
        r"\bp\.?\s*tax\b",
        r"\bpt\b",
    ],
    "tds": [
        r"\btax\s+deducted\s+at\s+source\b",
        r"\bincome\s+tax\b",
        r"\btds\b",
        r"\bit\s+deduction\b",
        r"\bit\s+tax\b",
        r"\bit\s*/\s*tds\b",
    ],
    "other_deductions": [
        r"\bvpf\b",
        r"\bvoluntary\s+pf\b",
        r"\besi\b",
        r"\besic\b",
        r"\blabour\s+welfare\s+fund\b",
        r"\blwf\b",
        r"\bgroup\s+insurance\b",
        r"\bhealth\s+insurance\b",
        r"\bmedical\s+insurance\b",
        r"\binsurance(?:\s+deduction)?\b",
        r"\bsalary\s+advance\b",
        r"\bloan(?:\s+recovery)?\b",
        r"\bother\s+deduction(?:s)?\b",
    ],
    "total_deductions": [
        r"\btotal\s+deductions?\b",
        r"\bgross\s+deductions?\b",
        r"\btotal\s+deduction\b",
    ],
}

NET_PAY_PATTERNS = [
    r"\bnet\s+pay\b",
    r"\bnet\s+salary\b",
    r"\btake\s+home(?:\s+pay)?\b",
    r"\bnet\s+payable\b",
    r"\bnet\s+amount\b",
]

METADATA_PATTERNS = {
    "employee_name": [
        r"(?:employee\s+name|emp\s+name|name\s+of\s+employee)\s*[:\-|]\s*([A-Za-z\s\.]+?)(?:\s*(?:\||\r?\n|$))",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:employee\s+id|emp\s+id)",
    ],
    "employee_id": [
        r"(?:employee\s+id|emp\s+id|emp\s+no|employee\s+code|emp\s+code)\s*[:\-|]\s*([A-Za-z0-9\-_]+)",
    ],
    "pan": [
        r"(?:pan|pan\s+no|pan\s+number)\s*[:\-|]\s*([A-Z]{5}[0-9]{4}[A-Z])",
    ],
    "uan": [
        r"(?:uan|uan\s+no|uan\s+number)\s*[:\-|]\s*([0-9]{12})",
    ],
    "bank_account_number": [
        r"(?:bank\s+a/c|a/c\s+no|account\s+number|bank\s+acc\s+no)\s*[:\-|]\s*([A-Za-z0-9\-]+)",
    ],
    "designation": [
        r"(?:designation|role|title)\s*[:\-|]\s*([A-Za-z0-9\s\.\-_/]+?)(?:\s*(?:\||\r?\n|$))",
        r"([A-Z][a-z]+(?:\s+[A-Za-z]+)+)\s+(?:department|dept)",
    ],
    "department": [
        r"(?:department|dept)\s*[:\-|]\s*([A-Za-z0-9\s\.\-_/]+?)(?:\s*(?:\||\r?\n|$))",
    ],
}


def classify_salary_label(label: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Classifies a label string into (category, field_name).
    Categories: 'earning', 'deduction', 'net_pay'.
    Returns (None, None) if unclassified.
    """
    norm = clean_header(label)
    if not norm:
        return None, None

    # 1. Net Pay
    for pat in NET_PAY_PATTERNS:
        if re.search(pat, norm):
            return "net_pay", "net_pay"

    # 2. Earnings - check Gross Pay first to avoid overlap
    for pat in EARNING_PATTERNS["gross_pay"]:
        if re.search(pat, norm):
            return "earning", "gross_pay"

    # 3. Deductions - check Employer PF before Employee PF
    for pat in DEDUCTION_PATTERNS["employer_pf"]:
        if re.search(pat, norm):
            return "deduction", "employer_pf"

    for pat in DEDUCTION_PATTERNS["total_deductions"]:
        if re.search(pat, norm):
            return "deduction", "total_deductions"

    for field in ["employee_pf", "professional_tax", "tds", "other_deductions"]:
        for pat in DEDUCTION_PATTERNS[field]:
            if re.search(pat, norm):
                return "deduction", field

    # 4. Earnings - specific fields
    for field in ["basic", "hra", "lta", "special_allowance", "other_allowances"]:
        for pat in EARNING_PATTERNS[field]:
            if re.search(pat, norm):
                return "earning", field

    return None, None


class DoclingSalarySlipParser:
    """
    Extractor for structured salary slips using Docling (Tasks 2.5 & 2.6).
    Extracts Basic, HRA, LTA, Special Allowance, Other Allowances, Gross Pay,
    Employer PF, Employee PF, Professional Tax, TDS, Total Deductions, and Net Pay,
    with arithmetic validation, confidence scoring, and review flagging.
    """

    def __init__(self, ocr_mode: Union[str, bool] = "auto"):
        self.ocr_mode = ocr_mode

        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True

        if ocr_mode is True or ocr_mode == "force":
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options = RapidOcrOptions(force_full_page_ocr=True)
        elif ocr_mode == "auto":
            pipeline_options.do_ocr = True
            pipeline_options.ocr_options = RapidOcrOptions()
        else:
            pipeline_options.do_ocr = False

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

    def parse(self, file_path: Union[str, Path]) -> SalarySlipParseResult:
        """Alias for extract() to provide consistent parser interface."""
        return self.extract(file_path)

    def extract(self, file_path: Union[str, Path]) -> SalarySlipParseResult:
        """Parses a salary slip PDF or image file into a SalarySlipParseResult."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Salary slip file not found: {path}")

        conv_res = self.converter.convert(path)
        doc = conv_res.document

        tables_data: List[pd.DataFrame] = []
        for table in doc.tables:
            try:
                df = table.export_to_dataframe(doc=doc)
                if not df.empty:
                    tables_data.append(df)
            except Exception:
                pass

        try:
            markdown_text = doc.export_to_markdown()
        except Exception:
            markdown_text = ""

        return self.extract_from_data(
            tables=tables_data,
            markdown_text=markdown_text,
            file_name=path.name,
            file_path=str(path),
        )

    def extract_from_data(
        self,
        tables: List[pd.DataFrame],
        markdown_text: str = "",
        file_name: str = "salary_slip.pdf",
        file_path: str = "",
    ) -> SalarySlipParseResult:
        """
        Extracts and normalizes salary components from pre-extracted table DataFrames
        and raw text/markdown.
        """
        result = SalarySlipParseResult(
            file_name=file_name,
            file_path=file_path,
        )

        combined_text = markdown_text

        # 1. Pay period extraction
        m, y, fy = extract_period_from_text(combined_text)
        if m and y and fy:
            result.month = m
            result.year = y
            result.financial_year = fy
        else:
            # Check table headers and cells for pay period
            for df in tables:
                col_text = " ".join([str(c) for c in df.columns])
                m_t, y_t, fy_t = extract_period_from_text(col_text)
                if m_t and y_t and fy_t:
                    result.month = m_t
                    result.year = y_t
                    result.financial_year = fy_t
                    break

        # 2. Metadata extraction from tables first, then regex fallback
        for df in tables:
            col_header_str = " ".join(str(c).lower() for c in df.columns)
            df_str = col_header_str + " " + df.to_string().lower()
            if any(k in df_str for k in ["employee name", "emp name", "designation", "pan", "uan"]):
                all_rows = [list(df.columns)] + df.values.tolist()
                for r in all_rows:
                    row_vals = [str(v).strip() for v in r if pd.notna(v) and str(v).strip() not in ("nan", "None", "")]
                    for idx, val in enumerate(row_vals):
                        val_lower = val.lower().rstrip(":")
                        if ("employee name" in val_lower or "emp name" in val_lower):
                            if idx + 1 < len(row_vals) and row_vals[idx + 1] and not result.raw_metadata.get("employee_name"):
                                result.raw_metadata["employee_name"] = row_vals[idx + 1]
                        elif ("employee id" in val_lower or "emp id" in val_lower):
                            if idx + 1 < len(row_vals) and row_vals[idx + 1] and not result.raw_metadata.get("employee_id"):
                                result.raw_metadata["employee_id"] = row_vals[idx + 1]
                        elif "designation" in val_lower:
                            if idx + 1 < len(row_vals) and row_vals[idx + 1] and not result.raw_metadata.get("designation"):
                                result.raw_metadata["designation"] = row_vals[idx + 1]
                        elif ("department" in val_lower or "dept" in val_lower):
                            if idx + 1 < len(row_vals) and row_vals[idx + 1] and not result.raw_metadata.get("department"):
                                result.raw_metadata["department"] = row_vals[idx + 1]
                        elif "pan" in val_lower:
                            if idx + 1 < len(row_vals) and row_vals[idx + 1] and not result.raw_metadata.get("pan"):
                                result.raw_metadata["pan"] = row_vals[idx + 1]
                        elif "uan" in val_lower:
                            if idx + 1 < len(row_vals) and row_vals[idx + 1] and not result.raw_metadata.get("uan"):
                                result.raw_metadata["uan"] = row_vals[idx + 1]
                        elif ("bank a/c" in val_lower or "account number" in val_lower):
                            if idx + 1 < len(row_vals) and row_vals[idx + 1] and not result.raw_metadata.get("bank_account_number"):
                                result.raw_metadata["bank_account_number"] = row_vals[idx + 1]

        for meta_key, patterns in METADATA_PATTERNS.items():
            if not result.raw_metadata.get(meta_key):
                for pat in patterns:
                    m_match = re.search(pat, combined_text, re.IGNORECASE)
                    if m_match:
                        val = m_match.group(1).strip()
                        val = re.sub(r"[|*\`]+$", "", val).strip()
                        if val:
                            result.raw_metadata[meta_key] = val
                            break

        # 3. Table data extraction
        earnings_dict: Dict[str, float] = {}
        deductions_dict: Dict[str, float] = {}
        other_allowances_sum: float = 0.0
        other_deductions_sum: float = 0.0

        for df in tables:
            df_str = df.to_string().lower()
            # If table is an employee metadata table without salary components, skip it for earnings/deductions
            if ("employee name" in df_str or "emp name" in df_str) and not any(
                w in df_str for w in ["basic", "gross", "deduction", "salary", "pay"]
            ):
                continue

            num_cols = len(df.columns)
            # Scenario A: 4 or more columns (e.g. Earnings, Amount, Deductions, Amount)
            if num_cols >= 4:
                for _, row in df.iterrows():
                    # Process Earnings pair (col 0, col 1)
                    earning_label = str(row.iloc[0]).strip()
                    earning_val = parse_numeric(row.iloc[1])
                    if earning_label and earning_val is not None:
                        cat, field = classify_salary_label(earning_label)
                        if field:
                            if field == "other_allowances":
                                other_allowances_sum += earning_val
                            elif field not in earnings_dict:
                                earnings_dict[field] = earning_val

                    # Process Deductions pair (col 2, col 3)
                    ded_label = str(row.iloc[2]).strip()
                    ded_val = parse_numeric(row.iloc[3])
                    if ded_label and ded_val is not None:
                        cat, field = classify_salary_label(ded_label)
                        if field:
                            if field == "other_deductions":
                                other_deductions_sum += ded_val
                            elif field not in deductions_dict:
                                deductions_dict[field] = ded_val

            # Scenario B: 2 or 3 columns (e.g. Component, Amount)
            elif num_cols >= 2:
                for _, row in df.iterrows():
                    label = str(row.iloc[0]).strip()
                    val = parse_numeric(row.iloc[1])
                    if not label or val is None:
                        # Try column 1 and 2 if column 0 is index/sl no
                        if num_cols >= 3:
                            label = str(row.iloc[1]).strip()
                            val = parse_numeric(row.iloc[2])

                    if label and val is not None:
                        cat, field = classify_salary_label(label)
                        if cat == "earning" and field:
                            if field == "other_allowances":
                                other_allowances_sum += val
                            elif field not in earnings_dict:
                                earnings_dict[field] = val
                        elif cat == "deduction" and field:
                            if field == "other_deductions":
                                other_deductions_sum += val
                            elif field not in deductions_dict:
                                deductions_dict[field] = val
                        elif cat == "net_pay" and result.net_pay == 0.0:
                            result.net_pay = val

        # 4. Text/Markdown line fallback for unextracted components (ignore lines that are table rows)
        for line in combined_text.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("|"):
                continue

            # Split line by colon, tab, or markdown pipes
            parts = [p.strip() for p in re.split(r"[:|=]", line_str) if p.strip()]
            if len(parts) >= 2:
                label_candidate = parts[0]
                val_candidate = parse_numeric(parts[-1])
                if val_candidate is not None and val_candidate > 0:
                    cat, field = classify_salary_label(label_candidate)
                    if cat == "earning" and field and field not in earnings_dict:
                        if field == "other_allowances":
                            if other_allowances_sum == 0.0:
                                other_allowances_sum = val_candidate
                        else:
                            earnings_dict[field] = val_candidate
                    elif cat == "deduction" and field and field not in deductions_dict:
                        if field == "other_deductions":
                            if other_deductions_sum == 0.0:
                                other_deductions_sum = val_candidate
                        else:
                            deductions_dict[field] = val_candidate
                    elif cat == "net_pay" and result.net_pay == 0.0:
                        result.net_pay = val_candidate

        # 5. Populate Result Fields
        result.basic = round(earnings_dict.get("basic", 0.0), 2)
        result.hra = round(earnings_dict.get("hra", 0.0), 2)
        result.lta = round(earnings_dict.get("lta", 0.0), 2)
        result.special_allowance = round(earnings_dict.get("special_allowance", 0.0), 2)
        result.other_allowances = round(
            other_allowances_sum if other_allowances_sum > 0.0 else earnings_dict.get("other_allowances", 0.0), 2
        )
        result.gross_pay = round(earnings_dict.get("gross_pay", 0.0), 2)

        result.employer_pf = round(deductions_dict.get("employer_pf", 0.0), 2)
        result.employee_pf = round(deductions_dict.get("employee_pf", 0.0), 2)
        result.professional_tax = round(deductions_dict.get("professional_tax", 0.0), 2)
        result.tds = round(deductions_dict.get("tds", 0.0), 2)
        result.other_deductions = round(
            other_deductions_sum if other_deductions_sum > 0.0 else deductions_dict.get("other_deductions", 0.0), 2
        )
        result.total_deductions = round(deductions_dict.get("total_deductions", 0.0), 2)

        if "net_pay" in earnings_dict and result.net_pay == 0.0:
            result.net_pay = round(earnings_dict["net_pay"], 2)
        elif "net_pay" in deductions_dict and result.net_pay == 0.0:
            result.net_pay = round(deductions_dict["net_pay"], 2)

        # 6. Gross Pay & Net Pay Arithmetic Validation Check (Task 2.6)
        result.calculated_gross = round(
            result.basic
            + result.hra
            + result.lta
            + result.special_allowance
            + result.other_allowances,
            2,
        )

        if result.gross_pay == 0.0 and result.calculated_gross > 0.0:
            # If gross pay wasn't explicitly stated as a separate line, infer it from components
            result.gross_pay = result.calculated_gross
            result.gross_discrepancy = 0.0
            result.is_gross_valid = True
        else:
            result.gross_discrepancy = round(
                abs(result.gross_pay - result.calculated_gross), 2
            )
            # Allow absolute tolerance (5.0 INR) or relative tolerance (1%)
            is_valid = (
                result.gross_discrepancy <= GROSS_TOLERANCE_ABSOLUTE
                or (
                    result.gross_pay > 0.0
                    and (result.gross_discrepancy / result.gross_pay)
                    <= GROSS_TOLERANCE_PERCENT
                )
            )
            result.is_gross_valid = is_valid
            if not is_valid:
                result.warnings.append(
                    f"Gross Pay validation failed: stated gross={result.gross_pay}, "
                    f"sum of components={result.calculated_gross} (diff={result.gross_discrepancy})"
                )

        # Deductions & Net Pay Reconcile
        calculated_ded = round(
            result.employee_pf
            + result.professional_tax
            + result.tds
            + result.other_deductions,
            2,
        )
        if result.total_deductions == 0.0 and calculated_ded > 0.0:
            result.total_deductions = calculated_ded

        result.calculated_net = round(
            result.gross_pay - result.total_deductions, 2
        )
        if result.net_pay == 0.0 and result.calculated_net > 0.0:
            result.net_pay = result.calculated_net

        # 7. Confidence Scoring & Review Flagging (Tasks 2.6 & 2.9)
        conf = 0.0
        if result.basic > 0.0:
            conf += 0.25
        if result.gross_pay > 0.0:
            conf += 0.25
        if result.net_pay > 0.0:
            conf += 0.20
        if result.is_gross_valid:
            conf += 0.15
        if (
            result.employee_pf > 0.0
            or result.professional_tax > 0.0
            or result.tds > 0.0
        ):
            conf += 0.10
        if result.month and result.year:
            conf += 0.05

        # Task 2.6 Gate: if gross validation fails, cap extraction confidence and flag review
        if not result.is_gross_valid:
            conf = min(conf, 0.55)

        result.extraction_confidence = round(min(conf, 1.0), 2)
        result.needs_review = (
            not result.is_gross_valid
            or result.extraction_confidence < DEFAULT_REVIEW_THRESHOLD
            or result.gross_pay <= 0.0
            or result.net_pay <= 0.0
        )

        return result
