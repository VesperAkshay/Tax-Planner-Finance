"""
Financial Snapshot API Endpoint with Rich FinTech Analytics (Task 8.3 + Phase 11 Upgrade).

Provides:
- Income / expense / net savings breakdown
- 50/30/20 Budget Rule Diagnostic (Needs vs Wants vs Savings)
- Top Merchants Leaderboard
- Recurring Subscriptions & Fixed Bills Radar
- Tax-Deductible Spends Auto-Discovery (80C, 80D, 80G, 10(13A) HRA)
- Daily Burn Rate & Financial Runway
- Filterable Recent Transactions Explorer
- Re-categorize endpoint to upgrade existing transactions on demand
"""

from collections import defaultdict
from datetime import date
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.api.auth import get_current_user
from app.categorization.categorizer import get_transaction_categorizer
from app.database import get_db_session
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/financial-snapshot", tags=["Financial Analytics"])


# ==============================================================================
# Response Schemas
# ==============================================================================


class CategorySpendingItem(BaseModel):
    category_name: str
    total_amount: float
    percentage: float
    transaction_count: int


class BudgetRuleDiagnostic(BaseModel):
    needs_amount: float
    needs_pct: float
    wants_amount: float
    wants_pct: float
    savings_amount: float
    savings_pct: float
    status: str
    advice: str


class TopMerchantItem(BaseModel):
    merchant: str
    total_spent: float
    transaction_count: int
    category: str


class RecurringSubscriptionItem(BaseModel):
    name: str
    amount: float
    category: str
    frequency: str = "Monthly"


class TaxDeductibleSpendItem(BaseModel):
    section: str
    title: str
    amount: float
    transaction_count: int
    description: str


class SnapshotTransactionItem(BaseModel):
    id: int
    date: str
    description: str
    merchant: str
    amount: float
    transaction_type: str
    category: str
    needs_review: bool


class FinancialSnapshotResponse(BaseModel):
    user_id: int
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float
    daily_burn_rate: float
    category_spending: List[CategorySpendingItem]
    top_categories: List[CategorySpendingItem]
    budget_rule_diagnostic: BudgetRuleDiagnostic
    top_merchants: List[TopMerchantItem]
    recurring_subscriptions: List[RecurringSubscriptionItem]
    tax_deductible_spends: List[TaxDeductibleSpendItem]
    uncategorized_count: int
    needs_review_count: int
    total_transactions_analyzed: int
    recent_transactions: List[SnapshotTransactionItem]


class ReCategorizeResponse(BaseModel):
    total_processed: int
    updated_count: int
    uncategorized_remaining: int
    message: str


# ==============================================================================
# Helper Functions
# ==============================================================================

NEEDS_CATEGORIES = {"rent", "groceries", "utilities", "medical"}
WANTS_CATEGORIES = {"dining", "shopping", "subscriptions", "entertainment", "transport"}


