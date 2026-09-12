"""
Unit and Persistence Tests for Reconciliation Resolution Flow (Tasks 4.4 & 4.7).

Verifies:
- Task 4.4: Updating flag status to 'resolved' or 'ignored' with required user note.
- Task 4.7: Direct verification that status and user note persist accurately on re-query.
"""

from datetime import date
import pytest
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    Account,
    ReconciliationFlag,
    SalarySlip,
    Transaction,
    User,
)
from app.reconciliation.constants import (
    FLAG_TYPE_MISMATCHED_AMOUNT,
    STATUS_IGNORED,
    STATUS_PENDING,
    STATUS_RESOLVED,
)
from app.reconciliation.service import (
    get_user_reconciliation_flags,
    resolve_reconciliation_flag,
    run_reconciliation_pipeline,
)


@pytest.fixture(name="db_session")
def db_session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


def test_task_4_4_resolve_flag_with_note(db_session: Session):
    """
    Task 4.4: Resolve flag to 'resolved' with non-empty user note.
    """
    user = User(email="test@reconciliation.local", hashed_password="pw", full_name="Tester", pan="ABCDE1234F")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    flag = ReconciliationFlag(
        user_id=user.id,
        month=8,
        year=2025,
        flag_type=FLAG_TYPE_MISMATCHED_AMOUNT,
        expected_amount=85000.0,
        actual_amount=80000.0,
        difference=5000.0,
        status=STATUS_PENDING,
    )
    db_session.add(flag)
    db_session.commit()
    db_session.refresh(flag)
    assert flag.status == STATUS_PENDING
    assert flag.user_note is None

    # Resolve flag with user note
    resolved = resolve_reconciliation_flag(
        session=db_session,
        flag_id=flag.id,
        user_id=user.id,
        action=STATUS_RESOLVED,
        user_note="Verified with payroll team: ₹5,000 deducted for transit pass advance.",
    )

    assert resolved.status == STATUS_RESOLVED
    assert resolved.user_note == "Verified with payroll team: ₹5,000 deducted for transit pass advance."
    assert resolved.resolved_at is not None


def test_task_4_4_ignore_flag_with_note(db_session: Session):
    """
    Task 4.4: Update flag to 'ignored' with user note.
    """
    user = User(email="ignore@reconciliation.local", hashed_password="pw", full_name="Tester", pan="ABCDE1234F")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    flag = ReconciliationFlag(
        user_id=user.id,
        month=5,
        year=2025,
        flag_type=FLAG_TYPE_MISMATCHED_AMOUNT,
        expected_amount=70000.0,
        actual_amount=72000.0,
        difference=2000.0,
        status=STATUS_PENDING,
    )
    db_session.add(flag)
    db_session.commit()
    db_session.refresh(flag)

    ignored = resolve_reconciliation_flag(
        session=db_session,
        flag_id=flag.id,
        user_id=user.id,
        action=STATUS_IGNORED,
        user_note="Minor discrepancy deemed acceptable; client confirmed reimbursable expense.",
    )

    assert ignored.status == STATUS_IGNORED
    assert ignored.user_note == "Minor discrepancy deemed acceptable; client confirmed reimbursable expense."
    assert ignored.resolved_at is not None


def test_task_4_4_resolution_validation_errors(db_session: Session):
    """
    Rejects missing note, whitespace-only note, invalid action, and non-existent flag.
    """
    user = User(email="val@reconciliation.local", hashed_password="pw", full_name="Val Tester", pan="ABCDE1234F")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    flag = ReconciliationFlag(
        user_id=user.id,
        month=6,
        year=2025,
        flag_type=FLAG_TYPE_MISMATCHED_AMOUNT,
        expected_amount=90000.0,
        status=STATUS_PENDING,
    )
    db_session.add(flag)
    db_session.commit()
    db_session.refresh(flag)

    # Empty user note
    with pytest.raises(ValueError, match="non-empty user_note is required"):
        resolve_reconciliation_flag(
            session=db_session,
            flag_id=flag.id,
            user_id=user.id,
            action=STATUS_RESOLVED,
            user_note="   ",
        )

    # Invalid action
    with pytest.raises(ValueError, match="Invalid resolution action"):
        resolve_reconciliation_flag(
            session=db_session,
            flag_id=flag.id,
            user_id=user.id,
            action="deleted",
            user_note="Valid note",
        )

    # Flag not found / wrong user
    with pytest.raises(ValueError, match="not found"):
        resolve_reconciliation_flag(
            session=db_session,
            flag_id=99999,
            user_id=user.id,
            action=STATUS_RESOLVED,
            user_note="Valid note",
        )


def test_task_4_7_resolution_persistence_on_requery(db_session: Session):
    """
    Task 4.7 manual/automated test:
    Directly calls the resolution function, then re-queries the database from scratch
    to confirm status and note persist accurately.
    """
    user = User(email="persist@reconciliation.local", hashed_password="pw", full_name="Persist Tester", pan="ABCDE1234F")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Insert pending flag
    flag = ReconciliationFlag(
        user_id=user.id,
        month=9,
        year=2025,
        flag_type=FLAG_TYPE_MISMATCHED_AMOUNT,
        expected_amount=100000.0,
        actual_amount=95000.0,
        difference=5000.0,
        status=STATUS_PENDING,
    )
    db_session.add(flag)
    db_session.commit()
    db_session.refresh(flag)
    flag_id = flag.id

    # Call resolution
    resolve_reconciliation_flag(
        session=db_session,
        flag_id=flag_id,
        user_id=user.id,
        action=STATUS_RESOLVED,
        user_note="Confirmed with bank statement: difference was ₹5,000 TDS deducted at source.",
    )

    # Re-query directly via select to confirm persistent state
    re_queried_flag = db_session.exec(select(ReconciliationFlag).where(ReconciliationFlag.id == flag_id)).first()
    assert re_queried_flag is not None
    assert re_queried_flag.status == STATUS_RESOLVED
    assert re_queried_flag.user_note == "Confirmed with bank statement: difference was ₹5,000 TDS deducted at source."
    assert re_queried_flag.resolved_at is not None

    # Filtered list query
    resolved_flags = get_user_reconciliation_flags(session=db_session, user_id=user.id, status=STATUS_RESOLVED)
    assert len(resolved_flags) == 1
    assert resolved_flags[0].id == flag_id

    pending_flags = get_user_reconciliation_flags(session=db_session, user_id=user.id, status=STATUS_PENDING)
    assert len(pending_flags) == 0
