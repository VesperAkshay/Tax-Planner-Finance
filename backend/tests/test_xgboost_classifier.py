"""
Unit tests for Task 3.4: XGBoost Classifier and Comparison with Baseline.
"""

from pathlib import Path
import numpy as np
import pytest

from app.categorization.embedder import get_transaction_embedder
from app.categorization.xgboost_classifier import (
    DEFAULT_XGBOOST_MODEL_PATH,
    XGBoostTransactionClassifier,
    compare_logistic_vs_xgboost,
    get_trained_xgboost_classifier,
    train_xgboost_classifier,
)
from app.seed_categories import SEED_CATEGORIES

CANONICAL_CATEGORIES = {c["name"] for c in SEED_CATEGORIES}


def test_train_xgboost_classifier_metrics():
    """Verify XGBoost classifier achieves >= 75% accuracy and macro F1 on 20% holdout split."""
    clf, metrics = train_xgboost_classifier(test_size=0.2, random_state=42)

    assert "holdout_accuracy" in metrics
    assert "macro_f1" in metrics
    assert "weighted_f1" in metrics
    assert metrics["train_samples"] == 576
    assert metrics["test_samples"] == 144

    # Performance benchmark check
    assert metrics["holdout_accuracy"] >= 0.75, f"XGBoost accuracy too low: {metrics['holdout_accuracy']}"
    assert metrics["macro_f1"] >= 0.75, f"XGBoost macro F1 too low: {metrics['macro_f1']}"

    # Verify all 12 classes exist in classifier
    assert len(clf.classes_) == 12
    for cat in CANONICAL_CATEGORIES:
        assert cat in clf.classes_


def test_xgboost_predict_and_proba_distributions():
    """Verify XGBoost predictions and probability distributions are valid."""
    clf = get_trained_xgboost_classifier()
    embedder = get_transaction_embedder()

    sample_queries = [
        "UPI-SWIGGY-swiggy@icici-Food Delivery",
        "ACH/CREDIT/TCS LIMITED/SALARY CREDIT JUNE 2025",
        "TRANSFER TO OWN ACCOUNT 501009876543 HDFC",
    ]
    embs = embedder.embed(sample_queries)

    preds = clf.predict(embs)
    assert len(preds) == 3
    for p in preds:
        assert p in CANONICAL_CATEGORIES
        assert isinstance(p, str)

    assert preds[0] == "Dining"
    assert preds[1] == "Salary Credit"
    assert preds[2] == "Self-Transfer"

    probs = clf.predict_proba(embs)
    assert probs.shape == (3, 12)
    for row in probs:
        assert abs(float(np.sum(row)) - 1.0) < 1e-4


def test_xgboost_predict_with_confidence():
    """Verify predict_with_confidence returns category string and probability in [0, 1]."""
    clf = get_trained_xgboost_classifier()

    queries = [
        "NEFT-RENT PAYMENT TO LANDLORD SANJAY",
        "ATM CASH WDL HDFC BANK ATM",
    ]
    results = clf.predict_with_confidence(queries)
    assert len(results) == 2

    for category, conf in results:
        assert isinstance(category, str)
        assert category in CANONICAL_CATEGORIES
        assert 0.0 <= conf <= 1.0

    assert results[0][0] == "Rent"
    assert results[0][1] > 0.75


def test_xgboost_serialization_and_deserialization(tmp_path: Path):
    """Verify XGBoost model can be saved and reloaded with identical predictions."""
    clf = get_trained_xgboost_classifier()
    save_path = tmp_path / "test_xgb.joblib"

    # Save
    saved_p = clf.save(save_path)
    assert saved_p.exists()

    # Load
    loaded_clf = XGBoostTransactionClassifier.load(save_path)
    assert loaded_clf.classes_ == clf.classes_

    # Verify predictions match
    embedder = get_transaction_embedder()
    test_vec = embedder.embed("POS ZARA PHOENIX MARKETCITY BANGALORE")

    p1 = clf.predict(test_vec)
    p2 = loaded_clf.predict(test_vec)
    assert p1 == p2 == ["Shopping"]

    prob1 = clf.predict_proba(test_vec)
    prob2 = loaded_clf.predict_proba(test_vec)
    assert np.allclose(prob1, prob2, atol=1e-5)


def test_compare_logistic_vs_xgboost():
    """Verify side-by-side comparison of Logistic Regression vs XGBoost (Task 3.4 requirement)."""
    comp = compare_logistic_vs_xgboost(test_size=0.2, random_state=42)

    assert "logistic_regression" in comp
    assert "xgboost" in comp
    assert "winner" in comp
    assert "difference_accuracy" in comp

    lr_acc = comp["logistic_regression"]["accuracy"]
    xgb_acc = comp["xgboost"]["accuracy"]

    assert lr_acc >= 0.85
    assert xgb_acc >= 0.75
    assert comp["winner"] in ("logistic_regression", "xgboost")
