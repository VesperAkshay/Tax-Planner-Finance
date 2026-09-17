"""
Phase 14 Automated Validation Suite: Full Deduction Catalog & Extended Tax Engine (Tasks 14.1 - 14.9).

Validates:
- 14.8: Pure unit tests for every newly supported statutory section in the tax engine:
        80DD, 80DDB, 80E, 80EEA, 80G, 80GG, 80GGC, 80TTA, 80TTB, 80U, and 80CCD(2)
        against statutory reference calculations under Old Regime (and New Regime for 80CCD(2)).
- 14.9: Duplicate Protection: Adding or updating a catalog entry for a section already
        elicited or declared updates the existing record in-place rather than creating a duplicate.
- 14.4: Statutory Eligibility Check: Declaring an item with requires_eligibility_check=True
        without eligibility_confirmed=True is rejected with HTTP 400.
- 14.5: Live Cap Tracking: Catalog endpoint returns accurate remaining caps and usage percentages.
- 14.7: Completion Checkpoint: Tax report is_final is False until the user has viewed the catalog,
        and becomes True with report_status='final' once viewed.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.models  # Register all SQLModel models
from app.api.auth import create_access_token
from app.database import get_db_session
from app.db.seed_catalog import seed_deduction_catalog
from app.main import app
from app.models.deduction_catalog import DeductionCatalog
from app.models.elicitation_progress import ElicitationProgress, ElicitationStateEnum
from app.models.user import User
from app.models.user_declared_deduction import DeductionSource, DeductionStatus, UserDeclaredDeduction
from app.tax_engine.comparator import compare_regimes
from app.tax_engine.new_regime import compute_new_regime_tax
from app.tax_engine.old_regime import compute_old_regime_tax
from app.tax_engine.rules_loader import load_tax_rules


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture(scope="module")
def tax_rules():
    return load_tax_rules()


@pytest.fixture(name="db_engine")
def db_engine_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_deduction_catalog(session)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="client")
def client_fixture(db_engine):
    def get_test_session():
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(db_engine):
    with Session(db_engine) as session:
        user = User(
            email="catalog_tester@example.com",
            hashed_password="hashed_pw_test",
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# Task 14.8: Tax Engine Unit Tests for All Newly Supported Statutory Sections
# ==============================================================================


def test_14_8_section_80dd_disability_maintenance(tax_rules):
    """
    Section 80DD:
    - Normal disability (< 80%): fixed deduction ₹75,000
    - Severe disability (>= 80%): fixed deduction ₹1,25,000
    """
    gross = 1200000.0

    # Normal disability
    res_normal = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80dd": {"is_severe": False, "disability_percentage": 50}},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_normal["deductions_breakdown"]["section_80dd"]["allowed"] == 75000.0
    assert res_normal["taxable_income"] == gross - 75000.0

    # Severe disability
    res_severe = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80dd": {"is_severe": True, "disability_percentage": 85}},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_severe["deductions_breakdown"]["section_80dd"]["allowed"] == 125000.0
    assert res_severe["taxable_income"] == gross - 125000.0


def test_14_8_section_80ddb_specified_diseases(tax_rules):
    """
    Section 80DDB:
    - Non-senior citizen: max ₹40,000
    - Senior citizen: max ₹1,00,000
    """
    gross = 1000000.0

    # Non-senior claiming ₹60,000 -> capped at ₹40,000
    res_non_senior = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80ddb": {"amount": 60000.0, "is_senior_citizen": False}},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_non_senior["deductions_breakdown"]["section_80ddb"]["allowed"] == 40000.0

    # Senior citizen claiming ₹85,000 -> allowed ₹85,000 (cap is ₹1,00,000)
    res_senior = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80ddb": {"amount": 85000.0, "is_senior_citizen": True}},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_senior["deductions_breakdown"]["section_80ddb"]["allowed"] == 85000.0

    # Senior citizen claiming ₹1,20,000 -> capped at ₹1,00,000
    res_senior_capped = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80ddb": {"amount": 120000.0, "is_senior_citizen": True}},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_senior_capped["deductions_breakdown"]["section_80ddb"]["allowed"] == 100000.0


def test_14_8_section_80e_education_loan_interest(tax_rules):
    """
    Section 80E:
    - Entire interest on higher education loan is deductible (no statutory upper cap)
    """
    gross = 1500000.0
    interest_claimed = 180000.0

    res = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80e": interest_claimed},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res["deductions_breakdown"]["section_80e"]["allowed"] == interest_claimed
    assert res["taxable_income"] == gross - interest_claimed


def test_14_8_section_80eea_affordable_housing_interest(tax_rules):
    """
    Section 80EEA:
    - Interest on affordable housing loan: capped at ₹1,50,000
    """
    gross = 1200000.0

    # Claim below cap: ₹1,10,000 -> allowed ₹1,10,000
    res_below = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80eea": 110000.0},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_below["deductions_breakdown"]["section_80eea"]["allowed"] == 110000.0

    # Claim above cap: ₹1,90,000 -> capped at ₹1,50,000
    res_above = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80eea": 190000.0},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_above["deductions_breakdown"]["section_80eea"]["allowed"] == 150000.0


def test_14_8_section_80g_charitable_donations(tax_rules):
    """
    Section 80G:
    - Qualifying limit: 10% of adjusted gross income
    """
    gross = 1000000.0  # 10% qualifying cap is ₹1,00,000
    res = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80g": {"amount": 120000.0, "deduction_percentage": 100.0}},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res["deductions_breakdown"]["section_80g"]["allowed"] == 100000.0


def test_14_8_section_80gg_rent_paid_non_hra(tax_rules):
    """
    Section 80GG:
    - Least of:
      1. ₹60,000 (₹5,000/month)
      2. 25% of total income
      3. Rent paid minus 10% of total income
    """
    gross = 800000.0
    # Rent paid = ₹120,000 (₹10k/month).
    # 1. Cap = 60,000
    # 2. 25% of 800,000 = 200,000
    # 3. 120,000 - 10% of 800,000 (80,000) = 40,000
    # Minimum is 40,000
    res = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80gg": {"rent_paid": 120000.0, "total_income": gross}},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res["deductions_breakdown"]["section_80gg"]["allowed"] == 40000.0


def test_14_8_section_80ggc_political_contributions(tax_rules):
    """
    Section 80GGC:
    - 100% of contribution via non-cash banking channel, limited to gross income
    """
    gross = 1000000.0
    res = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80ggc": 50000.0},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res["deductions_breakdown"]["section_80ggc"]["allowed"] == 50000.0


def test_14_8_section_80tta_and_80ttb_interest_deductions(tax_rules):
    """
    Section 80TTA (non-senior): cap ₹10,000 on savings interest
    Section 80TTB (senior): cap ₹50,000 on savings + deposit interest
    """
    gross = 900000.0

    # 80TTA: Claim ₹14,000 -> capped at ₹10,000
    res_tta = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80tta": 14000.0},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_tta["deductions_breakdown"]["section_80tta"]["allowed"] == 10000.0

    # 80TTB: Claim ₹65,000 -> capped at ₹50,000
    res_ttb = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80ttb": 65000.0},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_ttb["deductions_breakdown"]["section_80ttb"]["allowed"] == 50000.0


def test_14_8_section_80u_self_disability(tax_rules):
    """
    Section 80U:
    - Normal disability (< 80%): fixed ₹75,000
    - Severe disability (>= 80%): fixed ₹1,25,000
    """
    gross = 1000000.0

    # Normal disability
    res_u_norm = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80u": {"is_severe": False}},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_u_norm["deductions_breakdown"]["section_80u"]["allowed"] == 75000.0

    # Severe disability
    res_u_sev = compute_old_regime_tax(
        gross_income=gross,
        deductions={"section_80u": {"is_severe": True}},
        rules=tax_rules,
        is_salaried=False,
    )
    assert res_u_sev["deductions_breakdown"]["section_80u"]["allowed"] == 125000.0


def test_14_8_section_80ccd_2_employer_nps_both_regimes(tax_rules):
    """
    Section 80CCD(2):
    - Non-government: 10% of salary
    - Government: 14% of salary
    - Eligible under BOTH Old Regime and New Regime (Section 115BAC)
    """
    gross = 1200000.0
    basic_salary = 600000.0
    employer_nps = 75000.0  # 10% of 600k = 60,000

    deductions = {
        "section_80ccd_2": {
            "amount": employer_nps,
            "basic_salary": basic_salary,
            "is_govt": False,
        }
    }

    # Old Regime
    old_res = compute_old_regime_tax(
        gross_income=gross,
        deductions=deductions,
        rules=tax_rules,
        is_salaried=True,
    )
    assert old_res["deductions_breakdown"]["section_80ccd_2"]["allowed"] == 60000.0

    # New Regime (Section 115BAC allows 80CCD(2))
    new_res = compute_new_regime_tax(
        gross_income=gross,
        rules=tax_rules,
        is_salaried=True,
        deductions=deductions,
    )
    # Standard deduction = 75,000, 80CCD(2) allowed = 60,000
    # Taxable income = 1,200,000 - 75,000 - 60,000 = 1,065,000
    assert new_res["taxable_income"] == 1065000.0


# ==============================================================================
# Task 14.4: Eligibility Check Enforcement
# ==============================================================================


def test_14_4_eligibility_check_enforcement(client, auth_headers):
    """
    Task 14.4: Declaring an item requiring eligibility check (e.g. 80G or 80EEA)
    without eligibility_confirmed=True must return HTTP 400 Bad Request.
    """
    # Attempt to declare 80G without confirming eligibility
    resp = client.post(
        "/api/v1/catalog/declare",
        headers=auth_headers,
        json={
            "section_code": "80G",
            "amount": 25000.0,
            "eligibility_confirmed": False,
        },
    )
    assert resp.status_code == 400
    assert "eligibility confirmation is required" in resp.json()["detail"].lower()

    # Declare with confirmation = True -> succeeds
    resp_ok = client.post(
        "/api/v1/catalog/declare",
        headers=auth_headers,
        json={
            "section_code": "80G",
            "amount": 25000.0,
            "eligibility_confirmed": True,
        },
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["success"] is True
    assert resp_ok.json()["amount"] == 25000.0


# ==============================================================================
# Task 14.9: Duplicate Protection / Edit Affordance
# ==============================================================================


def test_14_9_catalog_declare_duplicate_protection(client, auth_headers, db_engine):
    """
    Task 14.9: Assert that adding a catalog entry for a section already covered
    by the agent updates the existing record rather than creating a duplicate row.
    """
    # 1. Pre-seed a deduction for 80C as if elicited by the agent
    with Session(db_engine) as session:
        user = session.exec(select(User).where(User.email == "catalog_tester@example.com")).first()
        user_id = user.id
        pre_existing = UserDeclaredDeduction(
            user_id=user_id,
            financial_year="2025-2026",
            section="80C",
            amount=100000.0,
            source=DeductionSource.agent_elicited,
            status=DeductionStatus.declared,
        )
        session.add(pre_existing)
        session.commit()

    # 2. User edits/declares 80C through the catalog endpoint with a revised amount
    resp = client.post(
        "/api/v1/catalog/declare",
        headers=auth_headers,
        json={
            "section_code": "80C",
            "amount": 150000.0,
            "financial_year": "2025-2026",
            "eligibility_confirmed": False,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["amount"] == 150000.0

    # 3. Verify in the database that exactly ONE row exists for user_id and section="80C"
    with Session(db_engine) as session:
        records = session.exec(
            select(UserDeclaredDeduction)
            .where(UserDeclaredDeduction.user_id == user_id)
            .where(UserDeclaredDeduction.financial_year == "2025-2026")
            .where(UserDeclaredDeduction.section == "80C")
        ).all()
        assert len(records) == 1
        assert records[0].amount == 150000.0


# ==============================================================================
# Task 14.5: Live Cap Tracking
# ==============================================================================


def test_14_5_live_cap_tracking(client, auth_headers):
    """
    Task 14.5: Test that the catalog list endpoint returns accurate remaining cap
    and used percentage for sections.
    """
    # Declare ₹120,000 for 80C
    client.post(
        "/api/v1/catalog/declare",
        headers=auth_headers,
        json={
            "section_code": "80C",
            "amount": 120000.0,
            "financial_year": "2025-2026",
            "eligibility_confirmed": False,
        },
    )

    resp = client.get("/api/v1/catalog?financial_year=2025-2026&mark_viewed=false", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    sec_80c = next((s for s in data["sections"] if s["section_code"] == "80C"), None)
    assert sec_80c is not None
    assert sec_80c["declared_amount"] == 120000.0
    # Cap is ₹150,000; remaining cap should be ₹30,000 and used_percentage 80.0%
    assert sec_80c["remaining_cap"] == 30000.0
    assert sec_80c["used_percentage"] == 80.0


# ==============================================================================
# Task 14.7: Completion Checkpoint in Tax Report
# ==============================================================================


def test_14_7_tax_report_catalog_completion_checkpoint(client, db_engine):
    """
    Task 14.7: Tax report is_final is False until catalog is viewed,
    and becomes True once the user marks or views the catalog.
    """
    # Create fresh user who hasn't viewed catalog
    with Session(db_engine) as session:
        fresh_user = User(
            email="checkpoint_user@example.com",
            hashed_password="pw",
            is_active=True,
        )
        session.add(fresh_user)
        session.commit()
        session.refresh(fresh_user)
        fresh_token = create_access_token(data={"sub": str(fresh_user.id), "email": fresh_user.email})
    headers = {"Authorization": f"Bearer {fresh_token}"}

    # 1. Before viewing catalog: report is draft
    rep_1 = client.get("/api/v1/tax/comparison-report?gross_income=1200000", headers=headers)
    assert rep_1.status_code == 200
    data_1 = rep_1.json()
    assert data_1["catalog_viewed"] is False
    assert data_1["is_final"] is False
    assert data_1["report_status"] == "draft"

    # 2. Mark catalog viewed checkpoint
    view_resp = client.post("/api/v1/catalog/viewed", headers=headers)
    assert view_resp.status_code == 200
    assert view_resp.json()["catalog_viewed"] is True

    # 3. After viewing catalog: report is final
    rep_2 = client.get("/api/v1/tax/comparison-report?gross_income=1200000", headers=headers)
    assert rep_2.status_code == 200
    data_2 = rep_2.json()
    assert data_2["catalog_viewed"] is True
    assert data_2["is_final"] is True
    assert data_2["report_status"] == "final"
