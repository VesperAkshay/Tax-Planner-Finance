"""
Tests for Career Switch & Offer Letter Decoder Engine (switch_engine.py and API).
Verifies:
1. CTC Offer decoding into guaranteed monthly in-hand vs at-risk pay.
2. Hidden trap detection (Gratuity lock-in, special allowance tax penalty, variable at risk, clawback).
3. Mid-year switch double-deduction and slab cliff trap (the surprise July tax demand).
4. Section 234B and 234C interest calculation.
5. Form 12B statement generation.
6. API endpoint integration.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models
from app.career_switch.switch_engine import (
    compare_two_offers,
    decode_offer_ctc,
    simulate_midyear_switch,
)
from app.database import get_db_session
from app.main import app
from app.seed_categories import seed_categories_sync
from app.tax_engine.rules_loader import load_tax_rules


@pytest.fixture(scope="module")
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_categories_sync(session)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="module")
def client(test_db):
    def get_test_session():
        with Session(test_db) as session:
            yield session

    app.dependency_overrides[get_db_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def auth_headers(client):
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "switch_tester@example.com",
            "password": "ValidPassword123!",
            "full_name": "Switch Tester",
            "pan": "ABCDE1234F",
        },
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_decode_offer_ctc_standard():
    rules = load_tax_rules()
    res = decode_offer_ctc(
        ctc=2400000,  # 24 LPA
        variable_pay=200000,
        joining_bonus=100000,
        bonus_clawback_months=18,
        rules=rules,
    )

    assert res["annual_ctc"] == 2400000
    components = res["components"]
    # Basic = 40% of 24L = 9.6L
    assert components["basic"] == 960000
    # Gratuity ~ 4.81% of basic
    assert components["gratuity_annual"] > 40000
    # Employer PF = 12% of basic
    assert components["employer_pf_annual"] == 115200

    monthly = res["monthly_breakdown"]
    assert monthly["guaranteed_in_hand"] > 0
    assert monthly["monthly_tds_tax"] > 0

    # Traps check
    trap_codes = [t["code"] for t in res["traps_detected"]]
    assert "GRATUITY_LOCK" in trap_codes
    assert "VARIABLE_PAY_AT_RISK" in trap_codes
    assert "CLAWBACK_RISK" in trap_codes


def test_simulate_midyear_switch_lethal_tax_trap():
    rules = load_tax_rules()
    # Scenario: 6 months at Co A earning 8L (TDS=0 due to 87A rebate <= 12L)
    # Then 6 months at Co B earning 9L (TDS=0 due to standalone 87A rebate)
    res = simulate_midyear_switch(
        company_a_months=6,
        company_a_gross=800000,
        company_a_tds=0,
        company_a_epf=38400,
        company_b_months=6,
        company_b_monthly_gross=150000,  # 1.5L/mo * 6 = 9L
        rules=rules,
    )

    incomes = res["incomes"]
    assert incomes["total_combined_gross"] == 1700000

    without_12b = res["without_form_12b"]
    assert without_12b["total_tds_collected"] == 0.0

    true_tax = res["true_statutory_liability"]
    # 17L gross - 75k std deduction = 16.25L taxable
    assert true_tax["total_tax_due"] == 130000.0

    shock = res["the_tax_shock"]
    assert shock["tds_shortfall"] == 130000.0
    assert shock["section_234b_interest"] == 5200.0  # 4%
    assert shock["section_234c_interest"] == 1950.0  # 1.5%
    assert shock["total_july_demand"] == 137150.0
    assert shock["has_critical_shortfall"] is True

    # With Form 12B, the new employer collects it spread over remaining 6 months
    with_12b = res["with_form_12b"]
    assert with_12b["july_tax_surprise"] == 0.0
    assert with_12b["adjusted_monthly_tds"] == round(130000.0 / 6, 2)


def test_compare_two_offers():
    rules = load_tax_rules()
    res = compare_two_offers(
        current_ctc=1500000,
        offer_a_ctc=2000000,
        offer_b_ctc=2400000,
        rules=rules,
    )

    assert "current" in res
    assert "offer_a" in res
    assert "offer_b" in res
    assert res["offer_a"]["monthly_cash_gain"] > 0
    assert res["offer_b"]["monthly_cash_gain"] > res["offer_a"]["monthly_cash_gain"]


def test_career_switch_api_endpoints(client, auth_headers):
    # 1. Decode offer endpoint
    res1 = client.post(
        "/api/v1/career/decode-offer",
        headers=auth_headers,
        json={"ctc": 1800000, "variable_pay": 150000, "joining_bonus": 50000},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert "monthly_breakdown" in data1
    assert "traps_detected" in data1
    assert len(data1["traps_detected"]) >= 1

    # 2. Simulate switch endpoint
    res2 = client.post(
        "/api/v1/career/simulate-switch",
        headers=auth_headers,
        json={
            "company_a_months": 5,
            "company_a_gross": 700000,
            "company_a_tds": 0,
            "company_a_epf": 30000,
            "company_b_months": 7,
            "company_b_monthly_gross": 160000,
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert "the_tax_shock" in data2
    assert "with_form_12b" in data2

    # 3. Form 12B generator endpoint
    res3 = client.post(
        "/api/v1/career/generate-form-12b",
        headers=auth_headers,
        json={
            "company_a_name": "Acme Tech Services Pvt Ltd",
            "company_a_tan": "BLRA12345C",
            "company_a_gross": 700000,
            "company_a_tds": 0,
            "company_a_epf": 30000,
            "period_start": "01-Apr-2024",
            "period_end": "31-Aug-2024",
        },
    )
    assert res3.status_code == 200
    data3 = res3.json()
    assert "raw_form_text" in data3
    assert "Acme Tech Services Pvt Ltd" in data3["raw_form_text"]
