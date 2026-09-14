"""
Unit tests for Task 6.1 - Tax Rules Rule-Text Corpus validation.

Verifies:
1. Corpus file exists at data/rag/tax_rules_corpus_fy_2025_26.json.
2. Covers all mandatory sections: 80C, 80D, 80CCD(1B), 80G, Section 24b, HRA, 87A, Standard Deduction.
3. Every chunk contains mandatory metadata: id, section, title, content, financial_year, source_url.
4. Correct financial year 2025-2026 and valid government source URLs.
"""

import json
from pathlib import Path
import pytest

CORPUS_PATH = Path("data/rag/tax_rules_corpus_fy_2025_26.json")


def test_corpus_file_exists():
    assert CORPUS_PATH.exists(), f"Corpus file not found at {CORPUS_PATH}"


def test_corpus_schema_and_required_sections():
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["financial_year"] == "2025-2026"
    assert "chunks" in data
    chunks = data["chunks"]
    assert len(chunks) >= 8, f"Expected at least 8 chunks, found {len(chunks)}"

    required_sections = {
        "80C",
        "80D",
        "80CCD(1B)",
        "80G",
        "Section 24(b)",
        "Section 10(13A)",
        "Section 87A",
        "Standard Deduction",
    }

    present_sections = {chunk["section"] for chunk in chunks}
    missing = required_sections - present_sections
    assert not missing, f"Missing required sections in corpus: {missing}"

    for chunk in chunks:
        assert chunk["id"], "Chunk missing id"
        assert chunk["section"], f"Chunk {chunk['id']} missing section"
        assert chunk["title"], f"Chunk {chunk['id']} missing title"
        assert len(chunk["content"]) > 100, f"Chunk {chunk['id']} content too short"
        assert chunk["financial_year"] == "2025-2026", f"Chunk {chunk['id']} invalid FY"
        assert chunk["source_url"].startswith("https://incometaxindia.gov.in/"), f"Chunk {chunk['id']} invalid source_url"
        assert isinstance(chunk.get("tags"), list), f"Chunk {chunk['id']} tags must be a list"
