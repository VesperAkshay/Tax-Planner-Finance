"""
Integrity and schema validation tests for Task 2.10 fixtures.
"""

import json
from pathlib import Path
import pytest

FIXTURES_DIR = Path("data/test_fixtures")

TEXT_PDF_FIXTURES = [
    "sample_hdfc_statement.pdf",
    "sample_icici_statement.pdf",
    "sample_sbi_statement.pdf",
]

SCANNED_PDF_FIXTURES = [
    "scanned_hdfc_statement.pdf",
    "scanned_icici_statement.pdf",
]

CSV_FIXTURES = [
    "sample_hdfc_statement.csv",
    "sample_kotak_statement.csv",
]

SALARY_SLIP_FIXTURES = [
    "sample_salary_slip.pdf",
    "sample_salary_slip_may.pdf",
    "sample_salary_slip_june.pdf",
]


def test_fixture_counts_satisfy_task_2_10_minimums():
    """Verify at least 3 text PDFs, 2 scanned PDFs, 2 CSVs, 3 salary slips exist."""
    assert len(TEXT_PDF_FIXTURES) >= 3
    assert len(SCANNED_PDF_FIXTURES) >= 2
    assert len(CSV_FIXTURES) >= 2
    assert len(SALARY_SLIP_FIXTURES) >= 3

    for name in TEXT_PDF_FIXTURES:
        p = FIXTURES_DIR / name
        assert p.exists() and p.stat().st_size > 0, f"Text PDF fixture missing or empty: {name}"

    for name in SCANNED_PDF_FIXTURES:
        p = FIXTURES_DIR / name
        assert p.exists() and p.stat().st_size > 0, f"Scanned PDF fixture missing or empty: {name}"

    for name in CSV_FIXTURES:
        p = FIXTURES_DIR / name
        assert p.exists() and p.stat().st_size > 0, f"CSV fixture missing or empty: {name}"

    for name in SALARY_SLIP_FIXTURES:
        p = FIXTURES_DIR / name
        assert p.exists() and p.stat().st_size > 0, f"Salary slip fixture missing or empty: {name}"


def test_bank_statement_expected_json_schemas_and_reconciliation():
    """Verify all bank statement expected JSON files exist and are mathematically consistent."""
    statement_fixtures = [
        ("sample_hdfc_statement.pdf", "sample_hdfc_statement.expected.json"),
        ("sample_icici_statement.pdf", "sample_icici_statement.expected.json"),
        ("sample_sbi_statement.pdf", "sample_sbi_statement.expected.json"),
        ("scanned_hdfc_statement.pdf", "scanned_hdfc_statement.expected.json"),
        ("scanned_icici_statement.pdf", "scanned_icici_statement.expected.json"),
        ("sample_hdfc_statement.csv", "sample_hdfc_statement.csv.expected.json"),
        ("sample_kotak_statement.csv", "sample_kotak_statement.csv.expected.json"),
    ]

    for data_file, expected_file in statement_fixtures:
        exp_path = FIXTURES_DIR / expected_file
        assert exp_path.exists(), f"Expected JSON missing: {expected_file}"

        data = json.loads(exp_path.read_text(encoding="utf-8"))
        assert data["fixture_type"] == "bank_statement"
        assert isinstance(data["bank_name"], str) and len(data["bank_name"]) > 0
        assert "opening_balance" in data and isinstance(data["opening_balance"], (int, float))
        assert "closing_balance" in data and isinstance(data["closing_balance"], (int, float))
        assert "total_credits" in data and isinstance(data["total_credits"], (int, float))
        assert "total_debits" in data and isinstance(data["total_debits"], (int, float))
        assert "rows" in data and isinstance(data["rows"], list) and len(data["rows"]) > 0
        assert len(data["rows"]) == data["total_rows"]

        # Mathematical consistency check
        expected_closing = round(data["opening_balance"] + data["total_credits"] - data["total_debits"], 2)
        assert abs(expected_closing - data["closing_balance"]) < 0.01, (
            f"Arithmetic inconsistency in {expected_file}: "
            f"Opening({data['opening_balance']}) + Cr({data['total_credits']}) - Dr({data['total_debits']}) = {expected_closing}, "
            f"but closing_balance={data['closing_balance']}"
        )

        # Row integrity check
        sum_credits = sum(r["amount"] for r in data["rows"] if r["transaction_type"] == "credit")
        sum_debits = sum(r["amount"] for r in data["rows"] if r["transaction_type"] == "debit")
        assert round(sum_credits, 2) == round(data["total_credits"], 2)
        assert round(sum_debits, 2) == round(data["total_debits"], 2)


def test_salary_slip_expected_json_schemas_and_arithmetic():
    """Verify all salary slip expected JSON files exist and have consistent gross pay arithmetic."""
    slip_fixtures = [
        ("sample_salary_slip.pdf", "sample_salary_slip.expected.json"),
        ("sample_salary_slip_may.pdf", "sample_salary_slip_may.expected.json"),
        ("sample_salary_slip_june.pdf", "sample_salary_slip_june.expected.json"),
    ]

    for data_file, expected_file in slip_fixtures:
        exp_path = FIXTURES_DIR / expected_file
        assert exp_path.exists(), f"Expected JSON missing: {expected_file}"

        data = json.loads(exp_path.read_text(encoding="utf-8"))
        assert data["fixture_type"] == "salary_slip"
        assert isinstance(data["employer_name"], str) and len(data["employer_name"]) > 0
        assert 1 <= data["month"] <= 12
        assert data["year"] >= 2024
        assert "-" in data["financial_year"]

        # Basic + HRA + LTA + Special <= Gross Pay
        allowance_sum = (
            data.get("basic_salary", 0.0)
            + data.get("hra", 0.0)
            + data.get("lta", 0.0)
            + data.get("special_allowance", 0.0)
        )
        assert allowance_sum <= data["gross_pay"] + 0.01

        # Net pay = Gross pay - total deductions
        deductions_sum = (
            data.get("employee_pf", 0.0)
            + data.get("professional_tax", 0.0)
            + data.get("tds", 0.0)
        )
        assert round(data["gross_pay"] - deductions_sum, 2) == round(data["net_pay"], 2)
