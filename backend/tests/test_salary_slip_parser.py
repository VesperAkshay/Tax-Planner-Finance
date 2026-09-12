from pathlib import Path
import pandas as pd
import pytest

from app.parsing.salary_slip_parser import (
    DoclingSalarySlipParser,
    calculate_financial_year,
    classify_salary_label,
    extract_period_from_text,
)
from app.parsing.schemas import SalarySlipParseResult


def test_period_and_fy_calculation():
    # April 2024 -> FY 2024-2025
    m, y, fy = extract_period_from_text("Payslip for the month of April 2024")
    assert m == 4
    assert y == 2024
    assert fy == "2024-2025"

    # March 2025 -> FY 2024-2025
    m, y, fy = extract_period_from_text("Salary Slip for March 2025")
    assert m == 3
    assert y == 2025
    assert fy == "2024-2025"

    # May 2025 -> FY 2025-2026
    m, y, fy = extract_period_from_text("Payslip: 05/2025")
    assert m == 5
    assert y == 2025
    assert fy == "2025-2026"


def test_salary_label_classification():
    assert classify_salary_label("Basic Salary") == ("earning", "basic")
    assert classify_salary_label("House Rent Allowance") == ("earning", "hra")
    assert classify_salary_label("HRA") == ("earning", "hra")
    assert classify_salary_label("Leave Travel Allowance") == ("earning", "lta")
    assert classify_salary_label("Special Allowance") == ("earning", "special_allowance")
    assert classify_salary_label("Conveyance Allowance") == ("earning", "other_allowances")
    assert classify_salary_label("Total Gross Pay") == ("earning", "gross_pay")
    assert classify_salary_label("Gross Earnings") == ("earning", "gross_pay")

    assert classify_salary_label("Employer PF") == ("deduction", "employer_pf")
    assert classify_salary_label("Provident Fund (PF)") == ("deduction", "employee_pf")
    assert classify_salary_label("Professional Tax") == ("deduction", "professional_tax")
    assert classify_salary_label("PT") == ("deduction", "professional_tax")
    assert classify_salary_label("Income Tax (TDS)") == ("deduction", "tds")
    assert classify_salary_label("Total Deductions") == ("deduction", "total_deductions")

    assert classify_salary_label("Net Pay") == ("net_pay", "net_pay")
    assert classify_salary_label("Take Home Pay") == ("net_pay", "net_pay")


def test_gross_pay_validation_and_tolerance():
    parser = DoclingSalarySlipParser(ocr_mode=False)

    # 1. Matching Gross Pay
    df_valid = pd.DataFrame({
        "Earnings": ["Basic", "HRA", "LTA", "Special Allowance", "Gross Pay"],
        "Amount1": [50000, 20000, 5000, 15000, 90000],
        "Deductions": ["PF", "PT", "TDS", "Total Deductions", "Net Pay"],
        "Amount2": [6000, 200, 8000, 14200, 75800],
    })
    res_valid = parser.extract_from_data(
        tables=[df_valid],
        markdown_text="Payslip for April 2024",
    )
    assert res_valid.is_gross_valid is True
    assert res_valid.gross_discrepancy == 0.0
    assert res_valid.extraction_confidence >= 0.85
    assert res_valid.needs_review is False

    # 2. Within Small Tolerance (< 5 INR)
    df_tol = pd.DataFrame({
        "Earnings": ["Basic", "HRA", "Special Allowance", "Gross Pay"],
        "Amount1": [50000, 20000, 15002, 85000],  # 2 INR diff
        "Deductions": ["PF", "PT", "TDS", "Net Pay"],
        "Amount2": [6000, 200, 8000, 70800],
    })
    res_tol = parser.extract_from_data(
        tables=[df_tol],
        markdown_text="Payslip for April 2024",
    )
    assert res_tol.is_gross_valid is True
    assert res_tol.gross_discrepancy == 2.0
    assert res_tol.needs_review is False

    # 3. Discrepant Gross Pay (Task 2.6 Gate)
    df_invalid = pd.DataFrame({
        "Earnings": ["Basic", "HRA", "Special Allowance", "Gross Pay"],
        "Amount1": [50000, 20000, 15000, 120000],  # Stated 120,000 vs Sum 85,000
        "Deductions": ["PF", "PT", "TDS", "Net Pay"],
        "Amount2": [6000, 200, 8000, 105800],
    })
    res_invalid = parser.extract_from_data(
        tables=[df_invalid],
        markdown_text="Payslip for April 2024",
    )
    assert res_invalid.is_gross_valid is False
    assert res_invalid.gross_discrepancy == 35000.0
    assert res_invalid.extraction_confidence <= 0.60
    assert res_invalid.needs_review is True
    assert any("Gross Pay validation failed" in w for w in res_invalid.warnings)


