"""
Unit tests verifying Task 3.1 labeled dataset integrity and coverage.
"""

import csv
from pathlib import Path
import pytest

from app.seed_categories import SEED_CATEGORIES

DATASET_PATH = Path("data/categorization/transactions_labeled_dataset.csv")
CANONICAL_CATEGORIES = {c["name"] for c in SEED_CATEGORIES}


def test_labeled_dataset_file_exists():
    """Verify labeled dataset CSV exists and is non-empty."""
    assert DATASET_PATH.exists(), f"Dataset file missing: {DATASET_PATH}"
    assert DATASET_PATH.stat().st_size > 0, "Dataset file is empty"


def test_labeled_dataset_row_count_and_columns():
    """Verify dataset contains ~500-1000 samples and required columns (Task 3.1 requirement)."""
    with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        assert fieldnames is not None
        assert "id" in fieldnames
        assert "description" in fieldnames
        assert "category" in fieldnames

        rows = list(reader)

    # Must be within the 500 to 1000 range required by spec
    assert 500 <= len(rows) <= 1000, f"Expected 500-1000 rows, got {len(rows)}"


def test_all_12_canonical_categories_covered_and_balanced():
    """Verify all 12 canonical categories are represented with at least 30 samples each."""
    category_counts = {}
    descriptions = set()

    with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row["category"].strip()
            desc = row["description"].strip()

            assert cat in CANONICAL_CATEGORIES, f"Unexpected category '{cat}' not in canonical categories"
            assert len(desc) > 0, f"Empty description for sample ID {row.get('id')}"

            # Deduplication check
            assert desc.lower() not in descriptions, f"Duplicate description found: {desc}"
            descriptions.add(desc.lower())

            category_counts[cat] = category_counts.get(cat, 0) + 1

    assert len(category_counts) == 12, f"Expected all 12 categories, found {len(category_counts)}"
    for cat in CANONICAL_CATEGORIES:
        assert cat in category_counts, f"Category '{cat}' missing from dataset"
        assert category_counts[cat] >= 30, f"Category '{cat}' has insufficient samples: {category_counts[cat]}"


def test_indian_banking_and_upi_patterns_present():
    """Verify realistic Indian banking narrations are present across the dataset."""
    with open(DATASET_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_text = " ".join(r["description"] for r in reader)

    patterns = ["UPI", "NEFT", "IMPS", "POS", "ACH", "RTGS", "@"]
    for pattern in patterns:
        assert pattern in all_text, f"Expected pattern '{pattern}' not found in dataset descriptions"
