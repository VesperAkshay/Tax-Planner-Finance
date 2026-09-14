"""
Automated unit tests for Tax Rules RAG Layer Retrieval (Task 6.4).

Tests semantic retrieval against 10 predefined tax planning questions:
1. "does home loan interest count?" -> Section 24(b)
2. "80D limit for parents?" -> 80D
3. "what is the maximum 80C deduction limit?" -> 80C
4. "can I claim NPS contribution under 80CCD 1B?" -> 80CCD(1B)
5. "cash donation limit for tax deduction under 80G" -> 80G
6. "how is HRA exemption calculated for metro cities?" -> Section 10(13A)
7. "marginal relief under section 87A for new regime" -> Section 87A
8. "standard deduction for salaried employees FY 2025-26" -> Standard Deduction
9. "preventive health checkup deduction limit under 80D" -> 80D
10. "children school tuition fees tax deduction" -> 80C

Asserts that top result's section and source_url match expectations.
"""

from pathlib import Path
import pytest

from app.rag.retriever import (
    DEFAULT_CORPUS_PATH,
    TaxRAGService,
)

SAMPLE_TEST_QUERIES = [
    {
        "query": "does home loan interest count?",
        "expected_section": "Section 24(b)",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=24",
    },
    {
        "query": "80D limit for parents?",
        "expected_section": "80D",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80D",
    },
    {
        "query": "what is the maximum 80C deduction limit?",
        "expected_section": "80C",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80C",
    },
    {
        "query": "can I claim NPS contribution under 80CCD 1B?",
        "expected_section": "80CCD(1B)",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80CCD",
    },
    {
        "query": "cash donation limit for tax deduction under 80G",
        "expected_section": "80G",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80G",
    },
    {
        "query": "how is HRA exemption calculated for metro cities?",
        "expected_section": "Section 10(13A)",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=10(13A)",
    },
    {
        "query": "marginal relief under section 87A for new regime",
        "expected_section": "Section 87A",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=87A",
    },
    {
        "query": "standard deduction for salaried employees FY 2025-26",
        "expected_section": "Standard Deduction",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=16",
    },
    {
        "query": "preventive health checkup deduction limit under 80D",
        "expected_section": "80D",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80D",
    },
    {
        "query": "children school tuition fees tax deduction",
        "expected_section": "80C",
        "expected_source_url": "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx?section=80C",
    },
]


@pytest.fixture(scope="module")
def rag_service(tmp_path_factory):
    """Initializes a temporary isolated ChromaDB store and indexes the corpus once."""
    test_db_dir = tmp_path_factory.mktemp("chroma_test_db")
    service = TaxRAGService(
        chroma_dir=test_db_dir,
        collection_name="test_tax_rules_fy_2025_26",
    )
    count = service.index_corpus(DEFAULT_CORPUS_PATH, force_reindex=True)
    assert count >= 10, f"Expected at least 10 chunks indexed, got {count}"
    return service


@pytest.mark.parametrize("test_case", SAMPLE_TEST_QUERIES, ids=[tc["query"] for tc in SAMPLE_TEST_QUERIES])
def test_retrieval_against_10_sample_queries(rag_service, test_case):
    """
    Task 6.4: Asserts that top-1 retrieved chunk matches expected section and source_url.
    """
    query = test_case["query"]
    expected_sec = test_case["expected_section"]
    expected_url = test_case["expected_source_url"]

    results = rag_service.retrieve(query=query, top_k=3)
    assert len(results) >= 1, f"No results retrieved for query: '{query}'"

    top = results[0]
    assert top["section"] == expected_sec, (
        f"Section mismatch for '{query}': expected '{expected_sec}', got '{top['section']}' (Title: {top['title']})"
    )
    assert top["source_url"] == expected_url, (
        f"URL mismatch for '{query}': expected '{expected_url}', got '{top['source_url']}'"
    )
    assert top["similarity_score"] > 0.30, (
        f"Low similarity score for '{query}': {top['similarity_score']}"
    )


def test_section_filtering(rag_service):
    """Tests metadata filtering by section."""
    results = rag_service.retrieve(
        query="tax deductions",
        top_k=5,
        section_filter="80D",
    )
    assert len(results) >= 1
    for r in results:
        assert r["section"] == "80D"


def test_regime_filtering(rag_service):
    """Tests metadata filtering by regime applicability."""
    results = rag_service.retrieve(
        query="rebate and relief",
        top_k=5,
        regime_filter="new",
    )
    assert len(results) >= 1
    for r in results:
        assert r["regime_applicability"] in ["new", "both"]
