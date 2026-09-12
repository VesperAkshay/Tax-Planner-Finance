from datetime import date as dt_date
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction


def detect_self_transfers(
    transactions: List[Transaction],
    max_day_difference: int = 0,
    self_transfer_category_id: Optional[int] = None,
) -> List[Tuple[Transaction, Transaction]]:
    """
    In-memory detection of self-transfers (Task 2.8).
    Matches same-day, same-amount, opposite-direction transactions across different accounts.

    For every matched pair (debit, credit):
    - Sets `is_self_transfer = True` on both transactions.
    - If `self_transfer_category_id` is provided, sets `category_id` and `category_confidence = 1.0`.

    Returns a list of matched pairs: `[(debit_tx, credit_tx), ...]`.
    Ensures 1-to-1 matching (each transaction is matched at most once).
    """
    matched_pairs: List[Tuple[Transaction, Transaction]] = []
    used_indices: Set[int] = set()

    # Separate candidates into debits and credits
    debits: List[Tuple[int, Transaction]] = []
    credits: List[Tuple[int, Transaction]] = []

    for idx, tx in enumerate(transactions):
        # Skip if already marked as self-transfer
        if getattr(tx, "is_self_transfer", False):
            used_indices.add(idx)
            continue

        tx_type = str(getattr(tx, "transaction_type", "")).lower().strip()
        if tx_type == "debit":
            debits.append((idx, tx))
        elif tx_type == "credit":
            credits.append((idx, tx))

    # Pass 1: Match by reference number (strongest link) when reference numbers match
    for d_idx, d_tx in debits:
        if d_idx in used_indices:
            continue
        d_ref = getattr(d_tx, "reference_number", None)
        if not d_ref or not str(d_ref).strip():
            continue

        for c_idx, c_tx in credits:
            if c_idx in used_indices:
                continue

            # Must be different accounts
            if d_tx.account_id == c_tx.account_id:
                continue

            # Check amount match
            if round(abs(d_tx.amount - c_tx.amount), 2) != 0.0:
                continue

            # Check date match
            day_diff = abs((d_tx.date - c_tx.date).days)
            if day_diff > max_day_difference:
                continue

            c_ref = getattr(c_tx, "reference_number", None)
            if c_ref and str(c_ref).strip().lower() == str(d_ref).strip().lower():
                # Definite match!
                used_indices.add(d_idx)
                used_indices.add(c_idx)
                d_tx.is_self_transfer = True
                c_tx.is_self_transfer = True

                if self_transfer_category_id is not None:
                    d_tx.category_id = self_transfer_category_id
                    d_tx.category_confidence = 1.0
                    c_tx.category_id = self_transfer_category_id
                    c_tx.category_confidence = 1.0

                matched_pairs.append((d_tx, c_tx))
                break

    # Pass 2: Match same-day, same-amount, opposite-direction across different accounts
    for d_idx, d_tx in debits:
        if d_idx in used_indices:
            continue

        for c_idx, c_tx in credits:
            if c_idx in used_indices:
                continue

            # Must be different accounts
            if d_tx.account_id == c_tx.account_id:
                continue

            # Must match amount exactly
            if round(abs(d_tx.amount - c_tx.amount), 2) != 0.0:
                continue

            # Must be within allowed day difference (default 0 = same-day)
            day_diff = abs((d_tx.date - c_tx.date).days)
            if day_diff > max_day_difference:
                continue

            # Match found!
            used_indices.add(d_idx)
            used_indices.add(c_idx)
            d_tx.is_self_transfer = True
            c_tx.is_self_transfer = True

            if self_transfer_category_id is not None:
                d_tx.category_id = self_transfer_category_id
                d_tx.category_confidence = 1.0
                c_tx.category_id = self_transfer_category_id
                c_tx.category_confidence = 1.0

            matched_pairs.append((d_tx, c_tx))
            break

    return matched_pairs


async def detect_and_update_self_transfers_db(
    session: AsyncSession,
    user_id: int,
    max_day_difference: int = 0,
) -> List[Tuple[Transaction, Transaction]]:
    """
    Database service function for self-transfer detection (Task 2.8).
    Queries all accounts for the user, loads active transactions,
    runs detection, marks `is_self_transfer = True`, links to 'Self-Transfer' category,
    and persists updates to the database.
    """
    # 1. Fetch user's account IDs
    account_stmt = select(Account.id).where(Account.user_id == user_id)
    acc_res = await session.execute(account_stmt)
    user_account_ids = list(acc_res.scalars().all())

    if len(user_account_ids) < 2:
        # Cross-account self-transfer requires at least 2 accounts owned by user
        return []

    # 2. Look up 'Self-Transfer' category ID if present
    cat_stmt = select(Category.id).where(col(Category.name).ilike("Self-Transfer"))
    cat_res = await session.execute(cat_stmt)
    self_transfer_cat_id = cat_res.scalars().first()

    # 3. Query transactions across all user accounts
    tx_stmt = select(Transaction).where(
        col(Transaction.account_id).in_(user_account_ids)
    )
    tx_res = await session.execute(tx_stmt)
    all_transactions = list(tx_res.scalars().all())

    # 4. Detect self-transfers
    pairs = detect_self_transfers(
        transactions=all_transactions,
        max_day_difference=max_day_difference,
        self_transfer_category_id=self_transfer_cat_id,
    )

    # 5. Save changes to DB
    if pairs:
        for d_tx, c_tx in pairs:
            session.add(d_tx)
            session.add(c_tx)
        await session.commit()

    return pairs
