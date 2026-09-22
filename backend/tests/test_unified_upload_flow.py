"""
Tests for the Unified Document Upload Workflow, In-Memory PDF Decryption, and Auto-Classification.
"""

import io
from pathlib import Path
import pytest
from pypdf import PdfWriter
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import app.models
from app.database import get_db_session
from app.main import app
from app.models.salary_slip import SalarySlip
from app.models.user import User
from app.parsing.pdf_unlocker import (
    PDFInvalidPasswordError,
    PDFPasswordRequiredError,
    decrypt_pdf_in_memory,
    is_pdf_encrypted,
)
from app.seed_categories import seed_categories_sync


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
            "email": "intake_tester@example.com",
            "password": "ValidPassword123!",
            "full_name": "Intake Tester",
            "pan": "ABCDE1234F",
        },
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_encrypted_pdf_bytes(password: str) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt(password)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_pdf_unlocker_direct():
    pwd = "MySecret123"
    enc_bytes = create_encrypted_pdf_bytes(pwd)

    assert is_pdf_encrypted(enc_bytes) is True

    # Missing password -> raises PDFPasswordRequiredError
    with pytest.raises(PDFPasswordRequiredError):
        decrypt_pdf_in_memory(enc_bytes, None)

    # Wrong password -> raises PDFInvalidPasswordError
    with pytest.raises(PDFInvalidPasswordError):
        decrypt_pdf_in_memory(enc_bytes, "WrongPassword")

    # Correct password -> returns decrypted bytes
    dec_bytes, was_enc = decrypt_pdf_in_memory(enc_bytes, pwd)
    assert was_enc is True
    assert is_pdf_encrypted(dec_bytes) is False


def test_upload_statement_password_protection_detection(client, auth_headers):
    enc_bytes = create_encrypted_pdf_bytes("BankPass99")

    # Uploading locked statement with no password -> expects 422 with PASSWORD_REQUIRED
    res = client.post(
        "/api/v1/upload/statement",
        headers=auth_headers,
        files={"file": ("hdfc_statement_locked.pdf", enc_bytes, "application/pdf")},
    )
    assert res.status_code == 422
    assert "PASSWORD_REQUIRED" in res.text

    # Uploading locked statement with wrong password -> expects 422 with INVALID_PASSWORD
    res2 = client.post(
        "/api/v1/upload/statement",
        headers=auth_headers,
        data={"password": "WrongPassword"},
        files={"file": ("hdfc_statement_locked.pdf", enc_bytes, "application/pdf")},
    )
    assert res2.status_code == 422
    assert "INVALID_PASSWORD" in res2.text


def test_upload_salary_slip_password_protection_detection(client, auth_headers):
    enc_bytes = create_encrypted_pdf_bytes("SalaryPass2025")

    # Uploading locked salary slip with no password -> expects 422 with PASSWORD_REQUIRED
    res = client.post(
        "/api/v1/upload/salary-slip",
        headers=auth_headers,
        files={"file": ("payslip_locked.pdf", enc_bytes, "application/pdf")},
    )
    assert res.status_code == 422
    assert "PASSWORD_REQUIRED" in res.text

    # Uploading locked salary slip with wrong password -> expects 422 with INVALID_PASSWORD
    res2 = client.post(
        "/api/v1/upload/salary-slip",
        headers=auth_headers,
        data={"password": "WrongPassword"},
        files={"file": ("payslip_locked.pdf", enc_bytes, "application/pdf")},
    )
    assert res2.status_code == 422
    assert "INVALID_PASSWORD" in res2.text


def test_upload_auto_endpoint_routes_csv_to_statement(client, auth_headers):
    csv_content = (
        "Date,Narration,Debit,Credit,Balance\n"
        "2024-05-01,SALARY CREDIT,,100000,100000\n"
        "2024-05-02,PPF CONTRIBUTION,12500,,87500\n"
    ).encode("utf-8")

    res = client.post(
        "/api/v1/upload/auto",
        headers=auth_headers,
        files={"file": ("my_bank_statement.csv", csv_content, "text/csv")},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["document_type"] == "bank_statement"
    assert data["statement"] is not None
    assert data["statement"]["transactions_count"] == 2
