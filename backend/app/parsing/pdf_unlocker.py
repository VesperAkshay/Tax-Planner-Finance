"""
PDF Encryption Detection and In-Memory Decryption Service.
Enables password unlocking for bank statements and salary slips (Tasks 16.2 & Unified Ingestion).
"""

import io
from pathlib import Path
from typing import Optional, Tuple, Union
from pypdf import PdfReader, PdfWriter


class PDFPasswordRequiredError(Exception):
    """Raised when a PDF is encrypted and no password was provided."""
    pass


class PDFInvalidPasswordError(Exception):
    """Raised when the provided password fails to decrypt the PDF."""
    pass


def is_pdf_encrypted(content: bytes) -> bool:
    """Checks if raw PDF bytes contain encryption dictionaries and require a password."""
    if b"/Encrypt" not in content:
        return False
    try:
        reader = PdfReader(io.BytesIO(content))
        return bool(reader.is_encrypted)
    except Exception:
        return False


def decrypt_pdf_in_memory(content: bytes, password: Optional[str] = None) -> Tuple[bytes, bool]:
    """
    Checks if a PDF is encrypted and decrypts it into memory if a valid password is provided.
    Returns:
        (decrypted_bytes, was_encrypted)
    Raises:
        PDFPasswordRequiredError: if the file is encrypted and no password was supplied.
        PDFInvalidPasswordError: if the password supplied is incorrect.
    """
    if b"/Encrypt" not in content:
        return content, False

    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception:
        return content, False

    if not reader.is_encrypted:
        return content, False

    if not password or not password.strip():
        raise PDFPasswordRequiredError("This PDF document is password-protected. Please provide the password to unlock it.")

    # Attempt decryption
    clean_password = password.strip()
    decrypt_result = reader.decrypt(clean_password)
    # In pypdf, decrypt returns 0 if failed, 1 (user password) or 2 (owner password) if successful
    if decrypt_result == 0:
        raise PDFInvalidPasswordError("Incorrect password for this PDF document. Please verify and try again.")

    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    return output_stream.getvalue(), True
