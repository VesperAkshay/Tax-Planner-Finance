"""
Cryptographic Security Layer for Bring Your Own Key (BYOK).

Implements:
1. Symmetric Authenticated Encryption (AES-128-CBC with HMAC-SHA256 via Fernet).
2. Per-User HKDF-SHA256 Key Derivation from server SECRET_KEY and user_id salt.
   Ensures that even if the database is compromised, ciphertext cannot be decrypted
   without both the server secret and the corresponding user ID.
3. Secure Key Masking for safe display in UI/API responses (e.g. 'sk-ant-••••••••abcd').
"""

import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import get_settings


def _derive_user_fernet_key(user_id: int) -> bytes:
    """
    Derives a 32-byte URL-safe base64-encoded Fernet key specific to a user
    using HKDF-SHA256 with the server SECRET_KEY as input keying material.
    """
    settings = get_settings()
    secret_bytes = settings.SECRET_KEY.encode("utf-8")
    salt = f"tax_planner_byok_salt_user_{user_id}".encode("utf-8")
    info = b"byok_symmetric_user_key_derivation"

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=info,
    )
    derived = hkdf.derive(secret_bytes)
    return base64.urlsafe_b64encode(derived)


def encrypt_api_key(raw_key: str, user_id: int) -> str:
    """
    Encrypts an API key for a specific user.
    Returns URL-safe base64-encoded ciphertext string.
    """
    if not raw_key or not raw_key.strip():
        raise ValueError("Cannot encrypt an empty API key")

    key = _derive_user_fernet_key(user_id)
    f = Fernet(key)
    ciphertext = f.encrypt(raw_key.strip().encode("utf-8"))
    return ciphertext.decode("utf-8")


def decrypt_api_key(ciphertext: str, user_id: int) -> str:
    """
    Decrypts an encrypted API key for a specific user.
    Returns the original plaintext API key.
    """
    if not ciphertext or not ciphertext.strip():
        raise ValueError("Cannot decrypt empty ciphertext")

    key = _derive_user_fernet_key(user_id)
    f = Fernet(key)
    plaintext_bytes = f.decrypt(ciphertext.strip().encode("utf-8"))
    return plaintext_bytes.decode("utf-8")


def mask_api_key(key: Optional[str]) -> str:
    """
    Safely masks an API key for display in API responses and frontend UI.
    Shows the first 6-8 prefix characters and last 4 suffix characters,
    with dots representing the middle payload.
    Example: 'sk-proj-1234567890abcdef' -> 'sk-proj-••••••••cdef'
    """
    if not key:
        return ""

    cleaned = key.strip()
    if len(cleaned) <= 8:
        return "••••••••"

    prefix_len = min(7, len(cleaned) // 3)
    suffix_len = min(4, len(cleaned) // 4)

    prefix = cleaned[:prefix_len]
    suffix = cleaned[-suffix_len:]
    return f"{prefix}••••••••{suffix}"
