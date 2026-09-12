"""
Unit tests for Task 3.3: Baseline Logistic Regression Classifier.
"""

from pathlib import Path
import numpy as np
import pytest

from app.categorization.embedder import get_transaction_embedder
from app.categorization.logistic_classifier import (
    DEFAULT_MODEL_PATH,
    LogisticRegressionClassifier,
    get_trained_logistic_classifier,
    train_baseline_logistic,
)
from app.seed_categories import SEED_CATEGORIES

CANONICAL_CATEGORIES = {c["name"] for c in SEED_CATEGORIES}


def test_train_baseline_logistic_metrics():
    """Verify Logistic Regression training achieves > 85% accuracy and macro F1 on 20% holdout."""
    clf, metrics = train_baseline_logistic(test_size=0.2, random_state=42)

    assert "holdout_accuracy" in metrics
    assert "macro_f1" in metrics
    assert "weighted_f1" in metrics
    assert metrics["train_samples"] == 576
    assert metrics["test_samples"] == 144

    # Verification threshold: must exceed 85% holdout accuracy
    assert metrics["holdout_accuracy"] >= 0.85, f"Holdout accuracy too low: {metrics['holdout_accuracy']}"
    assert metrics["macro_f1"] >= 0.85, f"Macro F1 too low: {metrics['macro_f1']}"

    # Verify all 12 classes exist in classifier
    assert len(clf.classes_) == 12
    for cat in CANONICAL_CATEGORIES:
        assert cat in clf.classes_


def test_predict_and_predict_proba_shapes():
    """Verify prediction and probability distributions have proper shapes and sums."""
    clf = get_trained_logistic_classifier()
    embedder = get_transaction_embedder()

    sample_queries = [
        "UPI-SWIGGY-swiggy@icici-Food Delivery",
        "SALARY CREDIT INFOSYS LIMITED",
        "TRANSFER TO OWN ACCOUNT 501009876543 HDFC",
    ]
    embs = embedder.embed(sample_queries)

    # Predictions
    preds = clf.predict(embs)
    assert len(preds) == 3
    for p in preds:
        assert p in CANONICAL_CATEGORIES

    # Expected top categories
    assert preds[0] == "Dining"
    assert preds[1] == "Salary Credit"
    assert preds[2] == "Self-Transfer"

    # Probabilities
    probs = clf.predict_proba(embs)
    assert probs.shape == (3, 12)
    # Each row must sum to 1.0 (valid probability distribution)
    for row in probs:
        assert abs(float(np.sum(row)) - 1.0) < 1e-4


def test_predict_with_confidence():
    """Verify predict_with_confidence returns category and probability in [0, 1]."""
    clf = get_trained_logistic_classifier()

    queries = [
        "NEFT-RENT PAYMENT TO LANDLORD SANJAY",
        "ATM CASH WDL HDFC BANK ATM",
        "UPI/DR/12345/bescom@billdesk/Electricity Bill",
    ]
    results = clf.predict_with_confidence(queries)
    assert len(results) == 3

    for category, conf in results:
        assert category in CANONICAL_CATEGORIES
        assert 0.0 <= conf <= 1.0

    assert results[0][0] == "Rent"
    assert results[0][1] > 0.80  # high confidence for clear rent narration

    assert results[1][0] == "Miscellaneous"
    assert results[2][0] == "Utilities"


def test_model_serialization_and_deserialization(tmp_path: Path):
    """Verify model can be saved to disk and loaded with exact identical predictions."""
    clf = get_trained_logistic_classifier()
    save_path = tmp_path / "test_lr.joblib"

    # Save model
    saved_p = clf.save(save_path)
    assert saved_p.exists()

    # Load model
    loaded_clf = LogisticRegressionClassifier.load(save_path)
    assert loaded_clf.classes_ == clf.classes_

    # Verify predictions on new test vector match exactly
    embedder = get_transaction_embedder()
    test_vec = embedder.embed("POS ZARA PHOENIX MARKETCITY BANGALORE")

    p1 = clf.predict(test_vec)
    p2 = loaded_clf.predict(test_vec)
    assert p1 == p2 == ["Shopping"]

    prob1 = clf.predict_proba(test_vec)
    prob2 = loaded_clf.predict_proba(test_vec)
    assert np.allclose(prob1, prob2, atol=1e-5)