def test_salary_slip_db_dict():
    res = SalarySlipParseResult(
        file_name="test_slip.pdf",
        file_path="/path/test_slip.pdf",
        month=4,
        year=2024,
        financial_year="2024-2025",
        basic=50000.0,
        hra=20000.0,
        gross_pay=70000.0,
        employee_pf=6000.0,
        total_deductions=6000.0,
        net_pay=64000.0,
        extraction_confidence=0.95,
        is_gross_valid=True,
        needs_review=False,
    )
    db_dict = res.to_dict_for_db(user_id=42)
    assert db_dict["user_id"] == 42
    assert db_dict["basic"] == 50000.0
    assert db_dict["month"] == 4
    assert db_dict["financial_year"] == "2024-2025"
    assert db_dict["net_pay"] == 64000.0
    assert db_dict["is_gross_valid"] is True


def test_extract_from_stacked_tables():
    parser = DoclingSalarySlipParser(ocr_mode=False)

    df_earnings = pd.DataFrame({
        "Component": ["Basic", "HRA", "LTA", "Special Allowance", "Conveyance", "Total Earnings"],
        "Amount": ["60,000.00", "24,000.00", "5,000.00", "16,000.00", "5,000.00", "1,10,000.00"],
    })
    df_deductions = pd.DataFrame({
        "Component": ["EPF", "Professional Tax", "TDS", "Total Deductions"],
        "Amount": ["7,200.00", "200.00", "10,000.00", "17,400.00"],
    })

    res = parser.extract_from_data(
        tables=[df_earnings, df_deductions],
        markdown_text="""Acme Technologies
Payslip for the month of May 2024
Net Salary: 92,600.00
Employee ID: ACM-998
PAN: PQRST9988Z
""",
    )
    assert res.basic == 60000.0
    assert res.hra == 24000.0
    assert res.lta == 5000.0
    assert res.special_allowance == 16000.0
    assert res.other_allowances == 5000.0
    assert res.gross_pay == 110000.0
    assert res.employee_pf == 7200.0
    assert res.professional_tax == 200.0
    assert res.tds == 10000.0
    assert res.total_deductions == 17400.0
    assert res.net_pay == 92600.0
    assert res.is_gross_valid is True
    assert res.month == 5
    assert res.year == 2024
    assert res.financial_year == "2024-2025"
    assert res.raw_metadata.get("employee_id") == "ACM-998"
    assert res.raw_metadata.get("pan") == "PQRST9988Z"


def test_docling_end_to_end_on_salary_slip_pdf():
    pdf_path = Path(__file__).resolve().parent.parent.parent / "data" / "test_fixtures" / "sample_salary_slip.pdf"
    assert pdf_path.exists(), f"Missing fixture: {pdf_path}"

    parser = DoclingSalarySlipParser(ocr_mode=False)
    result = parser.extract(pdf_path)

    # Component checks
    assert result.basic == 65000.00
    assert result.hra == 26000.00
    assert result.lta == 5000.00
    assert result.special_allowance == 20000.00
    assert result.other_allowances == 4000.00
    assert result.gross_pay == 120000.00

    assert result.employee_pf == 7800.00
    assert result.employer_pf == 7800.00
    assert result.professional_tax == 200.00
    assert result.tds == 12000.00
    assert result.net_pay == 100000.00

    # Validation checks
    assert result.is_gross_valid is True
    assert result.gross_discrepancy == 0.0
    assert result.month == 4
    assert result.year == 2024
    assert result.financial_year == "2024-2025"
    assert result.extraction_confidence >= 0.85
    assert result.needs_review is False

    # Metadata checks
    assert "Rahul Sharma" in result.raw_metadata.get("employee_name", "")
    assert "ACM-10492" in result.raw_metadata.get("employee_id", "")
    assert "ABCDE1234F" in result.raw_metadata.get("pan", "")
