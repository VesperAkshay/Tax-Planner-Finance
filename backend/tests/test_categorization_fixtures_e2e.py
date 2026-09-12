"""
End-to-End Categorization Pipeline Tests on Phase 2 Test Fixtures (Task 3.8).

Runs the full categorization pipeline (embedding, inference, confidence thresholding,
and review flagging) on all parsed bank statement fixtures from Phase 2.
"""

from pathlib import Path
from typing import List, Tuple
import pytest

from app.categorization.categorizer import (
    DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD,
    UNCATEGORIZED_CATEGORY,
    CategorizationResult,
    TransactionCategorizer,
    get_transaction_categorizer,
)
from app.categorization.feedback_loop import CANONICAL_CATEGORIES
from app.parsing.csv_parser import CSVBankParser
from app.parsing.pdf_parser import DoclingPDFParser
from app.parsing.schemas import ParsedTransactionRow

FIXTURES_DIR = Path("data/test_fixtures")


@pytest.fixture(scope="module")
def categorizer() -> TransactionCategorizer:
    return get_transaction_categorizer()


@pytest.fixture(scope="module")
def csv_parser() -> CSVBankParser:
    return CSVBankParser()


@pytest.fixture(scope="module")
def pdf_parser() -> DoclingPDFParser:
    return DoclingPDFParser()


def test_categorization_on_all_bank_statement_fixtures(
    categorizer: TransactionCategorizer,
    csv_parser: CSVBankParser,
    pdf_parser: DoclingPDFParser,
):
    """
    Parses all Phase 2 bank statement fixtures and runs them through the categorization pipeline.
    Asserts valid categorization schemas, confidence bounds, and review flag consistency.
    """
    fixtures = [
        # CSV Statements
        ("CSV", FIXTURES_DIR / "sample_hdfc_statement.csv", csv_parser),
        ("CSV", FIXTURES_DIR / "sample_kotak_statement.csv", csv_parser),
        # Text PDF Statements
        ("PDF", FIXTURES_DIR / "sample_hdfc_statement.pdf", pdf_parser),
        ("PDF", FIXTURES_DIR / "sample_icici_statement.pdf", pdf_parser),
        ("PDF", FIXTURES_DIR / "sample_sbi_statement.pdf", pdf_parser),
    ]

    total_transactions = 0
    categorized_confident_count = 0
    uncategorized_review_count = 0
    all_results: List[Tuple[str, ParsedTransactionRow, CategorizationResult]] = []

    for f_type, fixture_path, parser in fixtures:
        assert fixture_path.exists(), f"Fixture {fixture_path} must exist"
        parse_result = parser.parse(fixture_path)
        assert len(parse_result.rows) > 0, f"Fixture {fixture_path.name} should have parsed rows"

        annotated_rows = categorizer.apply_to_parsed_rows(parse_result.rows)
        assert len(annotated_rows) == len(parse_result.rows)

        for row, cat_res in annotated_rows:
            total_transactions += 1
            all_results.append((fixture_path.name, row, cat_res))

            # 1. Category must be either a canonical category or "Uncategorized"
            valid_categories = CANONICAL_CATEGORIES + [UNCATEGORIZED_CATEGORY]
            assert cat_res.category in valid_categories, f"Invalid category: {cat_res.category}"

            # 2. Confidence must be in [0.0, 1.0]
            assert 0.0 <= cat_res.confidence <= 1.0

            # 3. If confidence < threshold, category MUST be Uncategorized and needs_review MUST be True
            if cat_res.confidence < DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD:
                assert cat_res.category == UNCATEGORIZED_CATEGORY
                assert cat_res.needs_review is True
                assert cat_res.is_thresholded is True
                assert row.needs_review is True
                uncategorized_review_count += 1
            else:
                # High-confidence classification
                assert cat_res.category in CANONICAL_CATEGORIES
                assert cat_res.is_thresholded is False
                categorized_confident_count += 1

    # Ensure all statement fixtures were processed
    assert total_transactions >= 25, f"Expected >= 25 transactions, processed {total_transactions}"
    assert categorized_confident_count > 0, "Expected at least some high-confidence categorized transactions"
    assert uncategorized_review_count > 0, "Expected low-confidence transactions routed to review"


def test_salary_and_rent_in_fixtures_correctly_categorized(
    categorizer: TransactionCategorizer,
    pdf_parser: DoclingPDFParser,
):
    """
    Specifically tests that critical salary credits and rent payments inside
    HDFC, ICICI, and SBI statements are categorized correctly with high confidence.
    """
    # Test HDFC Text PDF
    hdfc_pdf = FIXTURES_DIR / "sample_hdfc_statement.pdf"
    res = pdf_parser.parse(hdfc_pdf)
    annotated = categorizer.apply_to_parsed_rows(res.rows)

    salary_row = next((r for r, c in annotated if "SALARY" in r.description), None)
    assert salary_row is not None
    _, sal_res = next((r, c) for r, c in annotated if "SALARY" in r.description)
    assert sal_res.category == "Salary Credit"
    assert sal_res.confidence >= 0.85
    assert sal_res.needs_review is False

    rent_row = next((r for r, c in annotated if "RENT" in r.description), None)
    assert rent_row is not None
    _, rent_res = next((r, c) for r, c in annotated if "RENT" in r.description)
    assert rent_res.category == "Rent"
    assert rent_res.confidence >= 0.80
    assert rent_res.needs_review is False


def test_utilities_and_groceries_in_fixtures_categorized(
    categorizer: TransactionCategorizer,
    pdf_parser: DoclingPDFParser,
):
    """
    Tests that groceries (Natures Basket) and utilities (Electricity, Broadband)
    in the ICICI and SBI statements are categorized accurately.
    """
    # ICICI statement has Natures Basket and Bescom Electricity
    icici_pdf = FIXTURES_DIR / "sample_icici_statement.pdf"
    icici_res = pdf_parser.parse(icici_pdf)
    icici_annotated = categorizer.apply_to_parsed_rows(icici_res.rows)

    nb_row, nb_cat = next((r, c) for r, c in icici_annotated if "NATURES BASKET" in r.description)
    assert nb_cat.category == "Groceries"
    assert nb_cat.confidence >= 0.80

    bescom_row, bescom_cat = next((r, c) for r, c in icici_annotated if "BESCOM" in r.description)
    assert bescom_cat.category == "Utilities"
    assert bescom_cat.confidence >= 0.70

    # SBI statement has Airtel Broadband and Apollo Pharmacy
    sbi_pdf = FIXTURES_DIR / "sample_sbi_statement.pdf"
    sbi_res = pdf_parser.parse(sbi_pdf)
    sbi_annotated = categorizer.apply_to_parsed_rows(sbi_res.rows)

    airtel_row, airtel_cat = next((r, c) for r, c in sbi_annotated if "AIRTEL" in r.description)
    assert airtel_cat.category == "Utilities"
    assert airtel_cat.confidence >= 0.80

    apollo_row, apollo_cat = next((r, c) for r, c in sbi_annotated if "APOLLO" in r.description)
    assert apollo_cat.category == "Medical"
    assert apollo_cat.confidence >= 0.60
