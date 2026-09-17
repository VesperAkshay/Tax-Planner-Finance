"""
Phase 16 Automated Validation Suite: Input Robustness & Error Handling (Tasks 16.1 - 16.7).

Validates:
- 16.1: Non-financial document rejection (non-financial PDF or CSV rejected early with HTTP 422).
- 16.2: Explicit detection of password-protected / encrypted PDFs returning clear 422 warning.
- 16.3: Unsupported CSV format fallback: rejects with HTTP 422 and available columns list;
        succeeds cleanly when custom column_mapping is provided.
- 16.4: Empty or near-empty statement handling: warns on <= 1 transaction, caveats financial snapshot stats,
        and marks budget diagnostic as 'Insufficient Data'.
- 16.5: Forex transaction detection: flags foreign currency markers (USD, EUR, FX Markup),
        marks transactions as needs_review, and surfaces actionable warning.
"""

import io
import json
import pytest
from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import app.models  # Register all SQLModel models
from app.api.auth import create_access_token
from app.database import get_db_session
from app.db.seed_catalog import seed_deduction_catalog
from app.main import app
from app.models.account import Account
from app.models.user import User
from app.seed_categories import seed_categories_sync


# ------------------------------------------------------------------------------
# Helpers to generate adversarial fixtures
# ------------------------------------------------------------------------------

