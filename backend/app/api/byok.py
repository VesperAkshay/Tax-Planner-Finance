"""
BYOK (Bring Your Own Key) Management and Validation API Router.

Enables users to provide their own API keys for:
- OpenRouter (Multi-model / free tiers)
- OpenAI (GPT-4o, GPT-4o-mini, o3-mini)
- Anthropic (Claude 3.5 Sonnet, Claude 3.5 Haiku)
- Google Gemini (Gemini 1.5 Flash, Gemini 1.5 Pro via OpenAI compatibility)
- Groq Cloud (Llama 3.3 70B, Llama 3.1 8B with high-speed inference)
- Custom / Local OpenAI-compatible (Ollama, vLLM, LocalAI)

Features:
- Encrypted storage at rest using AES-128-CBC Fernet with user-specific HKDF keys.
- Live probe validation endpoint measuring ping latency.
- Key masking to prevent plaintext secret exposure in API responses.
- Easy revocation reverting to system default tier.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.agent.crypto import decrypt_api_key, encrypt_api_key, mask_api_key
from app.api.auth import get_current_user
from app.database import get_db_session
from app.models.common import get_utc_now
from app.models.user import User
from app.models.user_llm_key import UserLLMKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/byok", tags=["BYOK (Bring Your Own Key)"])

# Canonical base URLs for supported providers
PROVIDER_BASE_URLS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "groq": "https://api.groq.com/openai/v1",
}

DEFAULT_MODELS = {
    "openrouter": "openrouter/free",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "gemini": "gemini-1.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "custom": "default",
}


# ==============================================================================
# Pydantic Schemas
# ==============================================================================


class BYOKValidateRequest(BaseModel):
    provider: str = Field(..., description="Provider: openrouter, openai, anthropic, gemini, groq, custom")
    api_key: str = Field(..., min_length=4, description="API key to validate")
    model_name: Optional[str] = Field(None, description="Model identifier to test")
    custom_base_url: Optional[str] = Field(None, description="Custom base URL for custom provider or proxies")


class BYOKValidateResponse(BaseModel):
    valid: bool
    provider: str
    model_name: str
    latency_ms: Optional[int] = None
    message: str
    error: Optional[str] = None


class BYOKSaveRequest(BaseModel):
    provider: str = Field(..., description="Provider: openrouter, openai, anthropic, gemini, groq, custom")
    api_key: str = Field(..., min_length=4, description="API key to store encrypted")
    model_name: Optional[str] = Field(None, description="Model identifier to use")
    custom_base_url: Optional[str] = Field(None, description="Custom base URL if applicable")
    validate_before_save: bool = Field(True, description="Whether to probe key before saving")


class BYOKStatusResponse(BaseModel):
    has_key: bool
    provider: Optional[str] = None
    model_name: Optional[str] = None
    masked_key: Optional[str] = None
    custom_base_url: Optional[str] = None
    is_active: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ==============================================================================
# Probe Validation Helper
# ==============================================================================


def probe_provider_key(
    provider: str,
    api_key: str,
    model_name: Optional[str] = None,
    custom_base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Dispatches a minimal 1-token probe request to verify the validity of the user's API key.
    Measures latency in milliseconds.
    """
    clean_provider = provider.strip().lower()
    chosen_model = model_name.strip() if model_name and model_name.strip() else DEFAULT_MODELS.get(clean_provider, "gpt-4o-mini")
    t0 = time.perf_counter()

    try:
        if clean_provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key.strip())
            client.messages.create(
                model=chosen_model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
        else:
            from openai import OpenAI
            base_url = custom_base_url.strip() if custom_base_url and custom_base_url.strip() else PROVIDER_BASE_URLS.get(clean_provider)
            default_headers = {}
            if clean_provider == "openrouter":
                default_headers = {
                    "HTTP-Referer": "http://localhost:5173",
                    "X-Title": "Personal Finance Tax Regime Planner",
                }

            client = OpenAI(
                api_key=api_key.strip(),
                base_url=base_url,
                default_headers=default_headers if default_headers else None,
            )
            client.chat.completions.create(
                model=chosen_model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )

        latency_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "valid": True,
            "latency_ms": latency_ms,
            "message": f"Successfully authenticated with {provider.upper()} ({latency_ms}ms latency).",
            "model_name": chosen_model,
            "error": None,
        }

    except Exception as e:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        err_str = str(e)
        # Parse common provider error messages cleanly
        if "401" in err_str or "unauthorized" in err_str.lower() or "invalid api key" in err_str.lower():
            friendly_err = "Authentication failed: Invalid API key."
        elif "429" in err_str or "quota" in err_str.lower() or "rate limit" in err_str.lower():
            friendly_err = "Rate limit or quota exceeded on your API account."
        elif "404" in err_str or "model" in err_str.lower():
            friendly_err = f"Model '{chosen_model}' was not found or is not accessible with this key."
        else:
            friendly_err = f"Connection failed: {err_str[:200]}"

        logger.warning("BYOK probe failed for provider %s: %s", clean_provider, err_str)
        return {
            "valid": False,
            "latency_ms": latency_ms,
            "message": "Connection verification failed.",
            "model_name": chosen_model,
            "error": friendly_err,
        }


