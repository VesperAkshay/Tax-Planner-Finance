"""
Integration Test for the Complete API Pipeline (Tasks 8.8 & 8.9).

Executes the full pipeline via FastAPI TestClient:
1. User registration & JWT authentication.
2. Bank statement upload & parsing status check (Tasks 8.1 & 8.2).
3. Salary slip upload & compensation extraction (Task 8.1).
4. Financial snapshot computation (Task 8.3).
5. Salary reconciliation run and resolution flow (Task 8.4).
6. Tax planning agent conversation and deduction persistence (Tasks 8.5 & 7.3).
7. Final tax comparison report generation with RAG citations (Task 8.6).
8. Cross-tenant authorization check (Task 8.9: User B cannot access User A's data).
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

import app.models  # Ensures all SQLModel tables are registered in metadata
from app.database import get_db_session
from app.main import app
from app.seed_categories import seed_categories_sync

FIXTURES_DIR = Path("data/test_fixtures")


@pytest.fixture(scope="module")
def test_db_engine():
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
def client(test_db_engine):
    def get_test_session():
        with Session(test_db_engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==============================================================================
# 1. Authentication & JWT Setup (Task 8.7)
# ==============================================================================


@pytest.fixture(scope="module")
def user_a_token(client):
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@taxplanner.test",
            "password": "Password123!",
            "full_name": "Alice Sharma",
            "pan": "ABCDE1234F",
        },
    )
    assert reg_res.status_code == 201
    return reg_res.json()["access_token"]


@pytest.fixture(scope="module")
def user_b_token(client):
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@taxplanner.test",
            "password": "Password456!",
            "full_name": "Bob Verma",
            "pan": "XYZAB5678C",
        },
    )
    assert reg_res.status_code == 201
    return reg_res.json()["access_token"]


def test_auth_login_and_me(client, user_a_token):
    # Test valid login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@taxplanner.test", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Test wrong password
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@taxplanner.test", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # Test /auth/me
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {user_a_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "alice@taxplanner.test"
    assert me_res.json()["full_name"] == "Alice Sharma"


# ==============================================================================
# 2. Statement Upload & Parsing Status (Tasks 8.1 & 8.2)
# ==============================================================================


def test_statement_upload_and_status(client, user_a_token):
    csv_path = FIXTURES_DIR / "sample_hdfc_statement.csv"
    assert csv_path.exists(), f"Missing test fixture: {csv_path}"

    with open(csv_path, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload/statement",
            headers={"Authorization": f"Bearer {user_a_token}"},
            files={"file": ("sample_hdfc_statement.csv", f, "text/csv")},
            data={"bank_format": "hdfc"},
        )

    assert upload_res.status_code == 201
    data = upload_res.json()
    assert data["upload_id"] > 0
    assert data["transactions_count"] > 0
    upload_id = data["upload_id"]

    # Check status endpoint (Task 8.2)
    status_res = client.get(
        f"/api/v1/upload/status/{upload_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert status_res.status_code == 200
    sdata = status_res.json()
    assert sdata["upload_id"] == upload_id
    assert sdata["transactions_count"] > 0
    assert sdata["parse_status"] in ["completed", "needs_review"]


# ==============================================================================
# 3. Salary Slip Upload (Task 8.1)
# ==============================================================================


def test_salary_slip_upload(client, user_a_token):
    slip_path = FIXTURES_DIR / "sample_salary_slip.pdf"
    assert slip_path.exists(), f"Missing test fixture: {slip_path}"

    with open(slip_path, "rb") as f:
        upload_res = client.post(
            "/api/v1/upload/salary-slip",
            headers={"Authorization": f"Bearer {user_a_token}"},
            files={"file": ("sample_salary_slip.pdf", f, "application/pdf")},
            data={"month": 4, "year": 2025},
        )

    assert upload_res.status_code == 201
    data = upload_res.json()
    assert data["gross_pay"] > 0.0
    assert data["basic"] > 0.0
    assert data["net_pay"] > 0.0


# ==============================================================================
# 4. Financial Snapshot (Task 8.3)
# ==============================================================================


def test_financial_snapshot_endpoint(client, user_a_token):
    res = client.get(
        "/api/v1/financial-snapshot",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_income" in data
    assert "total_expenses" in data
    assert "net_savings" in data
    assert "savings_rate" in data
    assert isinstance(data["category_spending"], list)
    assert data["total_transactions_analyzed"] > 0


# ==============================================================================
# 5. Reconciliation Pipeline & Resolution (Task 8.4)
# ==============================================================================


def test_reconciliation_endpoints(client, user_a_token):
    # Run reconciliation
    run_res = client.post(
        "/api/v1/reconciliation/run",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert run_res.status_code == 200

    # List flags
    flags_res = client.get(
        "/api/v1/reconciliation/flags",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert flags_res.status_code == 200
    flags = flags_res.json()
    assert isinstance(flags, list)

    # If flags exist, test resolution flow
    if flags:
        flag_id = flags[0]["id"]
        # Missing user note should be rejected (Task 4.4 requirement)
        bad_res = client.post(
            f"/api/v1/reconciliation/flags/{flag_id}/resolve",
            headers={"Authorization": f"Bearer {user_a_token}"},
            json={"action": "resolved", "user_note": ""},
        )
        assert bad_res.status_code in [400, 422]

        # Valid resolution
        good_res = client.post(
            f"/api/v1/reconciliation/flags/{flag_id}/resolve",
            headers={"Authorization": f"Bearer {user_a_token}"},
            json={"action": "resolved", "user_note": "Verified by HR confirmation"},
        )
        assert good_res.status_code == 200
        assert good_res.json()["status"] == "resolved"


# ==============================================================================
# 6. Tax Planning Agent Conversation & Persistence (Tasks 8.5 & 7.3)
# ==============================================================================


def test_agent_chat_and_deductions_persistence(client, user_a_token):
    chat_res = client.post(
        "/api/v1/agent/chat",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={
            "message": "I invested 1.5L in PPF and have 25k medical insurance",
            "gross_income": 1500000.0,
            "user_responses": {
                "80c": 150000.0,
                "80d": 25000.0,
            },
            "session_id": "test_session_alice",
        },
    )
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert data["session_id"] == "test_session_alice"
    assert "node_80c" in data["visited_nodes"]
    assert "node_80d" in data["visited_nodes"]
    assert data["comparison_result"] is not None
    assert len(data["citations"]) >= 1
    assert "Recommended" in data["message"] or "Regime" in data["message"]


# ==============================================================================
# 7. Final Tax Comparison Report (Task 8.6 & 8.8 full pipeline assert)
# ==============================================================================


def test_tax_comparison_report(client, user_a_token):
    report_res = client.get(
        "/api/v1/tax/comparison-report?gross_income=1500000.0",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["gross_income"] == 1500000.0
    assert report["recommended_regime"] in ["new", "old"]
    assert report["new_regime"]["total_tax"] > 0.0
    assert report["old_regime"]["total_tax"] > 0.0
    assert "breakeven_deductions" in report
    assert len(report["citations"]) >= 1

    # Assert exact math for ₹15L with 1.5L (80C) + 25k (80D):
    # New Regime Tax: Gross 15L - 75k std ded = 14.25L taxable -> Tax = ₹97,500.00
    assert report["new_regime"]["total_tax"] == 97500.0


def test_tax_comparison_report_pdf_download(client, user_a_token):
    pdf_res = client.get(
        "/api/v1/tax/comparison-report/pdf?gross_income=1500000.0",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "attachment" in pdf_res.headers["content-disposition"]
    assert len(pdf_res.content) > 1000
    assert pdf_res.content.startswith(b"%PDF")


# ==============================================================================
# 8. Cross-Tenant Authorization Isolation (Task 8.9)
# ==============================================================================


def test_cross_tenant_isolation_checks(client, user_a_token, user_b_token):
    """
    Task 8.9: Verifies that User B cannot access or modify User A's data.
    """
    # 1. Attempt to access User A's upload status using User B's token
    status_leak = client.get(
        "/api/v1/upload/status/1",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert status_leak.status_code == 404, "Cross-tenant upload status leak!"

    # 2. Attempt to resolve User A's flag using User B's token
    flag_tamper = client.post(
        "/api/v1/reconciliation/flags/1/resolve",
        headers={"Authorization": f"Bearer {user_b_token}"},
        json={"action": "resolved", "user_note": "Tamper attempt"},
    )
    assert flag_tamper.status_code in [404, 400], "Cross-tenant flag resolution leak!"

    # 3. User B's financial snapshot must be completely isolated (0 transactions)
    b_snapshot = client.get(
        "/api/v1/financial-snapshot",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert b_snapshot.status_code == 200
    b_data = b_snapshot.json()
    assert b_data["total_transactions_analyzed"] == 0
    assert b_data["total_income"] == 0.0
    assert b_data["total_expenses"] == 0.0
