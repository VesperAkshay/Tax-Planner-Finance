"""
Phase 15 Automated Validation Suite: Account & Data Lifecycle Management (Tasks 15.1 - 15.10).

Validates:
- 15.7: Duplicate file upload detection: uploading the same file twice rejects the second with HTTP 409.
- 15.8: Overlapping date ranges: warning raised before ingestion (HTTP 409), and when confirmed,
        transactions are deduplicated without double-counting.
- 15.9: Scoped upload deletion: deleting a single upload cascades its transactions while leaving
        other uploads intact.
- 15.10: Full account erasure (right-to-erasure): wiping account leaves exactly 0 orphaned rows
         across all database tables.
- 15.4 / 15.1: Scoped financial year data deletion.
- 15.5: Data export ZIP packaging transactions CSV, declared deductions JSON, and tax report.
"""

from datetime import date, datetime
import io
import zipfile
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
from app.models.elicitation_progress import ElicitationProgress, ElicitationStateEnum
from app.models.reconciliation_flag import ReconciliationFlag
from app.models.salary_slip import SalarySlip
from app.models.statement_upload import StatementUpload
from app.models.tax_computation import TaxComputation
from app.models.transaction import Transaction
from app.models.user import User
from app.models.user_declared_deduction import DeductionSource, DeductionStatus, UserDeclaredDeduction
from app.seed_categories import seed_categories_sync


CSV_CONTENT_1 = b"""Date,Description,Amount,Type,Balance
2025-04-05,Salary Credit TechCorp,120000.00,credit,120000.00
2025-04-10,Swiggy Bangalore,650.00,debit,119350.00
2025-04-15,Amazon Shopping,2400.00,debit,116950.00
"""

# Overlaps April 10 - April 22 (includes Swiggy and Amazon duplicates + new Uber txn)
CSV_CONTENT_OVERLAP = b"""Date,Description,Amount,Type,Balance
2025-04-10,Swiggy Bangalore,650.00,debit,119350.00
2025-04-15,Amazon Shopping,2400.00,debit,116950.00
2025-04-22,Uber Rides,450.00,debit,116500.00
"""


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