def evaluate_budget_rule(
    total_income: float,
    needs_amt: float,
    wants_amt: float,
    net_savings: float,
) -> BudgetRuleDiagnostic:
    base = total_income if total_income > 0 else (needs_amt + wants_amt + max(0.0, net_savings))
    if base <= 0:
        return BudgetRuleDiagnostic(
            needs_amount=0.0,
            needs_pct=0.0,
            wants_amount=0.0,
            wants_pct=0.0,
            savings_amount=0.0,
            savings_pct=0.0,
            status="No Data",
            advice="Upload statements to generate your 50/30/20 budget diagnostic.",
        )

    n_pct = round((needs_amt / base) * 100.0, 1)
    w_pct = round((wants_amt / base) * 100.0, 1)
    s_pct = round((max(0.0, net_savings) / base) * 100.0, 1)

    if s_pct >= 25.0 and n_pct <= 50.0:
        status_label = "Optimal 50/30/20 Balance"
        advice = "Great financial health! Your savings rate exceeds the 20% benchmark with controlled essential living expenses."
    elif w_pct > 35.0:
        status_label = "Elevated Discretionary Spend"
        advice = f"Wants ({w_pct}%) exceed the 30% golden ratio. Reducing dining or impulse shopping could boost monthly investment capacity."
    elif n_pct > 55.0:
        status_label = "High Essential Outflows"
        advice = f"Needs consume {n_pct}% of verified income. Focus on optimizing fixed recurring bills or rent allocations."
    else:
        status_label = "Stable Financial Buffer"
        advice = "Your spending is reasonably balanced. Ensure surplus cash is deployed into tax-saving 80C/80CCD investments."

    return BudgetRuleDiagnostic(
        needs_amount=round(needs_amt, 2),
        needs_pct=n_pct,
        wants_amount=round(wants_amt, 2),
        wants_pct=w_pct,
        savings_amount=round(max(0.0, net_savings), 2),
        savings_pct=s_pct,
        status=status_label,
        advice=advice,
    )


# ==============================================================================
# Endpoints
# ==============================================================================


