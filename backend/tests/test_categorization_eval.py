"""
Automated unit and integration tests for Categorization Evaluation & Holdout Report (Task 3.5).

Verifies holdout metrics calculation, 12x12 confusion matrix generation,
per-category precision/recall/F1, and report file generation at backend/tests/categorization_eval_report.md.
"""

from pathlib import Path
import numpy as np
import pytest

from app.categorization.evaluator import (
    DEFAULT_REPORT_PATH,
    compute_holdout_metrics,
    generate_categorization_eval_report,
)


def test_compute_holdout_metrics_structure():
    classes = ["Dining", "Groceries", "Transport"]
    y_true = ["Dining", "Dining", "Groceries", "Transport", "Groceries"]
    y_pred = ["Dining", "Transport", "Groceries", "Transport", "Groceries"]
    descriptions = ["restaurant", "cafe", "store", "uber", "supermarket"]
    probs = np.array([
        [0.8, 0.1, 0.1],
        [0.3, 0.2, 0.5],
        [0.05, 0.9, 0.05],
        [0.1, 0.1, 0.8],
        [0.1, 0.8, 0.1],
    ])

    metrics = compute_holdout_metrics(
        y_true=y_true,
        y_pred=y_pred,
        classes=classes,
        probabilities=probs,
        descriptions=descriptions,
    )

    assert metrics["accuracy"] == 0.8  # 4 / 5
    assert "macro_f1" in metrics
    assert "per_category" in metrics
    assert len(metrics["classes"]) == 3
    assert len(metrics["confusion_matrix"]) == 3
    assert len(metrics["misclassified"]) == 1
    assert metrics["misclassified"][0]["true_category"] == "Dining"
    assert metrics["misclassified"][0]["predicted_category"] == "Transport"
    assert metrics["misclassified"][0]["confidence"] == 0.5


def test_generate_categorization_eval_report_custom_path(tmp_path: Path):
    custom_report = tmp_path / "test_categorization_eval_report.md"
    markdown_content, summary = generate_categorization_eval_report(report_path=custom_report)

    assert custom_report.exists()
    assert custom_report.stat().st_size > 500

    # Verify key sections exist in markdown
    assert "# ML Transaction Categorization Pipeline — Holdout Evaluation Report" in markdown_content
    assert "Executive Summary & Model Comparison" in markdown_content
    assert "Per-Category Performance Breakdown" in markdown_content
    assert "Full 12x12 Confusion Matrix" in markdown_content
    assert "In-Depth Error Analysis" in markdown_content
    assert "Confidence Thresholding Specification" in markdown_content

    # Summary structure
    assert summary["dataset_size"] == 720
    assert summary["test_size"] == 144
    assert summary["train_size"] == 576
    assert summary["logistic_regression"]["accuracy"] >= 0.85
    assert summary["logistic_regression"]["macro_f1"] >= 0.85


def test_holdout_evaluation_metrics_and_gates():
    markdown_content, summary = generate_categorization_eval_report()

    lr_summary = summary["logistic_regression"]
    xgb_summary = summary["xgboost"]

    # Gate verification
    assert lr_summary["accuracy"] >= 0.85, f"Expected accuracy >= 0.85, got {lr_summary['accuracy']}"
    assert lr_summary["macro_f1"] >= 0.85, f"Expected macro F1 >= 0.85, got {lr_summary['macro_f1']}"

    # Verify Logistic Regression outperforms XGBoost on dense embeddings
    assert lr_summary["accuracy"] > xgb_summary["accuracy"]
    assert lr_summary["macro_f1"] > xgb_summary["macro_f1"]


def test_confusion_matrix_dimensions_and_support():
    report_file = DEFAULT_REPORT_PATH
    assert report_file.exists(), f"Expected report at {report_file}"
    content = report_file.read_text(encoding="utf-8")

    # Confirm all 12 categories appear in the confusion matrix and report
    expected_categories = [
        "Dining",
        "Entertainment",
        "Groceries",
        "Medical",
        "Miscellaneous",
        "Rent",
        "Salary Credit",
        "Self-Transfer",
        "Shopping",
        "Subscriptions",
        "Transport",
        "Utilities",
    ]

    for cat in expected_categories:
        assert cat in content, f"Expected category {cat} to be in the evaluation report"

    assert "Holdout Accuracy Gate" in content
    assert "PASSED" in content