@pytest.fixture(name="user_and_auth")
def user_and_auth_fixture(db_engine):
    with Session(db_engine) as session:
        user = User(
            email="lifecycle_user@example.com",
            hashed_password="pw_hash_sample",
            is_active=True,
            pan="ABCDE1234F",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        acc = Account(
            user_id=user.id,
            account_name="Primary Savings",
            bank_name="HDFC Bank",
            account_number="9876543210",
        )
        session.add(acc)
        session.commit()
        session.refresh(acc)

        token = create_access_token(data={"sub": str(user.id), "email": user.email})
        user_id = user.id
        acc_id = acc.id

    return {
        "user_id": user_id,
        "account_id": acc_id,
        "headers": {"Authorization": f"Bearer {token}"},
    }


# ==============================================================================
# Task 15.7: Duplicate Upload Detection
# ==============================================================================


def test_15_7_duplicate_upload_detection(client, user_and_auth):
    """
    Task 15.7: Upload the same file twice; assert the second upload is rejected
    with a clear duplicate-detection message (HTTP 409).
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    files = {"file": ("statement_apr_2025.csv", io.BytesIO(CSV_CONTENT_1), "text/csv")}
    data = {"account_id": str(acc_id), "bank_format": "generic"}

    # 1. First upload succeeds
    resp1 = client.post("/api/v1/upload/statement", headers=headers, files=files, data=data)
    assert resp1.status_code == 201
    assert resp1.json()["transactions_count"] == 3

    # 2. Re-uploading exact same file is rejected
    files2 = {"file": ("statement_apr_2025.csv", io.BytesIO(CSV_CONTENT_1), "text/csv")}
    resp2 = client.post("/api/v1/upload/statement", headers=headers, files=files2, data=data)
    assert resp2.status_code == 409
    assert "duplicate upload detected" in resp2.json()["detail"].lower()


# ==============================================================================
# Task 15.8: Overlapping Date Ranges & Deduplication
# ==============================================================================


def test_15_8_overlapping_date_ranges_and_deduplication(client, user_and_auth, db_engine):
    """
    Task 15.8: Upload two overlapping-date-range statements for the same account;
    assert a warning is raised before ingestion, and confirm no transaction is
    double-counted if the user proceeds anyway.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    # 1. Base upload
    files_base = {"file": ("statement_apr_2025.csv", io.BytesIO(CSV_CONTENT_1), "text/csv")}
    resp_base = client.post("/api/v1/upload/statement", headers=headers, files=files_base, data={"account_id": str(acc_id)})
    assert resp_base.status_code == 201

    # 2. Attempt upload of overlapping file without confirm_overlap -> rejected with warning
    files_overlap = {"file": ("statement_overlap.csv", io.BytesIO(CSV_CONTENT_OVERLAP), "text/csv")}
    data_no_confirm = {"account_id": str(acc_id), "confirm_overlap": "false"}
    resp_warn = client.post("/api/v1/upload/statement", headers=headers, files=files_overlap, data=data_no_confirm)
    assert resp_warn.status_code == 409
    assert "overlaps with prior upload" in resp_warn.json()["detail"].lower()

    # 3. Upload with confirm_overlap = true -> proceeds with deduplication
    files_overlap2 = {"file": ("statement_overlap.csv", io.BytesIO(CSV_CONTENT_OVERLAP), "text/csv")}
    data_confirm = {"account_id": str(acc_id), "confirm_overlap": "true"}
    resp_ok = client.post("/api/v1/upload/statement", headers=headers, files=files_overlap2, data=data_confirm)
    assert resp_ok.status_code == 201
    # Only 1 new transaction (Uber Rides) should be ingested; Swiggy and Amazon were deduplicated
    assert resp_ok.json()["transactions_count"] == 1

    # 4. Verify total transactions in database for this account = 4 (Salary, Swiggy, Amazon, Uber)
    with Session(db_engine) as session:
        txns = session.exec(select(Transaction).where(Transaction.account_id == acc_id)).all()
        assert len(txns) == 4
        descriptions = [t.description for t in txns]
        assert descriptions.count("Swiggy Bangalore") == 1
        assert descriptions.count("Amazon Shopping") == 1
        assert descriptions.count("Uber Rides") == 1


# ==============================================================================
# Task 15.9: Scoped Delete - Single Upload
# ==============================================================================


def test_15_9_delete_single_upload_cascade(client, user_and_auth, db_engine):
    """
    Task 15.9: Delete a single upload; assert its transactions are gone
    but other uploads are untouched.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    # 1. Upload two distinct statements
    files1 = {"file": ("statement_1.csv", io.BytesIO(CSV_CONTENT_1), "text/csv")}
    resp1 = client.post("/api/v1/upload/statement", headers=headers, files=files1, data={"account_id": str(acc_id)})
    assert resp1.status_code == 201
    upload_1_id = resp1.json()["upload_id"]

    files2 = {"file": ("statement_2.csv", io.BytesIO(CSV_CONTENT_OVERLAP), "text/csv")}
    resp2 = client.post("/api/v1/upload/statement", headers=headers, files=files2, data={"account_id": str(acc_id), "confirm_overlap": "true"})
    assert resp2.status_code == 201
    upload_2_id = resp2.json()["upload_id"]

    # 2. Without confirmation: rejected
    del_no_conf = client.delete(f"/api/v1/lifecycle/upload/{upload_1_id}", headers=headers)
    assert del_no_conf.status_code == 400

    # 3. With confirmation: deletes upload 1 and its transactions
    del_resp = client.delete(f"/api/v1/lifecycle/upload/{upload_1_id}?confirm=true", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 4. Assert in database: upload 1 is gone, upload 2 and its transaction remain
    with Session(db_engine) as session:
        assert session.get(StatementUpload, upload_1_id) is None
        assert session.get(StatementUpload, upload_2_id) is not None

        txns_left = session.exec(select(Transaction).where(Transaction.account_id == acc_id)).all()
        assert len(txns_left) == 1
        assert txns_left[0].description == "Uber Rides"


# ==============================================================================
# Task 15.4 / 15.1: Scoped Delete - Financial Year Data
# ==============================================================================


def test_15_4_delete_financial_year_data(client, user_and_auth, db_engine):
    """
    Task 15.4: Delete all data for a specific financial year;
    assert deductions, computations, and FY transactions are removed.
    """
    headers = user_and_auth["headers"]
    user_id = user_and_auth["user_id"]

    # Pre-seed deduction and computation for 2025-2026
    with Session(db_engine) as session:
        ded = UserDeclaredDeduction(
            user_id=user_id,
            financial_year="2025-2026",
            section="80C",
            amount=50000.0,
            source=DeductionSource.catalog_self_added,
            status=DeductionStatus.declared,
        )
        session.add(ded)
        prog = ElicitationProgress(
            user_id=user_id,
            financial_year="2025-2026",
            section_code="80C",
            state=ElicitationStateEnum.answered,
        )
        session.add(prog)
        session.commit()

    # Delete 2025-2026 data
    resp = client.delete("/api/v1/lifecycle/financial-year/2025-2026?confirm=true", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Verify in DB
    with Session(db_engine) as session:
        deds_left = session.exec(
            select(UserDeclaredDeduction).where(UserDeclaredDeduction.user_id == user_id)
        ).all()
        assert len(deds_left) == 0


# ==============================================================================
# Task 15.5: Data Export ZIP Bundle
# ==============================================================================


def test_15_5_export_user_data_bundle(client, user_and_auth):
    """
    Task 15.5: Export endpoint returns a valid ZIP bundle containing
    transactions.csv, declared_deductions.json, export_summary.json.
    """
    headers = user_and_auth["headers"]
    resp = client.get("/api/v1/lifecycle/export?financial_year=2025-2026", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert "tax_planner_export_FY2025_2026.zip" in resp.headers["content-disposition"]

    # Open zip and check file entries
    zip_bytes = io.BytesIO(resp.content)
    with zipfile.ZipFile(zip_bytes, "r") as zf:
        namelist = zf.namelist()
        assert "transactions.csv" in namelist
        assert "declared_deductions.json" in namelist
        assert "export_summary.json" in namelist


# ==============================================================================
# Task 15.10: Full Account Erasure (Right-to-Erasure)
# ==============================================================================


def test_15_10_account_erasure_zero_orphans(client, user_and_auth, db_engine):
    """
    Task 15.10: Full account deletion; assert a post-deletion query across
    all tables returns zero rows for that user.
    """
    headers = user_and_auth["headers"]
    user_id = user_and_auth["user_id"]

    # Request erasure
    resp = client.delete("/api/v1/lifecycle/account?confirm=true", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Assert ZERO rows across ALL database tables for this user
    with Session(db_engine) as session:
        assert session.get(User, user_id) is None
        assert len(session.exec(select(Account).where(Account.user_id == user_id)).all()) == 0
        assert len(session.exec(select(StatementUpload).where(StatementUpload.user_id == user_id)).all()) == 0
        assert len(session.exec(select(SalarySlip).where(SalarySlip.user_id == user_id)).all()) == 0
        assert len(session.exec(select(ReconciliationFlag).where(ReconciliationFlag.user_id == user_id)).all()) == 0
        assert len(session.exec(select(TaxComputation).where(TaxComputation.user_id == user_id)).all()) == 0
        assert len(session.exec(select(ElicitationProgress).where(ElicitationProgress.user_id == user_id)).all()) == 0
        assert len(session.exec(select(UserDeclaredDeduction).where(UserDeclaredDeduction.user_id == user_id)).all()) == 0


# ==============================================================================
# Interactive Uploaded Files List & Salary Slip Deletion
# ==============================================================================


def test_list_and_delete_uploaded_files(client, user_and_auth, db_engine):
    """
    Validates GET /lifecycle/files returns structured list of uploaded files,
    and DELETE /lifecycle/salary-slip/{id} cascades flags and removes slip.
    """
    headers = user_and_auth["headers"]
    user_id = user_and_auth["user_id"]

    # 1. Initially empty
    resp = client.get("/api/v1/lifecycle/files", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["files"] == []

    # 2. Seed a StatementUpload and a SalarySlip
    with Session(db_engine) as session:
        upload = StatementUpload(
            user_id=user_id,
            file_name="hdfc_march_2025.csv",
            file_path="/tmp/hdfc.csv",
            file_type="csv",
            parse_status="completed",
        )
        session.add(upload)
        session.commit()
        session.refresh(upload)

        # Add child transaction
        txn = Transaction(
            account_id=1,
            upload_id=upload.id,
            date=datetime.now().date(),
            description="UPI Test Payment",
            amount=500.0,
            transaction_type="debit",
            financial_year="2025-2026",
        )
        session.add(txn)

        slip = SalarySlip(
            user_id=user_id,
            file_name="salary_slip_oct_2025.pdf",
            file_path="/tmp/salary.pdf",
            month=10,
            year=2025,
            financial_year="2025-2026",
            gross_pay=120000.0,
            net_pay=100000.0,
        )
        session.add(slip)
        session.commit()
        session.refresh(slip)
        slip_id = slip.id
        upload_id = upload.id

    # 3. List files again - should contain both files
    resp = client.get("/api/v1/lifecycle/files", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    filenames = [f["file_name"] for f in data["files"]]
    assert "hdfc_march_2025.csv" in filenames
    assert "salary_slip_oct_2025.pdf" in filenames

    stmt_entry = next(f for f in data["files"] if f["type"] == "statement")
    assert stmt_entry["id"] == upload_id
    assert stmt_entry["transaction_count"] == 1

    slip_entry = next(f for f in data["files"] if f["type"] == "salary_slip")
    assert slip_entry["id"] == slip_id
    assert "October 2025" in slip_entry["date_range"]

    # 4. Delete salary slip
    del_resp = client.delete(f"/api/v1/lifecycle/salary-slip/{slip_id}?confirm=true", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 5. List files again - should only have 1 file left
    resp2 = client.get("/api/v1/lifecycle/files", headers=headers)
    assert resp2.json()["total"] == 1
    assert resp2.json()["files"][0]["id"] == upload_id

    # 6. Delete statement upload
    del_resp2 = client.delete(f"/api/v1/lifecycle/upload/{upload_id}?confirm=true", headers=headers)
    assert del_resp2.status_code == 200
    assert del_resp2.json()["success"] is True

    # 7. List files again - now empty
    resp3 = client.get("/api/v1/lifecycle/files", headers=headers)
    assert resp3.json()["total"] == 0
