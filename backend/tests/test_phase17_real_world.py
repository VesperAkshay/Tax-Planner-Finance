"""
Phase 17 Automated Validation Suite: Real-World Coverage Features (Tasks 17.1 - 17.10).

Validates:
- 17.1 & 17.7: Savings interest detection (80TTA / 80TTB) across recurring credits.
               Verifies separate flow of taxable interest income and 80TTA deduction into tax engine.
- 17.2 & 17.8: Capital gains / wrong ITR form flag (MF redemptions / broker payouts).
               Verifies informational flag without attempting any capital gains computation.
- 17.3 & 17.9: Salary arrears detection & Section 89 relief warning on anomalous one-time spikes.
- 17.4: AIS & Form 26AS statutory reconciliation checklist on report.
- 17.5: Filing deadline awareness countdown (July 31 of Assessment Year).
- 17.6 & 17.10: Year-over-year comparison across multi-year data and end-to-end report payload.
"""

from datetime import date
import io
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

import app.models  # Register all SQLModel models
from app.api.auth import create_access_token
from app.database import get_db_session
from app.db.seed_catalog import seed_deduction_catalog
from app.main import app
from app.models.account import Account
from app.models.salary_slip import SalarySlip
from app.models.tax_computation import TaxComputation
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_declared_deduction import DeductionSource, DeductionStatus, UserDeclaredDeduction
from app.seed_categories import seed_categories_sync
from app.tax_engine.real_world_detectors import (
    compute_filing_deadline_countdown,
    compute_year_over_year_comparison_data,
    detect_capital_gains_activity,
    detect_salary_arrears,
    detect_savings_interest,
    get_ais_26as_checklist,
)


@pytest.fixture(name="db_engine")
def db_engine_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_categories_sync(session)
        seed_deduction_catalog(session)
    return engine


