"""
Unit tests for Confidence Thresholding in ML Categorization (Task 3.6).

Tests that predictions below DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD set
category = "Uncategorized" and needs_review = True, while predictions above
preserve the predicted category.
"""

from datetime import date
import pytest

from app.categorization.categorizer import (
    DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD,
    UNCATEGORIZED_CATEGORY,
    CategorizationResult,
    TransactionCategorizer,
    get_transaction_categorizer,
)
from app.parsing.schemas import ParsedTransactionRow


@pytest.fixture(scope="module")
def categorizer() -> TransactionCategorizer:
    return get_transaction_categorizer()


def test_high_confidence_prediction_preserves_category(categorizer: TransactionCategorizer):
    """
    Transactions with unambiguous keywords should achieve confidence >= 0.60
    and retain their predicted category with needs_review = False.
    """
    narration = "UPI-SWIGGY-swiggy@icici-Order Food Bangalore"
    result = categorizer.categorize(narration)

    assert result.category == "Dining"
    assert result.raw_predicted_category == "Dining"
    assert result.confidence >= DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD
    assert result.needs_review is False
    assert result.is_thresholded is False
    assert result.threshold == DEFAULT_CATEGORIZATION_CONFIDENCE_THRESHOLD


def test_salary_and_rent_high_confidence(categorizer: TransactionCategorizer):
    """
    Critical transactions (Salary, Rent) should categorize confidently without review flag.
    """
    salary_narration = "ACH/SALARY CREDIT/TECHCORP INDIA PVT LTD/OCT 2025"
    sal_result = categorizer.categorize(salary_narration)
    assert sal_result.category == "Salary Credit"
    assert sal_result.confidence >= 0.80
    assert sal_result.needs_review is False

    rent_narration = "NEFT-RENT PAYMENT FOR FLAT 402-HDFC0001234"
    rent_result = categorizer.categorize(rent_narration)
    assert rent_result.category == "Rent"
    assert rent_result.confidence >= 0.80
    assert rent_result.needs_review is False


def test_low_confidence_forces_uncategorized_and_needs_review(categorizer: TransactionCategorizer):
    """
    Ambiguous, random, or low-probability descriptions should fall below threshold
    (or when evaluated against an elevated threshold) resulting in Uncategorized and needs_review = True.
    """
    # Extremely strict threshold forces thresholding
    ambiguous_narration = "POS MISC TXN 98734298 REF 00129"
    result = categorizer.categorize(ambiguous_narration, threshold=0.99)

    assert result.category == UNCATEGORIZED_CATEGORY
    assert result.needs_review is True
    assert result.is_thresholded is True
    assert result.threshold == 0.99
    # The underlying raw prediction is preserved for debugging
    assert result.raw_predicted_category != UNCATEGORIZED_CATEGORY


def test_empty_or_whitespace_narration(categorizer: TransactionCategorizer):
    """
    Empty strings or whitespace should safely map to Uncategorized with confidence 0.0 and needs_review = True.
    """
    empty_result = categorizer.categorize("   ")
    assert empty_result.category == UNCATEGORIZED_CATEGORY
    assert empty_result.confidence == 0.0
    assert empty_result.needs_review is True
    assert empty_result.is_thresholded is True


def test_batch_categorization(categorizer: TransactionCategorizer):
    """
    Tests batch categorization across multiple distinct narrations.
    """
    narrations = [
        "UPI-UBER-uber.rides@hdfcbank-Trip to Airport",
        "UPI-NETFLIX-netflix@icici-Monthly Subscription",
        "NEFT CR-SALARY FOR NOVEMBER-TECH CORP",
    ]
    results = categorizer.categorize_batch(narrations)

    assert len(results) == 3
    assert results[0].category == "Transport"
    assert results[0].needs_review is False
    assert results[1].category == "Subscriptions"
    assert results[1].needs_review is False
    assert results[2].category == "Salary Credit"
    assert results[2].needs_review is False


def test_apply_to_parsed_row_preserves_and_updates_review_flag(categorizer: TransactionCategorizer):
    """
    Tests application to ParsedTransactionRow.
    If parse had needs_review=True, it stays True.
    If categorization is low confidence, needs_review becomes True.
    """
    # Case 1: High parse confidence + High categorization confidence -> needs_review = False
    row1 = ParsedTransactionRow(
        date=date(2025, 8, 15),
        description="UPI-BIGBASKET-bigbasket@bbdaily-Organic Vegetables",
        amount=1250.0,
        transaction_type="debit",
        parse_confidence=0.98,
        needs_review=False,
    )
    updated_row1, res1 = categorizer.apply_to_parsed_row(row1)
    assert res1.category == "Groceries"
    assert updated_row1.needs_review is False

    # Case 2: Low parse confidence (needs_review=True from parser) -> remains needs_review=True
    row2 = ParsedTransactionRow(
        date=date(2025, 8, 15),
        description="UPI-SWIGGY-swiggy@icici-Order Food",
        amount=450.0,
        transaction_type="debit",
        parse_confidence=0.70,  # Below DEFAULT_REVIEW_THRESHOLD (0.85), so needs_review initialized True
    )
    assert row2.needs_review is True
    updated_row2, res2 = categorizer.apply_to_parsed_row(row2)
    assert res2.category == "Dining"
    assert updated_row2.needs_review is True  # Persisted from parser

    # Case 3: High parse confidence but low categorization confidence -> becomes needs_review=True
    row3 = ParsedTransactionRow(
        date=date(2025, 8, 15),
        description="POS STORE 987342",
        amount=300.0,
        transaction_type="debit",
        parse_confidence=0.99,
        needs_review=False,
    )
    # Applying with high threshold forces review
    updated_row3, res3 = categorizer.apply_to_parsed_row(row3, threshold=0.99)
    assert res3.category == UNCATEGORIZED_CATEGORY
    assert res3.is_thresholded is True
    assert updated_row3.needs_review is True


def test_apply_to_parsed_rows_batch(categorizer: TransactionCategorizer):
    """
    Tests batch application to a list of ParsedTransactionRow objects.
    """
    rows = [
        ParsedTransactionRow(
            date=date(2025, 9, 1),
            description="UPI-BESCOM-bescom@sbi-Electricity Bill Payment",
            amount=2150.0,
            transaction_type="debit",
            parse_confidence=0.96,
        ),
        ParsedTransactionRow(
            date=date(2025, 9, 2),
            description="POS APOLLO PHARMACY BANGALORE",
            amount=850.0,
            transaction_type="debit",
            parse_confidence=0.95,
        ),
    ]

    annotated = categorizer.apply_to_parsed_rows(rows)
    assert len(annotated) == 2
    assert annotated[0][1].category == "Utilities"
    assert annotated[1][1].category == "Medical"
    assert annotated[0][0].needs_review is False
    assert annotated[1][0].needs_review is False
