"""
Financial Snapshot API Endpoint (Task 8.3).

Provides:
- Income/expense breakdown
- Spending by category with percentages and counts
- Net savings and savings rate
- Sourced directly from Phase 3 categorized transactions, scoped to the authenticated user.
"""

from collections import defaultdict
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.database import get_db_session
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/financial-snapshot", tags=["Financial Analytics"])


class CategorySpendingItem(BaseModel):
    category_name: str
    total_amount: float
    percentage: float
    transaction_count: int


class FinancialSnapshotResponse(BaseModel):
    user_id: int
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float  # Percentage (e.g. 35.4%)
    category_spending: List[CategorySpendingItem]
    top_categories: List[CategorySpendingItem]
    uncategorized_count: int
    needs_review_count: int
    total_transactions_analyzed: int


@router.get("", response_model=FinancialSnapshotResponse)
def get_financial_snapshot(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> FinancialSnapshotResponse:
    """
    Computes a comprehensive financial snapshot (Task 8.3) for the authenticated user.
    Excludes self-transfers from income/expense metrics.
    """
    # 1. Fetch user's accounts
    user_accounts = session.exec(select(Account).where(Account.user_id == current_user.id)).all()
    account_ids = [acc.id for acc in user_accounts]

    if not account_ids:
        return FinancialSnapshotResponse(
            user_id=current_user.id,
            total_income=0.0,
            total_expenses=0.0,
            net_savings=0.0,
            savings_rate=0.0,
            category_spending=[],
            top_categories=[],
            uncategorized_count=0,
            needs_review_count=0,
            total_transactions_analyzed=0,
        )

    # 2. Fetch all user transactions
    stmt = (
        select(Transaction)
        .where(Transaction.account_id.in_(account_ids))  # type: ignore
        .order_by(Transaction.date.desc())
    )
    transactions = session.exec(stmt).all()

    # Load categories mapping
    categories_map = {c.id: c.name for c in session.exec(select(Category)).all()}

    total_income = 0.0
    total_expenses = 0.0
    category_totals = defaultdict(float)
    category_counts = defaultdict(int)
    uncategorized_count = 0
    needs_review_count = 0

    for txn in transactions:
        if txn.needs_review:
            needs_review_count += 1

        cat_name = categories_map.get(txn.category_id, "Uncategorized")
        if cat_name.lower() == "uncategorized":
            uncategorized_count += 1

        # Skip self-transfers to avoid double-counting internal transfers
        if txn.is_self_transfer or cat_name.lower() == "self-transfer":
            continue

        if txn.transaction_type == "credit":
            total_income += txn.amount
        elif txn.transaction_type == "debit":
            total_expenses += txn.amount
            category_totals[cat_name] += txn.amount
            category_counts[cat_name] += 1

    total_income = round(total_income, 2)
    total_expenses = round(total_expenses, 2)
    net_savings = round(total_income - total_expenses, 2)
    savings_rate = round((net_savings / total_income * 100.0), 2) if total_income > 0.0 else 0.0

    # Build category spending list
    spending_list: List[CategorySpendingItem] = []
    for cat_name, amt in category_totals.items():
        pct = round((amt / total_expenses * 100.0), 2) if total_expenses > 0.0 else 0.0
        spending_list.append(
            CategorySpendingItem(
                category_name=cat_name,
                total_amount=round(amt, 2),
                percentage=pct,
                transaction_count=category_counts[cat_name],
            )
        )

    # Sort descending by spend amount
    spending_list.sort(key=lambda x: x.total_amount, reverse=True)
    top_categories = spending_list[:5]

    return FinancialSnapshotResponse(
        user_id=current_user.id,
        total_income=total_income,
        total_expenses=total_expenses,
        net_savings=net_savings,
        savings_rate=savings_rate,
        category_spending=spending_list,
        top_categories=top_categories,
        uncategorized_count=uncategorized_count,
        needs_review_count=needs_review_count,
        total_transactions_analyzed=len(transactions),
    )