def generate_non_financial_pdf_bytes() -> bytes:
    """Generates a valid PDF with zero financial terms (e.g. a cooking recipe)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, "Grandma's Chocolate Chip Cookies Recipe")
    c.drawString(100, 730, "Ingredients: 2 cups flour, 1 cup butter, brown sugar, vanilla extract.")
    c.drawString(100, 710, "Bake at 350 degrees Fahrenheit for 12 minutes until golden brown.")
    c.drawString(100, 690, "Serve warm with cold milk. Enjoy with family and friends.")
    c.save()
    return buf.getvalue()


def generate_encrypted_pdf_bytes() -> bytes:
    """Generates a PDF byte string containing an /Encrypt dictionary simulation."""
    # A minimalist PDF with an /Encrypt trailer
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Filter /Standard /V 2 /R 3 /O (sampleownerpassword) /U (sampleuserpassword) /P -4 >>\nendobj\n"
        b"trailer\n<< /Root 1 0 R /Encrypt 4 0 R >>\n%%EOF\n"
    )
    return content


UNSUPPORTED_CSV_CONTENT = b"""Txn_Timestamp,Counterparty_Entity,Transfer_Value,Vault_Balance
2025-05-10,Custom Merchant Alpha,1250.00,45000.00
2025-05-12,Custom Merchant Beta,450.00,44550.00
"""

SINGLE_TXN_CSV_CONTENT = b"""Date,Description,Amount,Type,Balance
2025-04-10,Grocery Store Purchase,1200.00,debit,48800.00
"""

FOREX_CSV_CONTENT = b"""Date,Description,Amount,Type,Balance
2025-04-10,Domestic Electric Bill,1500.00,debit,48500.00
2025-04-12,USD 45.00 AWS Cloud Hosting FX MARKUP,3750.00,debit,44750.00
2025-04-14,Hotel Booking Paris EUR 120.00 INTL POS,10800.00,debit,33950.00
"""

NON_FINANCIAL_CSV_CONTENT = b"""SKU,Product_Title,Warehouse_Location,Units_In_Stock
A101,Blue Cotton T-Shirt,Bay-4,150
B202,Red Canvas Shoes,Bay-9,75
"""


# ------------------------------------------------------------------------------
# Test Fixtures
# ------------------------------------------------------------------------------

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
            email="robust_tester@example.com",
            hashed_password="pw_hash_test",
            is_active=True,
            pan="ROBST1234K",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        acc = Account(
            user_id=user.id,
            account_name="Robustness Primary",
            bank_name="Test Bank",
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
# Task 16.1: Pre-Classification & Non-Financial Document Rejection
# ==============================================================================


def test_16_1_reject_non_financial_pdf(client, user_and_auth):
    """
    Task 16.1: Uploading a non-financial PDF (e.g. recipe/essay) is rejected early
    with HTTP 422 before expensive OCR/Docling processing.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    pdf_bytes = generate_non_financial_pdf_bytes()
    files = {"file": ("cookie_recipe.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"account_id": str(acc_id)}

    resp = client.post("/api/v1/upload/statement", headers=headers, files=files, data=data)
    assert resp.status_code == 422
    assert "does not structurally resemble a bank statement" in resp.json()["detail"].lower()


def test_16_1_reject_non_financial_csv(client, user_and_auth):
    """
    Task 16.1: Uploading a non-financial CSV (e.g. inventory table) is rejected early with HTTP 422.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    files = {"file": ("inventory.csv", io.BytesIO(NON_FINANCIAL_CSV_CONTENT), "text/csv")}
    data = {"account_id": str(acc_id)}

    resp = client.post("/api/v1/upload/statement", headers=headers, files=files, data=data)
    assert resp.status_code == 422
    assert "does not appear to be a valid financial statement" in resp.json()["detail"].lower()


# ==============================================================================
# Task 16.2: Password-Protected PDF Detection
# ==============================================================================


def test_16_2_detect_password_protected_pdf(client, user_and_auth):
    """
    Task 16.2: Detect password-protected/encrypted PDFs explicitly;
    prompt the user for decryption rather than failing silently or returning an empty parse.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    enc_bytes = generate_encrypted_pdf_bytes()
    files = {"file": ("locked_statement.pdf", io.BytesIO(enc_bytes), "application/pdf")}
    data = {"account_id": str(acc_id)}

    resp = client.post("/api/v1/upload/statement", headers=headers, files=files, data=data)
    assert resp.status_code == 422
    assert "password-protected or encrypted" in resp.json()["detail"].lower()


# ==============================================================================
# Task 16.3: Unsupported CSV Format & Custom Column Mapping Fallback
# ==============================================================================


def test_16_3_unsupported_csv_requires_mapping_and_succeeds_with_mapping(client, user_and_auth):
    """
    Task 16.3:
    1. CSV from unsupported bank without mapping returns HTTP 422 listing available columns.
    2. Providing custom column_mapping allows seamless parsing and ingestion.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    # 1. Without mapping: rejected with available columns list
    files1 = {"file": ("custom_bank.csv", io.BytesIO(UNSUPPORTED_CSV_CONTENT), "text/csv")}
    data1 = {"account_id": str(acc_id)}
    resp1 = client.post("/api/v1/upload/statement", headers=headers, files=files1, data=data1)
    assert resp1.status_code == 422
    detail = resp1.json()["detail"]
    assert detail["error"] == "unsupported_bank_format"
    assert "Txn_Timestamp" in detail["available_columns"]
    assert "Counterparty_Entity" in detail["available_columns"]

    # 2. With custom column mapping: succeeds cleanly
    mapping = {
        "date": "Txn_Timestamp",
        "description": "Counterparty_Entity",
        "amount": "Transfer_Value",
        "balance": "Vault_Balance",
    }
    files2 = {"file": ("custom_bank.csv", io.BytesIO(UNSUPPORTED_CSV_CONTENT), "text/csv")}
    data2 = {
        "account_id": str(acc_id),
        "column_mapping": json.dumps(mapping),
    }
    resp2 = client.post("/api/v1/upload/statement", headers=headers, files=files2, data=data2)
    assert resp2.status_code == 201
    assert resp2.json()["transactions_count"] == 2
    assert resp2.json()["parse_status"] == "completed"


# ==============================================================================
# Task 16.4: Empty or Near-Empty Statement Handling
# ==============================================================================


def test_16_4_near_empty_statement_caveats_stats(client, user_and_auth):
    """
    Task 16.4: Handle single-transaction statement without misleading 100% stats;
    surfaces warning on upload and caveats financial snapshot stats.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    # 1. Upload single-transaction statement
    files = {"file": ("single_txn.csv", io.BytesIO(SINGLE_TXN_CSV_CONTENT), "text/csv")}
    data = {"account_id": str(acc_id)}
    resp = client.post("/api/v1/upload/statement", headers=headers, files=files, data=data)
    assert resp.status_code == 201
    assert resp.json()["transactions_count"] == 1
    assert "fewer than 2 transactions" in resp.json()["warning"].lower()

    # 2. Fetch financial snapshot: check caveat and insufficient sample flag
    snap_resp = client.get("/api/v1/financial-snapshot", headers=headers)
    assert snap_resp.status_code == 200
    snap_data = snap_resp.json()
    assert snap_data["is_sample_insufficient"] is True
    assert snap_data["caveat"] is not None
    assert "fewer than 2 transactions" in snap_data["caveat"].lower()
    assert snap_data["budget_rule_diagnostic"]["status"] == "Insufficient Data"


# ==============================================================================
# Task 16.5: Forex / Non-INR Transaction Detection
# ==============================================================================


def test_16_5_forex_transaction_detection_and_flagging(client, user_and_auth):
    """
    Task 16.5: Detects non-INR currency markers (USD, EUR, INTL POS, FX MARKUP),
    sets needs_review flag, counts forex transactions, and returns an actionable warning.
    """
    headers = user_and_auth["headers"]
    acc_id = user_and_auth["account_id"]

    files = {"file": ("forex_statement.csv", io.BytesIO(FOREX_CSV_CONTENT), "text/csv")}
    data = {"account_id": str(acc_id)}
    resp = client.post("/api/v1/upload/statement", headers=headers, files=files, data=data)
    assert resp.status_code == 201
    upload_data = resp.json()

    # Assert forex detection flags
    assert upload_data["has_forex"] is True
    assert upload_data["forex_count"] == 2  # AWS USD and Paris EUR
    assert "non-inr / forex transaction" in upload_data["warning"].lower()
    assert upload_data["needs_review"] is True

    # Assert in financial snapshot
    snap_resp = client.get("/api/v1/financial-snapshot", headers=headers)
    assert snap_resp.status_code == 200
    snap_data = snap_resp.json()
    assert snap_data["has_forex_transactions"] is True
    assert snap_data["forex_count"] == 2