# ==============================================================================
# Router Endpoints
# ==============================================================================


@router.post("/validate", response_model=BYOKValidateResponse)
def validate_user_key(payload: BYOKValidateRequest) -> BYOKValidateResponse:
    """
    Test a candidate API key against the specified provider without saving it.
    Returns latency, validation status, and actionable error descriptions.
    """
    result = probe_provider_key(
        provider=payload.provider,
        api_key=payload.api_key,
        model_name=payload.model_name,
        custom_base_url=payload.custom_base_url,
    )
    return BYOKValidateResponse(
        valid=result["valid"],
        provider=payload.provider.lower(),
        model_name=result["model_name"],
        latency_ms=result["latency_ms"],
        message=result["message"],
        error=result["error"],
    )


@router.post("", response_model=BYOKStatusResponse)
def save_user_byok_key(
    payload: BYOKSaveRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> BYOKStatusResponse:
    """
    Encrypts and persists the user's personal API key in the database vault.
    Optionally validates the key live prior to saving.
    """
    clean_provider = payload.provider.strip().lower()
    clean_model = payload.model_name.strip() if payload.model_name and payload.model_name.strip() else DEFAULT_MODELS.get(clean_provider, "gpt-4o-mini")
    clean_base_url = payload.custom_base_url.strip() if payload.custom_base_url and payload.custom_base_url.strip() else None

    if payload.validate_before_save:
        probe_res = probe_provider_key(
            provider=clean_provider,
            api_key=payload.api_key,
            model_name=clean_model,
            custom_base_url=clean_base_url,
        )
        if not probe_res["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Key validation failed: {probe_res['error']}",
            )

    # Encrypt raw key using authenticated AES-128 Fernet tied to this user_id
    encrypted_key = encrypt_api_key(payload.api_key, current_user.id)

    # Upsert existing active key record for this user
    existing_key = session.exec(
        select(UserLLMKey).where(UserLLMKey.user_id == current_user.id)
    ).first()

    now = get_utc_now()
    if existing_key:
        existing_key.provider = clean_provider
        existing_key.model_name = clean_model
        existing_key.custom_base_url = clean_base_url
        existing_key.encrypted_key = encrypted_key
        existing_key.is_active = True
        existing_key.updated_at = now
        session.add(existing_key)
        saved_record = existing_key
    else:
        saved_record = UserLLMKey(
            user_id=current_user.id,
            provider=clean_provider,
            model_name=clean_model,
            custom_base_url=clean_base_url,
            encrypted_key=encrypted_key,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        session.add(saved_record)

    session.commit()
    session.refresh(saved_record)

    return BYOKStatusResponse(
        has_key=True,
        provider=saved_record.provider,
        model_name=saved_record.model_name,
        masked_key=mask_api_key(payload.api_key),
        custom_base_url=saved_record.custom_base_url,
        is_active=saved_record.is_active,
        created_at=saved_record.created_at.isoformat(),
        updated_at=saved_record.updated_at.isoformat(),
    )


@router.get("", response_model=BYOKStatusResponse)
def get_user_byok_status(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> BYOKStatusResponse:
    """
    Returns the current BYOK configuration for the authenticated user.
    The raw API key is never returned; only the masked string is exposed.
    """
    key_record = session.exec(
        select(UserLLMKey)
        .where(UserLLMKey.user_id == current_user.id)
        .where(UserLLMKey.is_active == True)
    ).first()

    if not key_record:
        return BYOKStatusResponse(has_key=False, is_active=False)

    try:
        decrypted_raw = decrypt_api_key(key_record.encrypted_key, current_user.id)
        masked = mask_api_key(decrypted_raw)
    except Exception as e:
        logger.error("Failed to decrypt stored key for user %s: %s", current_user.id, e)
        masked = "••••••••"

    return BYOKStatusResponse(
        has_key=True,
        provider=key_record.provider,
        model_name=key_record.model_name,
        masked_key=masked,
        custom_base_url=key_record.custom_base_url,
        is_active=key_record.is_active,
        created_at=key_record.created_at.isoformat(),
        updated_at=key_record.updated_at.isoformat(),
    )


@router.delete("")
def delete_user_byok_key(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> Dict[str, Any]:
    """
    Deletes the user's stored BYOK credentials, immediately reverting
    their account to the server's default fallback tier.
    """
    records = session.exec(
        select(UserLLMKey).where(UserLLMKey.user_id == current_user.id)
    ).all()

    for r in records:
        session.delete(r)

    session.commit()
    return {
        "success": True,
        "message": "Custom API key removed from your vault. Reverted to system AI tier.",
    }
