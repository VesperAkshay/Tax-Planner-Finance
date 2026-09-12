"""
Automated full parsing pipeline evaluation runner (Task 2.11).

Evaluates DoclingPDFParser, CSVBankParser, and DoclingSalarySlipParser
against all 10 test fixtures and hand-verified ground truth in data/test_fixtures/.
Computes field-level accuracy and writes a comprehensive report to
backend/tests/parsing_accuracy_report.md.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pytest

from app.parsing.csv_parser import CSVBankParser
from app.parsing.pdf_parser import DoclingPDFParser
from app.parsing.salary_slip_parser import DoclingSalarySlipParser

FIXTURES_DIR = Path("data/test_fixtures")
REPORT_PATH = Path("backend/tests/parsing_accuracy_report.md")


def evaluate_statement_fixture(
    actual: Any, expected: Dict[str, Any]
) -> Tuple[float, int, int, List[str]]:
    """
    Computes field-level accuracy for a parsed bank statement.
    Returns (accuracy_pct, matched_points, total_points, details_list).
    """
    matched = 0
    total = 0
    details = []

    # 1. Total rows count
    total += 1
    if len(actual.rows) == expected["total_rows"]:
        matched += 1
        details.append(f"Row count matched ({len(actual.rows)}/{expected['total_rows']})")
    else:
        details.append(f"Row count mismatch: got {len(actual.rows)}, expected {expected['total_rows']}")

    # 2. Total credits
    total += 1
    if abs(actual.total_credits - expected["total_credits"]) < 1.0:
        matched += 1
        details.append(f"Total credits matched (₹{actual.total_credits:,.2f})")
    else:
        details.append(f"Total credits mismatch: got ₹{actual.total_credits}, expected ₹{expected['total_credits']}")

    # 3. Total debits
    total += 1
    if abs(actual.total_debits - expected["total_debits"]) < 1.0:
        matched += 1
        details.append(f"Total debits matched (₹{actual.total_debits:,.2f})")
    else:
        details.append(f"Total debits mismatch: got ₹{actual.total_debits}, expected ₹{expected['total_debits']}")

    # 4. Closing balance
    if "closing_balance" in expected and expected["closing_balance"] is not None:
        total += 1
        act_cb = actual.closing_balance if actual.closing_balance is not None else 0.0
        if abs(act_cb - expected["closing_balance"]) < 1.0:
            matched += 1
            details.append(f"Closing balance matched (₹{act_cb:,.2f})")
        else:
            details.append(f"Closing balance mismatch: got ₹{act_cb}, expected ₹{expected['closing_balance']}")

    # 5. Row-by-row matching
    for exp_row in expected["rows"]:
        exp_date = exp_row["date"]
        exp_amt = float(exp_row["amount"])
        exp_type = exp_row["transaction_type"]

        # Find best matching actual row
        candidate = None
        for act_row in actual.rows:
            if str(act_row.date) == exp_date and abs(act_row.amount - exp_amt) < 1.0:
                candidate = act_row
                break

        # Check date + amount
        total += 1
        if candidate is not None:
            matched += 1
            # Check transaction type
            total += 1
            if candidate.transaction_type == exp_type:
                matched += 1
            else:
                details.append(f"Row type mismatch on {exp_date}: got {candidate.transaction_type}, expected {exp_type}")

            # Check narration / description presence
            total += 1
            if candidate.description and len(candidate.description) > 0:
                matched += 1
            else:
                details.append(f"Missing description on {exp_date}")
        else:
            total += 2  # account for type and description
            details.append(f"Missing transaction on {exp_date} for amount ₹{exp_amt}")

    accuracy_pct = round((matched / total) * 100.0, 2) if total > 0 else 0.0
    return accuracy_pct, matched, total, details


def evaluate_salary_slip_fixture(
    actual: Any, expected: Dict[str, Any]
) -> Tuple[float, int, int, List[str]]:
    """
    Computes field-level accuracy for a parsed salary slip.
    Returns (accuracy_pct, matched_points, total_points, details_list).
    """
    matched = 0
    total = 0
    details = []

    fields_to_check = [
        ("month", int),
        ("year", int),
        ("financial_year", str),
        ("basic_salary", float),
        ("hra", float),
        ("lta", float),
        ("special_allowance", float),
        ("gross_pay", float),
        ("employer_pf", float),
        ("employee_pf", float),
        ("professional_tax", float),
        ("tds", float),
        ("net_pay", float),
    ]

    for field_name, f_type in fields_to_check:
        if field_name not in expected:
            continue
        total += 1
        exp_val = expected[field_name]
        act_val = getattr(actual, field_name if field_name != "basic_salary" else "basic", None)

        if act_val is None:
            details.append(f"Field {field_name} is None (expected {exp_val})")
            continue

        if f_type is float:
            if abs(float(act_val) - float(exp_val)) < 1.0:
                matched += 1
                details.append(f"{field_name} matched (₹{act_val:,.2f})")
            else:
                details.append(f"{field_name} mismatch: got ₹{act_val}, expected ₹{exp_val}")
        elif f_type is int:
            if int(act_val) == int(exp_val):
                matched += 1
                details.append(f"{field_name} matched ({act_val})")
            else:
                details.append(f"{field_name} mismatch: got {act_val}, expected {exp_val}")
        else:
            if str(act_val).strip() == str(exp_val).strip():
                matched += 1
                details.append(f"{field_name} matched ('{act_val}')")
            else:
                details.append(f"{field_name} mismatch: got '{act_val}', expected '{exp_val}'")

    accuracy_pct = round((matched / total) * 100.0, 2) if total > 0 else 0.0
    return accuracy_pct, matched, total, details


def generate_markdown_report(eval_results: List[Dict[str, Any]]) -> str:
    """Formats the evaluation results into a detailed Markdown report."""
    md = []
    md.append("# Document Parsing Pipeline Accuracy Report (Task 2.11 & Gate 2.12)\n")
    md.append("**Evaluation Date**: Automated Test Suite Execution\n")
    md.append("**Scope**: All test fixtures in `data/test_fixtures/` evaluated against hand-verified `.expected.json` ground truths.\n")

    # Aggregate summaries
    categories = {
        "Text PDF Bank Statements": [r for r in eval_results if r["category"] == "text_pdf"],
        "Scanned PDF Bank Statements (OCR)": [r for r in eval_results if r["category"] == "scanned_pdf"],
        "CSV Bank Statements": [r for r in eval_results if r["category"] == "csv"],
        "Salary Slips": [r for r in eval_results if r["category"] == "salary_slip"],
    }

    total_matched = sum(r["matched"] for r in eval_results)
    total_points = sum(r["total"] for r in eval_results)
    overall_accuracy = round((total_matched / total_points) * 100.0, 2) if total_points > 0 else 0.0

    md.append("## Executive Summary & Gate Evaluation\n")
    md.append("| Category | Fixtures | Fields Tested | Matched | Accuracy | Gate Requirement | Gate Status |")
    md.append("|---|---|---|---|---|---|---|")

    text_csv_matched = 0
    text_csv_total = 0

    for cat_name, items in categories.items():
        cat_m = sum(i["matched"] for i in items)
        cat_t = sum(i["total"] for i in items)
        cat_acc = round((cat_m / cat_t) * 100.0, 2) if cat_t > 0 else 0.0

        if cat_name in ("Text PDF Bank Statements", "CSV Bank Statements"):
            text_csv_matched += cat_m
            text_csv_total += cat_t
            req = "> 90.0%"
            status = "PASSED" if cat_acc >= 90.0 else "FAILED"
        elif cat_name == "Scanned PDF Bank Statements (OCR)":
            req = "> 75.0%"
            status = "PASSED" if cat_acc >= 75.0 else "FAILED"
        else:
            req = "> 85.0%"
            status = "PASSED" if cat_acc >= 85.0 else "FAILED"

        status_badge = f"**{status}**" if status == "PASSED" else f"<span style='color:red;'>**{status}**</span>"
        md.append(f"| {cat_name} | {len(items)} | {cat_t} | {cat_m} | **{cat_acc:.2f}%** | {req} | {status_badge} |")

    combined_text_csv_acc = round((text_csv_matched / text_csv_total) * 100.0, 2) if text_csv_total > 0 else 0.0
    scanned_items = categories["Scanned PDF Bank Statements (OCR)"]
    scanned_m = sum(i["matched"] for i in scanned_items)
    scanned_t = sum(i["total"] for i in scanned_items)
    scanned_acc = round((scanned_m / scanned_t) * 100.0, 2) if scanned_t > 0 else 0.0

    gate_passed = combined_text_csv_acc >= 90.0 and scanned_acc >= 75.0
    gate_verdict = "PASSED" if gate_passed else "FAILED"

    md.append(f"\n**Combined Text/CSV Accuracy**: **{combined_text_csv_acc:.2f}%** (Gate: > 90.0%)\n")
    md.append(f"**Scanned PDF (OCR) Accuracy**: **{scanned_acc:.2f}%** (Gate: > 75.0%)\n")
    md.append(f"**Overall Pipeline Accuracy**: **{overall_accuracy:.2f}%**\n")
    md.append(f"**Phase 2 Gate Verdict**: **{gate_verdict}**\n\n---\n")

    # Detailed Per-Fixture Breakdown
    md.append("## Per-Fixture Detailed Breakdown\n")
    md.append("| # | Fixture File | Type / Bank / Employer | Matched / Total | Accuracy | Status |")
    md.append("|---|---|---|---|---|---|")

    for idx, r in enumerate(eval_results, 1):
        status = "PASSED" if r["accuracy"] >= 75.0 else "FAILED"
        md.append(f"| {idx} | `{r['file_name']}` | {r['details_label']} | {r['matched']}/{r['total']} | **{r['accuracy']:.2f}%** | {status} |")

    md.append("\n---\n")
    md.append("## Field-Level Extraction Observations\n")
    for r in eval_results:
        md.append(f"### `{r['file_name']}` ({r['accuracy']:.2f}% accuracy)")
        md.append(f"- **Category**: {r['category']}")
        md.append(f"- **Fields Evaluated**: {r['matched']} / {r['total']}")
        md.append("- **Verification Notes**:")
        for note in r["details"][:6]:
            md.append(f"  - {note}")
        if len(r["details"]) > 6:
            md.append(f"  - ... ({len(r['details']) - 6} additional fields verified)")
        md.append("")

    return "\n".join(md)


def test_full_parsing_pipeline_evaluation():
    """
    Task 2.11 automated evaluation test:
    Executes DoclingPDFParser, CSVBankParser, and DoclingSalarySlipParser
    against all 10 fixtures, validates accuracy against Task 2.12 gate criteria,
    and writes backend/tests/parsing_accuracy_report.md.
    """
    fixtures_config = [
        # Text Bank Statement PDFs (3)
        {
            "file": "sample_hdfc_statement.pdf",
            "expected": "sample_hdfc_statement.expected.json",
            "category": "text_pdf",
            "label": "HDFC Bank (Text PDF)",
        },
        {
            "file": "sample_icici_statement.pdf",
            "expected": "sample_icici_statement.expected.json",
            "category": "text_pdf",
            "label": "ICICI Bank (Text PDF)",
        },
        {
            "file": "sample_sbi_statement.pdf",
            "expected": "sample_sbi_statement.expected.json",
            "category": "text_pdf",
            "label": "SBI (Text PDF)",
        },
        # Scanned Bank Statement PDFs (2)
        {
            "file": "scanned_hdfc_statement.pdf",
            "expected": "scanned_hdfc_statement.expected.json",
            "category": "scanned_pdf",
            "label": "HDFC Bank (Scanned OCR PDF)",
        },
        {
            "file": "scanned_icici_statement.pdf",
            "expected": "scanned_icici_statement.expected.json",
            "category": "scanned_pdf",
            "label": "ICICI Bank (Scanned OCR PDF)",
        },
        # CSV Bank Statements (2)
        {
            "file": "sample_hdfc_statement.csv",
            "expected": "sample_hdfc_statement.csv.expected.json",
            "category": "csv",
            "label": "HDFC Bank (Separate Columns CSV)",
        },
        {
            "file": "sample_kotak_statement.csv",
            "expected": "sample_kotak_statement.csv.expected.json",
            "category": "csv",
            "label": "Kotak Mahindra Bank (Type Indicator CSV)",
        },
        # Salary Slips (3)
        {
            "file": "sample_salary_slip.pdf",
            "expected": "sample_salary_slip.expected.json",
            "category": "salary_slip",
            "label": "Acme Tech Solutions (April 2024)",
        },
        {
            "file": "sample_salary_slip_may.pdf",
            "expected": "sample_salary_slip_may.expected.json",
            "category": "salary_slip",
            "label": "Infosys Technologies (May 2025)",
        },
        {
            "file": "sample_salary_slip_june.pdf",
            "expected": "sample_salary_slip_june.expected.json",
            "category": "salary_slip",
            "label": "TCS (June 2025)",
        },
    ]

    text_pdf_parser = DoclingPDFParser()
    scanned_pdf_parser = DoclingPDFParser(ocr_mode="force_ocr")
    csv_parser = CSVBankParser()
    salary_slip_parser = DoclingSalarySlipParser()

    eval_results = []

    for cfg in fixtures_config:
        file_path = FIXTURES_DIR / cfg["file"]
        exp_path = FIXTURES_DIR / cfg["expected"]

        assert file_path.exists(), f"Fixture missing: {file_path}"
        assert exp_path.exists(), f"Expected output missing: {exp_path}"

        expected_data = json.loads(exp_path.read_text(encoding="utf-8"))

        if cfg["category"] == "text_pdf":
            parsed = text_pdf_parser.parse(file_path)
            acc, matched, total, details = evaluate_statement_fixture(parsed, expected_data)
        elif cfg["category"] == "scanned_pdf":
            parsed = scanned_pdf_parser.parse(file_path)
            acc, matched, total, details = evaluate_statement_fixture(parsed, expected_data)
        elif cfg["category"] == "csv":
            parsed = csv_parser.parse(file_path)
            acc, matched, total, details = evaluate_statement_fixture(parsed, expected_data)
        elif cfg["category"] == "salary_slip":
            parsed = salary_slip_parser.parse(file_path)
            acc, matched, total, details = evaluate_salary_slip_fixture(parsed, expected_data)
        else:
            raise ValueError(f"Unknown category: {cfg['category']}")

        eval_results.append(
            {
                "file_name": cfg["file"],
                "category": cfg["category"],
                "details_label": cfg["label"],
                "accuracy": acc,
                "matched": matched,
                "total": total,
                "details": details,
            }
        )

    # Generate Markdown Report
    report_content = generate_markdown_report(eval_results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_content, encoding="utf-8")

    # Aggregate metric calculations
    text_results = [r for r in eval_results if r["category"] == "text_pdf"]
    scanned_results = [r for r in eval_results if r["category"] == "scanned_pdf"]
    csv_results = [r for r in eval_results if r["category"] == "csv"]
    salary_results = [r for r in eval_results if r["category"] == "salary_slip"]

    text_acc = (sum(r["matched"] for r in text_results) / sum(r["total"] for r in text_results)) * 100.0
    csv_acc = (sum(r["matched"] for r in csv_results) / sum(r["total"] for r in csv_results)) * 100.0
    scanned_acc = (sum(r["matched"] for r in scanned_results) / sum(r["total"] for r in scanned_results)) * 100.0
    salary_acc = (sum(r["matched"] for r in salary_results) / sum(r["total"] for r in salary_results)) * 100.0

    combined_text_csv_acc = (
        (sum(r["matched"] for r in text_results) + sum(r["matched"] for r in csv_results))
        / (sum(r["total"] for r in text_results) + sum(r["total"] for r in csv_results))
    ) * 100.0

    # Task 2.12 Gate Assertions
    assert combined_text_csv_acc >= 90.0, (
        f"Gate 2.12 Failed: Text & CSV statement accuracy must be > 90%, got {combined_text_csv_acc:.2f}%"
    )
    assert text_acc >= 90.0, f"Text PDF accuracy must be > 90%, got {text_acc:.2f}%"
    assert csv_acc >= 90.0, f"CSV accuracy must be > 90%, got {csv_acc:.2f}%"
    assert scanned_acc >= 75.0, (
        f"Gate 2.12 Failed: Scanned PDF accuracy must be > 75%, got {scanned_acc:.2f}%"
    )
    assert salary_acc >= 85.0, f"Salary slip accuracy must be > 85%, got {salary_acc:.2f}%"
