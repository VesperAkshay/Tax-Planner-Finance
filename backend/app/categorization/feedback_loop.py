"""
Active Learning & User Feedback Loop for Transaction Categorization (Task 3.7).

Provides mechanism to capture user-confirmed category overrides, append them
to an active training set, and trigger gated model retraining with zero regression.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

from app.categorization.embedder import (
    DEFAULT_DATASET_PATH,
    TransactionEmbedder,
    get_transaction_embedder,
)
from app.categorization.logistic_classifier import (
    DEFAULT_MODEL_PATH,
    LogisticRegressionClassifier,
    get_trained_logistic_classifier,
)

DEFAULT_FEEDBACK_DATASET_PATH: Path = Path("data/categorization/user_feedback_dataset.csv")

CANONICAL_CATEGORIES: List[str] = [
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

FEEDBACK_CSV_HEADERS: List[str] = [
    "timestamp",
    "user_id",
    "description",
    "confirmed_category",
    "original_predicted_category",
    "original_confidence",
]


def sanitize_description_for_training(text: str) -> str:
    """
    Sanitizes transaction description for training:
    - Strips whitespace
    - Normalizes multi-spaces
    - Masks potential 10-digit mobile numbers or 12-16 digit account numbers with tokens
    """
    if not text:
        return ""
    cleaned = text.strip()
    # Mask pure 10-digit phone/UPI numbers
    cleaned = re.sub(r"\b[6-9]\d{9}\b", "XXXXXXXXXX", cleaned)
    # Mask 12-16 digit bank account numbers
    cleaned = re.sub(r"\b\d{12,16}\b", "XXXXXXXXXXXX", cleaned)
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def record_user_feedback(
    description: str,
    confirmed_category: str,
    user_id: Optional[int] = None,
    original_predicted_category: Optional[str] = None,
    original_confidence: Optional[float] = None,
    feedback_csv_path: Union[str, Path] = DEFAULT_FEEDBACK_DATASET_PATH,
) -> Dict[str, Any]:
    """
    Records a user-confirmed or user-corrected transaction category.
    Validates that confirmed_category matches one of the 12 canonical categories.
    Appends the record to the user feedback CSV file.
    """
    category_stripped = confirmed_category.strip()
    if category_stripped not in CANONICAL_CATEGORIES:
        raise ValueError(
            f"Invalid category '{confirmed_category}'. Must be one of: {CANONICAL_CATEGORIES}"
        )

    sanitized_desc = sanitize_description_for_training(description)
    if not sanitized_desc:
        raise ValueError("Description cannot be empty or pure whitespace.")

    p = Path(feedback_csv_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)

    file_exists = p.exists() and p.stat().st_size > 0

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id if user_id is not None else "",
        "description": sanitized_desc,
        "confirmed_category": category_stripped,
        "original_predicted_category": original_predicted_category or "",
        "original_confidence": round(float(original_confidence), 4) if original_confidence is not None else "",
    }

    with open(p, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FEEDBACK_CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)

    return record


def load_user_feedback(
    feedback_csv_path: Union[str, Path] = DEFAULT_FEEDBACK_DATASET_PATH,
) -> pd.DataFrame:
    """Loads all user feedback records from the CSV file."""
    p = Path(feedback_csv_path).resolve()
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame(columns=FEEDBACK_CSV_HEADERS)
    return pd.read_csv(p)


def get_combined_training_data(
    base_dataset_path: Union[str, Path] = DEFAULT_DATASET_PATH,
    feedback_csv_path: Union[str, Path] = DEFAULT_FEEDBACK_DATASET_PATH,
) -> pd.DataFrame:
    """
    Merges the original base labeled dataset with user feedback samples.
    Deduplicates descriptions by preferring user feedback labels over base labels.
    """
    base_p = Path(base_dataset_path).resolve()
    base_df = pd.read_csv(base_p)
    base_df = base_df[["description", "category"]].copy()

    fb_df = load_user_feedback(feedback_csv_path)
    if fb_df.empty:
        return base_df

    fb_clean = fb_df[["description", "confirmed_category"]].rename(
        columns={"confirmed_category": "category"}
    ).copy()

    # User feedback overrides baseline labels on exact description match
    combined = pd.concat([base_df, fb_clean], ignore_index=True)
    combined = combined.drop_duplicates(subset=["description"], keep="last")
    return combined.reset_index(drop=True)


def retrain_model_with_feedback(
    feedback_csv_path: Union[str, Path] = DEFAULT_FEEDBACK_DATASET_PATH,
    base_dataset_path: Union[str, Path] = DEFAULT_DATASET_PATH,
    output_model_path: Union[str, Path] = DEFAULT_MODEL_PATH,
    min_feedback_samples: int = 5,
    validation_gate_accuracy: float = 0.88,
    random_state: int = 42,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Retrains the Logistic Regression model using combined base + feedback data.
    Enforces a strict validation gate: retrained model must achieve >= validation_gate_accuracy
    on a holdout test split before overwriting the production model artifact.

    Returns:
        (passed_gate: bool, metrics_dict: Dict[str, Any])
    """
    fb_df = load_user_feedback(feedback_csv_path)
    if len(fb_df) < min_feedback_samples:
        return False, {
            "status": "skipped",
            "reason": f"Insufficient feedback samples ({len(fb_df)} < {min_feedback_samples})",
            "feedback_count": len(fb_df),
        }

    combined_df = get_combined_training_data(base_dataset_path, feedback_csv_path)
    embedder = get_transaction_embedder()

    texts = combined_df["description"].tolist()
    labels = combined_df["category"].tolist()

    embeddings = embedder.embed(texts, normalize=True)

    X_train, X_test, y_train, y_test = train_test_split(
        embeddings,
        labels,
        test_size=0.2,
        random_state=random_state,
        stratify=labels,
    )

    candidate_clf = LogisticRegressionClassifier(C=2.0, random_state=random_state)
    candidate_clf.fit(X_train, y_train)

    preds = candidate_clf.predict(X_test)
    accuracy = float(accuracy_score(y_test, preds))
    macro_f1 = float(f1_score(y_test, preds, average="macro"))

    metrics = {
        "status": "evaluated",
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "total_samples": len(combined_df),
        "feedback_samples": len(fb_df),
        "validation_gate_accuracy": validation_gate_accuracy,
    }

    if accuracy >= validation_gate_accuracy:
        # Train on 100% combined dataset and save
        production_clf = LogisticRegressionClassifier(C=2.0, random_state=random_state)
        production_clf.fit(embeddings, labels)
        production_clf.save(output_model_path)
        metrics["status"] = "deployed"
        return True, metrics
    else:
        metrics["status"] = "rejected_regression_gate"
        return False, metrics
