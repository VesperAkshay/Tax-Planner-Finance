import pytest
from sqlmodel import SQLModel, create_engine, Session, select

from app.models.category import Category, CategoryCreate
from app.seed_categories import SEED_CATEGORIES, seed_categories_sync

EXPECTED_CATEGORIES = [
    "Rent",
    "Groceries",
    "Utilities",
    "Transport",
    "Dining",
    "Shopping",
    "Entertainment",
    "Subscriptions",
    "Medical",
    "Salary Credit",
    "Miscellaneous",
    "Self-Transfer",
]


def test_category_metadata():
    """Verify categories table is registered in metadata."""
    assert "categories" in SQLModel.metadata.tables


def test_expected_12_categories():
    """Verify seed list contains exactly the 12 specified categories."""
    assert len(SEED_CATEGORIES) == 12
    category_names = [c["name"] for c in SEED_CATEGORIES]
    assert sorted(category_names) == sorted(EXPECTED_CATEGORIES)


def test_seed_categories_idempotent():
    """Test seed_categories in an in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    # First run: should create all 12
    with Session(engine) as session:
        created, all_cats = seed_categories_sync(session)
        assert created == 12
        assert len(all_cats) == 12
        names = [c.name for c in all_cats]
        for expected in EXPECTED_CATEGORIES:
            assert expected in names

    # Second run: idempotent, should create 0 new
    with Session(engine) as session:
        created, all_cats = seed_categories_sync(session)
        assert created == 0
        assert len(all_cats) == 12
