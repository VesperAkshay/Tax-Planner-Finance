"""
Automated Validation Test Suite for Bring Your Own Key (BYOK) (v1.2).

Verifies:
1. Cryptographic AES-128-CBC Fernet encryption, decryption, and per-user HKDF isolation.
2. Secure API key masking preventing secret exposure.
3. REST API CRUD endpoints: saving encrypted key, retrieval with masking, and deletion.
4. Cross-tenant isolation: User B cannot view or access User A's key.
5. Dynamic LLM client factory dispatch across all 5 supported providers (OpenAI, Anthropic, OpenRouter, Groq, Gemini).
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.agent.crypto import decrypt_api_key, encrypt_api_key, mask_api_key
from app.agent.llm_client import get_llm_client_and_model
from app.api.auth import get_current_user
from app.database import get_db_session
from app.main import app
from app.models.user import User
from app.models.user_llm_key import UserLLMKey


# In-memory SQLite for fast test isolation
@pytest.fixture(name="byok_session")
def byok_session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user_a")
def test_user_a_fixture(byok_session: Session):
    user = User(
        id=101,
        email="user_a@example.com",
        full_name="User Alpha",
        hashed_password="hashed_pw_a",
        is_active=True,
    )
    byok_session.add(user)
    byok_session.commit()
    byok_session.refresh(user)
    return user


@pytest.fixture(name="test_user_b")
def test_user_b_fixture(byok_session: Session):
    user = User(
        id=202,
        email="user_b@example.com",
        full_name="User Beta",
        hashed_password="hashed_pw_b",
        is_active=True,
    )
    byok_session.add(user)
    byok_session.commit()
    byok_session.refresh(user)
    return user


# ==============================================================================
# 1. Cryptographic Security Tests
# ==============================================================================


def test_crypto_encryption_and_decryption():
    raw_key = "sk-proj-test1234567890abcdefghijklmnopqrstuvwxyz"
    user_id = 42

    ciphertext = encrypt_api_key(raw_key, user_id)
    assert ciphertext != raw_key
    assert len(ciphertext) > 20

    decrypted = decrypt_api_key(ciphertext, user_id)
    assert decrypted == raw_key


def test_crypto_cross_user_isolation():
    raw_key = "sk-ant-api03-secret-key-for-user-1"
    user_1 = 1
    user_2 = 2

    ciphertext = encrypt_api_key(raw_key, user_1)

    # Decrypting User 1's key with User 2's salt must fail
    with pytest.raises(Exception):
        decrypt_api_key(ciphertext, user_2)


def test_crypto_key_masking():
    # Standard OpenAI key
    assert mask_api_key("sk-proj-1234567890abcdef") == "sk-proj••••••••cdef"
    # Anthropic key
    assert mask_api_key("sk-ant-api03-abcdef123456") == "sk-ant-••••••••3456"
    # Short key
    assert mask_api_key("short") == "••••••••"
    # Empty
    assert mask_api_key("") == ""
    assert mask_api_key(None) == ""


# ==============================================================================
# 2. REST API CRUD & Isolation Tests
# ==============================================================================


def test_byok_api_crud_lifecycle(byok_session: Session, test_user_a: User):
    def override_get_db():
        yield byok_session

    def override_get_user():
        return test_user_a

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_user

    client = TestClient(app)

    # 1. Initially no key
    res = client.get("/api/v1/byok")
    assert res.status_code == 200
    assert res.json()["has_key"] is False

    # 2. Save encrypted key without live network probe
    payload = {
        "provider": "openai",
        "api_key": "sk-proj-customuserkey9876543210zyxwvu",
        "model_name": "gpt-4o-mini",
        "validate_before_save": False,
    }
    save_res = client.post("/api/v1/byok", json=payload)
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["has_key"] is True
    assert save_data["provider"] == "openai"
    assert save_data["model_name"] == "gpt-4o-mini"
    # Verify raw secret is NOT leaked
    assert "sk-proj-customuserkey9876543210zyxwvu" not in str(save_data)
    assert "••••••••" in save_data["masked_key"]

    # 3. Retrieve status
    get_res = client.get("/api/v1/byok")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["has_key"] is True
    assert get_data["is_active"] is True
    assert get_data["provider"] == "openai"
    assert "sk-proj" in get_data["masked_key"]

    # 4. Delete / Revoke key
    del_res = client.delete("/api/v1/byok")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 5. Verify status returns has_key = False
    after_del = client.get("/api/v1/byok")
    assert after_del.status_code == 200
    assert after_del.json()["has_key"] is False

    app.dependency_overrides.clear()


def test_byok_cross_user_isolation_api(byok_session: Session, test_user_a: User, test_user_b: User):
    def override_get_db():
        yield byok_session

    # User A saves a key
    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: test_user_a

    client = TestClient(app)
    save_res = client.post(
        "/api/v1/byok",
        json={
            "provider": "groq",
            "api_key": "gsk_testkeyuser1234567890",
            "model_name": "llama-3.3-70b-versatile",
            "validate_before_save": False,
        },
    )
    assert save_res.status_code == 200

    # User B checks BYOK status -> MUST BE FALSE
    app.dependency_overrides[get_current_user] = lambda: test_user_b
    client_b = TestClient(app)
    res_b = client_b.get("/api/v1/byok")
    assert res_b.status_code == 200
    assert res_b.json()["has_key"] is False

    app.dependency_overrides.clear()


# ==============================================================================
# 3. Dynamic LLM Client Dispatcher Tests
# ==============================================================================


def test_llm_dispatcher_openai():
    client, model, prov = get_llm_client_and_model(
        byok_key="sk-test-key-openai",
        byok_provider="openai",
        byok_model="gpt-4o-mini",
    )
    assert client is not None
    assert model == "gpt-4o-mini"
    assert prov == "openai"


def test_llm_dispatcher_anthropic():
    client, model, prov = get_llm_client_and_model(
        byok_key="sk-ant-test-key",
        byok_provider="anthropic",
        byok_model="claude-3-5-haiku-latest",
    )
    assert client is not None
    assert model == "claude-3-5-haiku-latest"
    assert prov == "anthropic"


def test_llm_dispatcher_openrouter():
    client, model, prov = get_llm_client_and_model(
        byok_key="sk-or-v1-test",
        byok_provider="openrouter",
        byok_model="openrouter/free",
    )
    assert client is not None
    assert model == "openrouter/free"
    assert prov == "openrouter"


def test_llm_dispatcher_gemini():
    client, model, prov = get_llm_client_and_model(
        byok_key="gemini-test-key",
        byok_provider="gemini",
        byok_model="gemini-1.5-flash",
    )
    assert client is not None
    assert model == "gemini-1.5-flash"
    assert prov == "openai"


def test_llm_dispatcher_groq():
    client, model, prov = get_llm_client_and_model(
        byok_key="gsk-test-key",
        byok_provider="groq",
        byok_model="llama-3.3-70b-versatile",
    )
    assert client is not None
    assert model == "llama-3.3-70b-versatile"
    assert prov == "openai"