@router.get("", response_model=FinancialSnapshotResponse)
def get_financial_snapshot(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> FinancialSnapshotResponse:
    """
    Computes rich FinTech analytics and financial snapshot for the authenticated user.
    """
    # 1. Fetch user accounts
    user_accounts = session.exec(select(Account).where(Account.user_id == current_user.id)).all()
    account_ids = [acc.id for acc in user_accounts]

    if not account_ids:
        empty_diag = BudgetRuleDiagnostic(
            needs_amount=0.0,
            needs_pct=0.0,
            wants_amount=0.0,
            wants_pct=0.0,
            savings_amount=0.0,
            savings_pct=0.0,
            status="No Data",
            advice="Upload statements to generate metrics.",
        )
        return FinancialSnapshotResponse(
            user_id=current_user.id,
            total_income=0.0,
            total_expenses=0.0,
            net_savings=0.0,
            savings_rate=0.0,
            daily_burn_rate=0.0,
            category_spending=[],
            top_categories=[],
            budget_rule_diagnostic=empty_diag,
            top_merchants=[],
            recurring_subscriptions=[],
            tax_deductible_spends=[],
            uncategorized_count=0,
            needs_review_count=0,
            total_transactions_analyzed=0,
            recent_transactions=[],
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
    category_totals: Dict[str, float] = defaultdict(float)
    category_counts: Dict[str, int] = defaultdict(int)
    merchant_totals: Dict[str, float] = defaultdict(float)
    merchant_counts: Dict[str, int] = defaultdict(int)
    merchant_categories: Dict[str, str] = {}
    uncategorized_count = 0
    needs_review_count = 0

    dates: List[date] = []
    tax_80d_amt = 0.0
    tax_80d_count = 0
    tax_80c_amt = 0.0
    tax_80c_count = 0
    tax_hra_amt = 0.0
    tax_hra_count = 0
    tax_80g_amt = 0.0
    tax_80g_count = 0

    needs_amt = 0.0
    wants_amt = 0.0
    recent_txns: List[SnapshotTransactionItem] = []

    for txn in transactions:
        if txn.date:
            dates.append(txn.date)

        if txn.needs_review:
            needs_review_count += 1

        cat_name = categories_map.get(txn.category_id, "Uncategorized")
        cat_lower = cat_name.lower()

        if cat_lower == "uncategorized":
            uncategorized_count += 1

        # Skip self-transfers from income/expense counting
        if txn.is_self_transfer or cat_lower == "self-transfer":
            continue

        clean_merch = txn.cleaned_description or txn.description[:30]

        if txn.transaction_type == "credit":
            total_income += txn.amount
        elif txn.transaction_type == "debit":
            total_expenses += txn.amount
            category_totals[cat_name] += txn.amount
            category_counts[cat_name] += 1

            # Merchant tracking
            merchant_totals[clean_merch] += txn.amount
            merchant_counts[clean_merch] += 1
            merchant_categories[clean_merch] = cat_name

            # 50/30/20 Bucket allocation
            if cat_lower in NEEDS_CATEGORIES:
                needs_amt += txn.amount
            elif cat_lower in WANTS_CATEGORIES:
                wants_amt += txn.amount

            # Tax deduction discovery
            desc_lower = txn.description.lower()
            if cat_lower == "medical" or any(k in desc_lower for k in ["insurance", "mediclaim", "star health", "care health"]):
                tax_80d_amt += txn.amount
                tax_80d_count += 1
            elif cat_lower == "rent":
                tax_hra_amt += txn.amount
                tax_hra_count += 1
            elif any(k in desc_lower for k in ["nps", "ppf", "elss", "lic", "mutual fund", "zerodha", "groww"]):
                tax_80c_amt += txn.amount
                tax_80c_count += 1
            elif any(k in desc_lower for k in ["pm cares", "donation", "relief fund", "charity"]):
                tax_80g_amt += txn.amount
                tax_80g_count += 1

        if len(recent_txns) < 50:
            recent_txns.append(
                SnapshotTransactionItem(
                    id=txn.id or 0,
                    date=str(txn.date),
                    description=txn.description,
                    merchant=clean_merch,
                    amount=round(txn.amount, 2),
                    transaction_type=txn.transaction_type,
                    category=cat_name,
                    needs_review=txn.needs_review,
                )
            )

    total_income = round(total_income, 2)
    total_expenses = round(total_expenses, 2)
    net_savings = round(total_income - total_expenses, 2)
    savings_rate = round((net_savings / total_income * 100.0), 2) if total_income > 0.0 else 0.0

    # Daily burn rate calculation
    if dates:
        date_span = (max(dates) - min(dates)).days + 1
    else:
        date_span = 30
    daily_burn_rate = round(total_expenses / max(1, date_span), 2)

    # Category spending breakdown
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
    spending_list.sort(key=lambda x: x.total_amount, reverse=True)
    top_categories = spending_list[:5]

    # Top Merchants Leaderboard (top 5)
    top_merchants_list: List[TopMerchantItem] = []
    for m_name, m_amt in sorted(merchant_totals.items(), key=lambda x: x[1], reverse=True)[:5]:
        top_merchants_list.append(
            TopMerchantItem(
                merchant=m_name,
                total_spent=round(m_amt, 2),
                transaction_count=merchant_counts[m_name],
                category=merchant_categories.get(m_name, "Miscellaneous"),
            )
        )

    # Recurring Subscriptions
    recurring_list: List[RecurringSubscriptionItem] = []
    for m_name, m_amt in merchant_totals.items():
        cat = merchant_categories.get(m_name, "")
        if cat in ("Subscriptions", "Utilities") or any(k in m_name.lower() for k in ["netflix", "spotify", "prime", "wifi", "broadband", "jio", "airtel"]):
            recurring_list.append(
                RecurringSubscriptionItem(
                    name=m_name,
                    amount=round(m_amt, 2),
                    category=cat,
                    frequency="Monthly",
                )
            )

    # Tax Deductible Radar
    tax_deductibles: List[TaxDeductibleSpendItem] = []
    if tax_hra_amt > 0:
        tax_deductibles.append(
            TaxDeductibleSpendItem(
                section="Section 10(13A)",
                title="House Rent Paid (HRA Exemption)",
                amount=round(tax_hra_amt, 2),
                transaction_count=tax_hra_count,
                description="Eligible to exempt rent against HRA received from your employer.",
            )
        )
    if tax_80d_amt > 0:
        tax_deductibles.append(
            TaxDeductibleSpendItem(
                section="Section 80D",
                title="Medical Insurance & Healthcare",
                amount=round(tax_80d_amt, 2),
                transaction_count=tax_80d_count,
                description="Eligible for health insurance premium deduction up to ₹25,000 (₹50,000 for seniors).",
            )
        )
    if tax_80c_amt > 0:
        tax_deductibles.append(
            TaxDeductibleSpendItem(
                section="Section 80C / 80CCD",
                title="Investments & Pension Plans",
                amount=round(tax_80c_amt, 2),
                transaction_count=tax_80c_count,
                description="ELSS, PPF, and NPS investments qualify towards Section 80C/80CCD(1B) caps.",
            )
        )
    if tax_80g_amt > 0:
        tax_deductibles.append(
            TaxDeductibleSpendItem(
                section="Section 80G",
                title="Charitable Donations",
                amount=round(tax_80g_amt, 2),
                transaction_count=tax_80g_count,
                description="Qualifies for 50% or 100% deduction under Section 80G.",
            )
        )

    diagnostic = evaluate_budget_rule(
        total_income=total_income,
        needs_amt=needs_amt,
        wants_amt=wants_amt,
        net_savings=net_savings,
    )

    return FinancialSnapshotResponse(
        user_id=current_user.id,
        total_income=total_income,
        total_expenses=total_expenses,
        net_savings=net_savings,
        savings_rate=savings_rate,
        daily_burn_rate=daily_burn_rate,
        category_spending=spending_list,
        top_categories=top_categories,
        budget_rule_diagnostic=diagnostic,
        top_merchants=top_merchants_list,
        recurring_subscriptions=recurring_list,
        tax_deductible_spends=tax_deductibles,
        uncategorized_count=uncategorized_count,
        needs_review_count=needs_review_count,
        total_transactions_analyzed=len(transactions),
        recent_transactions=recent_txns,
    )


@router.post("/re-categorize", response_model=ReCategorizeResponse)
def recategorize_user_transactions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session),
) -> ReCategorizeResponse:
    """
    Upgrades and re-categorizes existing transactions for the user using the
    hybrid Indian Merchant Pattern Matcher + XGBoost + LLM pipeline.
    """
    user_accounts = session.exec(select(Account).where(Account.user_id == current_user.id)).all()
    account_ids = [acc.id for acc in user_accounts]

    if not account_ids:
        return ReCategorizeResponse(
            total_processed=0,
            updated_count=0,
            uncategorized_remaining=0,
            message="No bank accounts found for user.",
        )

    transactions = session.exec(
        select(Transaction).where(Transaction.account_id.in_(account_ids))  # type: ignore
    ).all()

    if not transactions:
        return ReCategorizeResponse(
            total_processed=0,
            updated_count=0,
            uncategorized_remaining=0,
            message="No transactions found to re-categorize.",
        )

    all_categories = {c.name.lower(): c.id for c in session.exec(select(Category)).all()}
    categorizer = get_transaction_categorizer(model_type="xgboost")

    descriptions = [t.description for t in transactions]
    cat_results = categorizer.categorize_batch(
        descriptions,
        use_llm_fallback=True,
        user_id=current_user.id,
    )

    updated_count = 0
    uncategorized_remaining = 0

    for txn, res in zip(transactions, cat_results):
        if res.category.lower() == "uncategorized":
            uncategorized_remaining += 1
        else:
            cat_id = all_categories.get(res.category.lower())
            if cat_id and txn.category_id != cat_id:
                txn.category_id = cat_id
                txn.category_confidence = res.confidence
                txn.needs_review = res.needs_review
                if res.clean_merchant:
                    txn.cleaned_description = res.clean_merchant
                session.add(txn)
                updated_count += 1

    session.commit()

    return ReCategorizeResponse(
        total_processed=len(transactions),
        updated_count=updated_count,
        uncategorized_remaining=uncategorized_remaining,
        message=f"Successfully upgraded {updated_count} transactions using Hybrid XGBoost + LLM pipeline.",
    )
