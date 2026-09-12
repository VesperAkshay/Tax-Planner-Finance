"""
Unit tests for the Active Learning & Feedback Loop (Task 3.7).

Verifies feedback capture, PII sanitization, schema validation against canonical categories,
dataset combination, and gated retraining behavior.
"""

from pathlib import Path
import pandas as pd
import pytest

from app.categorization.feedback_loop import (
    CANONICAL_CATEGORIES,
    get_combined_training_data,
    load_user_feedback,
    record_user_feedback,
    retrain_model_with_feedback,
    sanitize_description_for_training,
)


def test_sanitize_description_pii():
    raw_desc = "  UPI/DR/9876543210/ram@okhdfc/Payment for groceries  123456789012  "
    sanitized = sanitize_description_for_training(raw_desc)

    # Check PII masking
    assert "9876543210" not in sanitized
    assert "XXXXXXXXXX" in sanitized
    assert "123456789012" not in sanitized
    assert "XXXXXXXXXXXX" in sanitized
    # Check leading/trailing and inner whitespace
    assert not sanitized.startswith(" ")
    assert not sanitized.endswith(" ")
    assert "  " not in sanitized


def test_record_user_feedback_valid(tmp_path: Path):
    feedback_csv = tmp_path / "user_feedback.csv"

    record = record_user_feedback(
        description="POS POORVIKA MOBILES ELECTRONICS CHENNAI",
        confirmed_category="Shopping",
        user_id=1,
        original_predicted_category="Transport",
        original_confidence=0.2625,
        feedback_csv_path=feedback_csv,
    )

    assert record["confirmed_category"] == "Shopping"
    assert record["user_id"] == 1
    assert feedback_csv.exists()

    df = load_user_feedback(feedback_csv)
    assert len(df) == 1
    assert df.iloc[0]["confirmed_category"] == "Shopping"
    assert df.iloc[0]["description"] == "POS POORVIKA MOBILES ELECTRONICS CHENNAI"


def test_record_user_feedback_invalid_category(tmp_path: Path):
    feedback_csv = tmp_path / "user_feedback.csv"

    with pytest.raises(ValueError, match="Invalid category"):
        record_user_feedback(
            description="UPI-BITCOIN-BUY",
            confirmed_category="Cryptocurrency",
            feedback_csv_path=feedback_csv,
        )


def test_record_user_feedback_empty_description(tmp_path: Path):
    feedback_csv = tmp_path / "user_feedback.csv"

    with pytest.raises(ValueError, match="cannot be empty"):
        record_user_feedback(
            description="   ",
            confirmed_category="Dining",
            feedback_csv_path=feedback_csv,
        )


def test_get_combined_training_data_override(tmp_path: Path):
    feedback_csv = tmp_path / "user_feedback.csv"

    # Add user correction for an existing or new description
    record_user_feedback(
        description="UPI/DR/778899001122/spencer@axis/Spencer Retail Store",
        confirmed_category="Groceries",
        feedback_csv_path=feedback_csv,
    )

    combined = get_combined_training_data(feedback_csv_path=feedback_csv)
    assert len(combined) >= 720

    # Ensure the confirmed category is present for Spencer Retail
    spencer_row = combined[combined["description"] == "UPI/DR/778899001122/spencer@axis/Spencer Retail Store"]
    assert not spencer_row.empty
    assert spencer_row.iloc[-1]["category"] == "Groceries"


def test_retrain_model_skips_when_insufficient_samples(tmp_path: Path):
    feedback_csv = tmp_path / "user_feedback.csv"
    # Create empty feedback file
    feedback_csv.touch()

    success, metrics = retrain_model_with_feedback(
        feedback_csv_path=feedback_csv,
        min_feedback_samples=10,
    )

    assert success is False
    assert metrics["status"] == "skipped"
    assert "Insufficient feedback" in metrics["reason"]


def test_retrain_model_with_feedback_gate(tmp_path: Path):
    feedback_csv = tmp_path / "user_feedback.csv"
    output_model = tmp_path / "retrained_model.joblib"

    # Seed 5 feedback samples (min_feedback_samples=5)
    samples = [
        ("POS POORVIKA MOBILES ELECTRONICS CHENNAI", "Shopping"),
        ("POS PRASADS IMAX HYDERABAD", "Entertainment"),
        ("UPI-HPCL LPG GAS CYLINDER-hpcl@okaxis-Cooking Gas Refill", "Utilities"),
        ("POS RELIANCE SMART POINT HSR LAYOUT", "Groceries"),
        ("UPI/DR/343945560192/boatlifestyle@hdfcbank/Imagine Boat Audio", "Shopping"),
    ]

    for desc, cat in samples:
        record_user_feedback(
            description=desc,
            confirmed_category=cat,
            feedback_csv_path=feedback_csv,
        )

    success, metrics = retrain_model_with_feedback(
        feedback_csv_path=feedback_csv,
        output_model_path=output_model,
        min_feedback_samples=5,
        validation_gate_accuracy=0.85,
    )

    assert success is True
    assert metrics["status"] == "deployed"
    assert metrics["accuracy"] >= 0.85
    assert output_model.exists()
