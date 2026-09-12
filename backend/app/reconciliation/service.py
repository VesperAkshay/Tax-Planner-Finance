"""
Reconciliation Database Service & Resolution Flow (Task 4.4).

Manages:
- Database-backed execution of reconciliation across user salary slips and bank credits.
- Resolution flow: resolving or ignoring flags with mandatory user notes and timestamp tracking.
- Querying and filtering reconciliation flags.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select

from app.models.common import get_utc_now
from app.models.reconciliation_flag import ReconciliationFlag
from app.models.salary_slip import SalarySlip
from app.models.transaction import Transaction
from app.reconciliation.constants import (
    STATUS_IGNORED,
    STATUS_PENDING,
    STATUS_RESOLVED,
    VALID_STATUSES,
)
from app.reconciliation.matcher import reconcile_salary_and_bank
from app.reconciliation.schemas import (
    BankCreditItem,
    ReconciliationReport,
    SalarySlipItem,
)


def resolve_reconciliation_flag(
    session: Session,
    flag_id: int,
    user_id: int,
    action: str,
    user_note: str,
) -> ReconciliationFlag:
    """
    Implements the Task 4.4 Resolution Flow:
    Updates status to 'resolved' or 'ignored' with a required user_note and resolved timestamp.
    Raises ValueError if user_note is missing or action is invalid.
    """
    if action not in (STATUS_RESOLVED, STATUS_IGNORED):
        raise ValueError(f"Invalid resolution action '{action}'. Must be '{STATUS_RESOLVED}' or '{STATUS_IGNORED}'.")

    if not user_note or not user_note.strip():
        raise ValueError("A non-empty user_note is required when resolving or ignoring a reconciliation flag.")

    stmt = select(ReconciliationFlag).where(
        ReconciliationFlag.id == flag_id,
        ReconciliationFlag.user_id == user_id,
    )
    flag = session.exec(stmt).first()
    if flag is None:
        raise ValueError(f"Reconciliation flag with ID {flag_id} not found for user {user_id}.")

    flag.status = action
    flag.user_note = user_note.strip()
    flag.resolved_at = get_utc_now()
    flag.updated_at = get_utc_now()

    session.add(flag)
    session.commit()
    session.refresh(flag)
    return flag


def get_user_reconciliation_flags(
    session: Session,
    user_id: int,
    status: Optional[str] = None,
) -> List[ReconciliationFlag]:
    """Retrieves all reconciliation flags for a given user, optionally filtered by status."""
    query = select(ReconciliationFlag).where(ReconciliationFlag.user_id == user_id)
    if status is not None:
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_STATUSES}")
        query = query.where(ReconciliationFlag.status == status)

    query = query.order_by(ReconciliationFlag.year.desc(), ReconciliationFlag.month.desc())
    return list(session.exec(query).all())


def run_reconciliation_pipeline(
    session: Session,
    user_id: int,
    auto_commit: bool = True,
) -> ReconciliationReport:
    """
    Fetches all SalarySlips and credit Transactions for the user from Neon DB,
    executes month-level matching and edge case detection, persists any new flags,
    and returns a full ReconciliationReport.
    """
    # 1. Fetch Salary Slips
    slip_stmt = select(SalarySlip).where(SalarySlip.user_id == user_id)
    db_slips = session.exec(slip_stmt).all()

    slip_items = [
        SalarySlipItem(
            id=s.id,
            month=s.month,
            year=s.year,
            net_pay=s.net_pay,
            gross_pay=s.gross_pay,
            file_name=s.file_name,
        )
        for s in db_slips
    ]

    # 2. Fetch Credit Transactions
    txn_stmt = (
        select(Transaction)
        .join(Transaction.account)  # type: ignore
        .where(Transaction.transaction_type == "credit")
    )
    # Filter by user through account
    db_txns = [t for t in session.exec(select(Transaction).where(Transaction.transaction_type == "credit")).all() if t.account and t.account.user_id == user_id]

    credit_items = [
        BankCreditItem(
            id=t.id,
            date=t.date,
            amount=t.amount,
            description=t.description,
            account_id=t.account_id,
        )
        for t in db_txns
    ]

    # 3. Execute matching engine
    report = reconcile_salary_and_bank(
        slips=slip_items,
        credits=credit_items,
        user_id=user_id,
    )

    # 4. Persist newly identified flags into DB
    if auto_commit and report.flags:
        for f in report.flags:
            # Check for existing flag on same slip/transaction/type
            existing_stmt = select(ReconciliationFlag).where(
                ReconciliationFlag.user_id == user_id,
                ReconciliationFlag.month == f.month,
                ReconciliationFlag.year == f.year,
                ReconciliationFlag.flag_type == f.flag_type,
            )
            existing = session.exec(existing_stmt).first()

            if existing is None:
                new_flag = ReconciliationFlag(
                    user_id=user_id,
                    salary_slip_id=f.salary_slip_id,
                    transaction_id=f.transaction_id,
                    month=f.month,
                    year=f.year,
                    flag_type=f.flag_type,
                    expected_amount=f.expected_amount,
                    actual_amount=f.actual_amount,
                    difference=f.difference,
                    status=STATUS_PENDING,
                )
                session.add(new_flag)

        session.commit()

    return report
