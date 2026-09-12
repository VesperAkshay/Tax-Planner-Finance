import pytest
from pydantic import ValidationError
from sqlmodel import SQLModel

from app.models.reconciliation_flag import (
    ReconciliationFlag,
    ReconciliationFlagCreate,
    ReconciliationFlagResolve,
)
from app.models.salary_slip import SalarySlip, SalarySlipCreate


def test_metadata_registration():
    """Verify salary_slips and reconciliation_flags are registered in SQLModel metadata."""
    assert "salary_slips" in SQLModel.metadata.tables
    assert "reconciliation_flags" in SQLModel.metadata.tables


def test_salary_slip_instantiation_and_components():
    """Verify all earnings and deduction fields on SalarySlip."""
    slip = SalarySlip(
        user_id=1,
        file_name="salary_june_2025.pdf",
        file_path="/storage/slips/june_2025.pdf",
        month=6,
        year=2025,
        financial_year="2025-2026",
        basic=60000.0,
        hra=30000.0,
        lta=5000.0,
        special_allowance=25000.0,
        gross_pay=120000.0,
        employee_pf=7200.0,
        employer_pf=7200.0,
        professional_tax=200.0,
        tds=10000.0,
        total_deductions=17400.0,
        net_pay=102600.0,
        extraction_confidence=0.98,
        is_gross_valid=True,
        needs_review=False,
    )
    assert slip.gross_pay == 120000.0
    assert slip.basic == 60000.0
    assert slip.hra == 30000.0
    assert slip.lta == 5000.0
    assert slip.special_allowance == 25000.0
    assert slip.employee_pf == 7200.0
    assert slip.employer_pf == 7200.0
    assert slip.professional_tax == 200.0
    assert slip.tds == 10000.0
    assert slip.net_pay == 102600.0
    assert slip.extraction_confidence == 0.98


def test_reconciliation_flag_fields_and_status():
    """Verify ReconciliationFlag fields, default pending status, and resolution validation."""
    flag = ReconciliationFlag(
        user_id=1,
        salary_slip_id=10,
        transaction_id=25,
        month=6,
        year=2025,
        flag_type="mismatched_amount",
        expected_amount=102600.0,
        actual_amount=100000.0,
        difference=2600.0,
        status="pending",
    )
    assert flag.status == "pending"
    assert flag.difference == 2600.0

    # Test resolution validation
    resolve_valid = ReconciliationFlagResolve(status="resolved", user_note="Difference resolved manually")
    assert resolve_valid.status == "resolved"

    with pytest.raises(ValidationError):
        ReconciliationFlagResolve(status="invalid_status", user_note="Test note")

    with pytest.raises(ValidationError):
        ReconciliationFlagResolve(status="resolved", user_note="")  # empty note not allowed
