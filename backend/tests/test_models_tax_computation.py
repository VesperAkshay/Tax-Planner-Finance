import pytest
from sqlmodel import SQLModel

from app.models.tax_computation import TaxComputation, TaxComputationCreate
from app.models.tax_rule_version import TaxRuleVersion, TaxRuleVersionCreate
from app.models.user_declared_deduction import (
    UserDeclaredDeduction,
    UserDeclaredDeductionCreate,
)


def test_metadata_tables():
    """Verify all 3 tax and deduction tables are in SQLModel metadata."""
    assert "user_declared_deductions" in SQLModel.metadata.tables
    assert "tax_rule_versions" in SQLModel.metadata.tables
    assert "tax_computations" in SQLModel.metadata.tables


def test_user_declared_deduction_fields():
    """Verify UserDeclaredDeduction model instantiation and fields."""
    ded = UserDeclaredDeduction(
        user_id=1,
        financial_year="2025-2026",
        section="80CCD(1B)",
        amount=50000.0,
        source="agent_elicited",
        metadata_json={"nps_tier": "Tier-1", "pran": "123456789"},
    )
    assert ded.user_id == 1
    assert ded.section == "80CCD(1B)"
    assert ded.amount == 50000.0
    assert ded.source == "agent_elicited"
    assert ded.metadata_json["nps_tier"] == "Tier-1"


def test_tax_rule_version_fields():
    """Verify TaxRuleVersion model with JSON rules payload."""
    rule_ver = TaxRuleVersion(
        financial_year="2025-2026",
        version_tag="v1.0",
        is_active=True,
        rules={
            "new_regime": {"standard_deduction": 75000, "rebate_87a_limit": 60000},
            "old_regime": {"standard_deduction": 50000, "rebate_87a_limit": 12500},
        },
    )
    assert rule_ver.financial_year == "2025-2026"
    assert rule_ver.is_active is True
    assert rule_ver.rules["new_regime"]["standard_deduction"] == 75000


def test_tax_computation_fields():
    """Verify TaxComputation model liability fields and recommendation."""
    comp = TaxComputation(
        user_id=2,
        financial_year="2025-2026",
        gross_income=1200000.0,
        old_regime_taxable_income=950000.0,
        old_regime_tax=102500.0,
        old_regime_cess=4100.0,
        old_regime_total_liability=106600.0,
        new_regime_taxable_income=1125000.0,
        new_regime_tax=62500.0,
        new_regime_cess=2500.0,
        new_regime_total_liability=65000.0,
        recommended_regime="new",
        tax_savings=41600.0,
    )
    assert comp.gross_income == 1200000.0
    assert comp.recommended_regime == "new"
    assert comp.tax_savings == 41600.0
    assert comp.old_regime_total_liability > comp.new_regime_total_liability