@pytest.fixture(name="client")
def client_fixture(db_engine):
    def get_test_db():
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = get_test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(name="user_and_auth")
def user_and_auth_fixture(db_engine):
    with Session(db_engine) as session:
        user = User(
            email="realworld_tester@example.com",
            full_name="Real World User",
            pan="ABCDE1234F",
            hashed_password="mockhashedpassword123",
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        account = Account(
            user_id=user.id,
            account_name="HDFC Salary Account",
            account_number_mask="...1000",
            bank_name="HDFC Bank",
            account_type="savings",
            current_balance=250000.0,
        )
        session.add(account)
        session.commit()
        session.refresh(account)

        token = create_access_token({"sub": str(user.id), "email": user.email})
        headers = {"Authorization": f"Bearer {token}"}
        return {"user_id": user.id, "account_id": account.id, "headers": headers}


# ==============================================================================
# 17.1 & 17.7: Savings Interest Detection and Tax Computation Flow
# ==============================================================================


def test_17_1_and_17_7_savings_interest_detection_and_tax_flow(client, user_and_auth, db_engine):
    """
    Task 17.1 & 17.7:
    - Scans transactions for recurring savings interest credits.
    - Accurately aggregates total reportable interest and computes 80TTA/80TTB deduction.
    - Feeds reported interest as taxable income and 80TTA as deduction separately into the tax engine.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]
    u_id = user_and_auth["user_id"]

    # 1. Direct Detector Unit Verification
    sample_txns = [
        {"date": "2025-06-30", "transaction_type": "credit", "amount": 3250.0, "description": "INTEREST CREDIT SB"},
        {"date": "2025-09-30", "transaction_type": "credit", "amount": 3400.0, "description": "INT.PD Q2 SAVINGS"},
        {"date": "2025-12-31", "transaction_type": "credit", "amount": 3150.0, "description": "CREDIT INTEREST SB"},
        {"date": "2026-03-31", "transaction_type": "credit", "amount": 3200.0, "description": "SB INT CR"},
        {"date": "2025-08-15", "transaction_type": "debit", "amount": 1500.0, "description": "Grocery Store"},
    ]
    total_expected = 3250.0 + 3400.0 + 3150.0 + 3200.0  # 13,000.0

    # Non-senior citizen (80TTA: cap ₹10,000)
    res_regular = detect_savings_interest(sample_txns, is_senior_citizen=False)
    assert res_regular["has_interest"] is True
    assert res_regular["total_interest"] == total_expected
    assert res_regular["eligible_section"] == "80TTA"
    assert res_regular["cap"] == 10000.0
    assert res_regular["allowable_deduction"] == 10000.0
    assert res_regular["taxable_interest_income"] == total_expected
    assert "₹13,000.00" in res_regular["prompt_message"]
    assert "80TTA/80TTB" in res_regular["prompt_message"]

    # Senior citizen (80TTB: cap ₹50,000)
    res_senior = detect_savings_interest(sample_txns, is_senior_citizen=True)
    assert res_senior["eligible_section"] == "80TTB"
    assert res_senior["cap"] == 50000.0
    assert res_senior["allowable_deduction"] == total_expected

    # 2. Database & API End-to-End Tax Engine Flow Verification
    with Session(db_engine) as session:
        # Plant salary slip: Gross Pay = ₹1,00,000/month -> ₹12,00,000/year
        slip = SalarySlip(
            user_id=u_id,
            file_name="salary_slip_april_2025.pdf",
            file_path="/mock/path/salary_slip_april_2025.pdf",
            month=4,
            year=2025,
            financial_year="2025-2026",
            basic=50000.0,
            hra=20000.0,
            gross_pay=100000.0,
            net_pay=85000.0,
            employee_pf=6000.0,
        )
        session.add(slip)

        # Plant interest transactions in DB
        for item in sample_txns:
            session.add(
                Transaction(
                    account_id=acc_id,
                    date=date.fromisoformat(item["date"]),
                    description=item["description"],
                    amount=item["amount"],
                    transaction_type=item["transaction_type"],
                    financial_year="2025-2026",
                )
            )
        session.commit()

    # Call tax comparison report
    resp = client.get("/api/v1/tax/comparison-report?financial_year=2025-2026", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Assert separate line items:
    # 1. Total gross income includes the ₹13,000 interest: 12,00,000 + 13,000 = 12,13,000.00
    assert data["gross_income"] == 1213000.0
    assert data["salary_income"] == 1200000.0
    assert data["savings_interest_income"] == 13000.0

    # 2. 80TTA deduction of ₹10,000 is applied
    assert data["deductions_applied"].get("section_80tta") == 10000.0

    # 3. Old Regime: Gross 12,13,000 - 50,000 (std ded) - 10,000 (80TTA) = 11,53,000
    assert data["old_regime"]["taxable_income"] == 1153000.0

    # 4. New Regime: Gross 12,13,000 - 75,000 (std ded) = 11,38,000 (80TTA disallowed)
    assert data["new_regime"]["taxable_income"] == 1138000.0

    # Real-world flag present
    assert data["real_world_flags"]["savings_interest"]["has_interest"] is True
    assert data["real_world_flags"]["savings_interest"]["total_interest"] == 13000.0


# ==============================================================================
# 17.2 & 17.8: Capital Gains / Wrong ITR Form Flag (Informational Only)
# ==============================================================================


def test_17_2_and_17_8_capital_gains_flag_informational_only(client, user_and_auth, db_engine):
    """
    Task 17.2 & 17.8:
    - Detects mutual fund redemptions and broker payouts.
    - Flags ITR-2 advisory warning.
    - STRICT INVARIANT: Never attempts to calculate capital gains tax.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    # 1. Direct Detector Unit Verification
    txns = [
        {"date": "2025-07-15", "transaction_type": "credit", "amount": 85000.0, "description": "CAMS MUTUAL FUND REDEMPTION PAYOUT"},
        {"date": "2025-08-20", "transaction_type": "credit", "amount": 42000.0, "description": "ZERODHA BROKING EQUITY PAYOUT"},
        {"date": "2025-09-10", "transaction_type": "debit", "amount": 10000.0, "description": "SIP Purchase Mutual Fund"},  # Debit ignored
    ]

    cg_res = detect_capital_gains_activity(txns)
    assert cg_res["has_capital_gains_indicators"] is True
    assert cg_res["flagged_transactions_count"] == 2
    assert cg_res["recommended_itr_form"] == "ITR-2"
    assert "This may mean you have capital gains and need ITR-2, not ITR-1" in cg_res["warning_message"]
    assert "this tool doesn't compute capital gains" in cg_res["warning_message"]

    # Invariant: No tax amount calculation
    assert "capital_gains_tax" not in cg_res
    assert "computed_gains" not in cg_res

    # 2. API Financial Snapshot Integration
    with Session(db_engine) as session:
        for t in txns:
            session.add(
                Transaction(
                    account_id=acc_id,
                    date=date.fromisoformat(t["date"]),
                    description=t["description"],
                    amount=t["amount"],
                    transaction_type=t["transaction_type"],
                    financial_year="2025-2026",
                )
            )
        session.commit()

    snap_resp = client.get("/api/v1/financial-snapshot", headers=headers)
    assert snap_resp.status_code == 200
    snap_data = snap_resp.json()
    assert snap_data["real_world_flags"]["capital_gains"]["has_capital_gains_indicators"] is True
    assert snap_data["real_world_flags"]["capital_gains"]["recommended_itr_form"] == "ITR-2"


# ==============================================================================
# 17.3 & 17.9: Salary Arrears / Section 89 Relief Flag
# ==============================================================================


def test_17_3_and_17_9_salary_arrears_section_89_relief_flag(client, user_and_auth, db_engine):
    """
    Task 17.3 & 17.9:
    - Detects unusually large one-time salary-like credits inconsistent with regular monthly pattern.
    - Flags for checking Section 89 relief eligibility via Form 10E.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    # 1. Direct Detector Unit Verification
    txns = [
        {"date": "2025-04-30", "transaction_type": "credit", "amount": 80000.0, "description": "SALARY CREDIT TECHCORP"},
        {"date": "2025-05-31", "transaction_type": "credit", "amount": 80000.0, "description": "SALARY CREDIT TECHCORP"},
        {"date": "2025-06-30", "transaction_type": "credit", "amount": 80000.0, "description": "SALARY CREDIT TECHCORP"},
        # Anomalous spike: 2.5x baseline salary
        {"date": "2025-07-31", "transaction_type": "credit", "amount": 200000.0, "description": "SALARY CREDIT TECHCORP"},
    ]

    arr_res = detect_salary_arrears(txns)
    assert arr_res["has_arrears_indicator"] is True
    assert arr_res["regular_monthly_salary"] == 80000.0
    assert len(arr_res["flagged_transactions"]) == 1
    assert arr_res["flagged_transactions"][0]["amount"] == 200000.0
    assert "Section 89 relief (via Form 10E)" in arr_res["warning_message"]
    assert "unusually large salary credit of ₹200,000.00" in arr_res["warning_message"]

    # Also test explicit keyword arrears
    txns_explicit = [
        {"date": "2025-04-30", "transaction_type": "credit", "amount": 80000.0, "description": "SALARY CREDIT TECHCORP"},
        {"date": "2025-05-31", "transaction_type": "credit", "amount": 45000.0, "description": "PAY REVISION ARREARS TECHCORP"},
    ]
    arr_exp = detect_salary_arrears(txns_explicit)
    assert arr_exp["has_arrears_indicator"] is True


# ==============================================================================
# 17.4: AIS & Form 26AS Statutory Reconciliation Checklist
# ==============================================================================


def test_17_4_ais_and_form_26as_checklist():
    """
    Task 17.4:
    - Generates statutory AIS & Form 26AS cross-check checklist items.
    """
    checklist = get_ais_26as_checklist()
    assert "Before filing, download your AIS and Form 26AS" in checklist["notice_banner"]
    items = checklist["checklist_items"]
    assert len(items) >= 4

    item_ids = [i["id"] for i in items]
    assert "tds_26as" in item_ids
    assert "ais_interest_dividends" in item_ids
    assert "gross_salary_schedule" in item_ids
    assert "bank_prevalidation" in item_ids


# ==============================================================================
# 17.5: Filing Deadline Awareness Indicator
# ==============================================================================


def test_17_5_filing_deadline_awareness():
    """
    Task 17.5:
    - Surfaces countdown to salaried individual filing deadline (July 31 of Assessment Year).
    """
    # FY 2025-2026 -> AY 2026-2027 -> Deadline: 2026-07-31
    ref_future = date(2026, 5, 1)  # 91 days before deadline
    dl_future = compute_filing_deadline_countdown("2025-2026", reference_date=ref_future)
    assert dl_future["deadline_date"] == "2026-07-31"
    assert dl_future["assessment_year"] == "2026-2027"
    assert dl_future["days_remaining"] == 91
    assert dl_future["is_expired"] is False
    assert "91 days remaining" in dl_future["status_message"]

    # FY 2024-2025 -> AY 2025-2026 -> Deadline: 2025-07-31
    ref_past = date(2025, 8, 10)  # 10 days after deadline
    dl_past = compute_filing_deadline_countdown("2024-2025", reference_date=ref_past)
    assert dl_past["deadline_date"] == "2025-07-31"
    assert dl_past["days_remaining"] == -10
    assert dl_past["is_expired"] is True
    assert "Section 139(4)" in dl_past["status_message"]
    assert "Section 234F" in dl_past["status_message"]


# ==============================================================================
# 17.6 & 17.10: Year-over-Year Comparison & End-to-End Report Integration
# ==============================================================================


def test_17_6_and_17_10_year_over_year_and_end_to_end_report(client, user_and_auth, db_engine):
    """
    Task 17.6 & 17.10:
    - Multi-year comparison view compares current vs prior year metrics.
    - End-to-end report surfaces AIS checklist, deadline indicator, real-world flags,
      and produces downloadable PDF invoice with HTTP 200.
    """
    headers = user_and_auth["headers"]
    u_id = user_and_auth["user_id"]
    acc_id = user_and_auth["account_id"]

    with Session(db_engine) as session:
        # Prior Year computation (2024-2025)
        tc_prior = TaxComputation(
            user_id=u_id,
            financial_year="2024-2025",
            gross_income=1000000.0,
            old_regime_taxable_income=850000.0,
            old_regime_tax=82500.0,
            old_regime_cess=3300.0,
            old_regime_total_liability=85800.0,
            new_regime_taxable_income=925000.0,
            new_regime_tax=45000.0,
            new_regime_cess=1800.0,
            new_regime_total_liability=46800.0,
            recommended_regime="new",
            tax_savings=39000.0,
        )
        session.add(tc_prior)

        # Plant transactions for 2025-2026:
        # 1. Salary
        session.add(Transaction(account_id=acc_id, date=date(2025, 4, 30), description="SALARY CREDIT TECHCORP", amount=1200000.0, transaction_type="credit", financial_year="2025-2026"))
        # 2. Interest
        session.add(Transaction(account_id=acc_id, date=date(2025, 6, 30), description="INTEREST CREDIT SB", amount=8500.0, transaction_type="credit", financial_year="2025-2026"))
        # 3. MF Redemption (Capital gains)
        session.add(Transaction(account_id=acc_id, date=date(2025, 8, 15), description="CAMS MUTUAL FUND REDEMPTION PAYOUT", amount=50000.0, transaction_type="credit", financial_year="2025-2026"))
        # 4. Salary Arrears spike
        session.add(Transaction(account_id=acc_id, date=date(2025, 11, 30), description="SALARY CREDIT WITH RETROSPECTIVE ARREARS", amount=350000.0, transaction_type="credit", financial_year="2025-2026"))

        session.commit()

    # 1. Test Year-Over-Year endpoint
    yoy_resp = client.get("/api/v1/tax/year-over-year?current_fy=2025-2026&prior_fy=2024-2025", headers=headers)
    assert yoy_resp.status_code == 200
    yoy_data = yoy_resp.json()
    assert yoy_data["has_prior_year_data"] is True
    assert yoy_data["current_financial_year"] == "2025-2026"
    assert yoy_data["prior_financial_year"] == "2024-2025"
    assert "gross_income" in yoy_data["metrics"]
    assert len(yoy_data["highlights"]) >= 1

    # 2. Test full Comparison Report endpoint
    rep_resp = client.get("/api/v1/tax/comparison-report?financial_year=2025-2026", headers=headers)
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()

    # Verify all 3 flags appear with correct scoping
    rw_flags = rep_data["real_world_flags"]
    assert rw_flags["savings_interest"]["has_interest"] is True
    assert rw_flags["capital_gains"]["has_capital_gains_indicators"] is True
    assert rw_flags["salary_arrears"]["has_arrears_indicator"] is True

    # Verify AIS checklist & Deadline
    assert rep_data["ais_26as_checklist"] is not None
    assert len(rep_data["ais_26as_checklist"]["checklist_items"]) >= 4
    assert rep_data["filing_deadline"] is not None
    assert rep_data["filing_deadline"]["financial_year"] == "2025-2026"

    # 3. Test PDF Invoice Memo generation with Phase 17 inclusions
    pdf_resp = client.get("/api/v1/tax/comparison-report/pdf?financial_year=2025-2026", headers=headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")
    assert len(pdf_resp.content) > 1000
