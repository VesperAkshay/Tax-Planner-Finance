from datetime import date
import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_async_session
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.reconciliation.self_transfer import (
    detect_and_update_self_transfers_db,
    detect_self_transfers,
)


def create_tx(
    account_id: int,
    tx_date: date,
    amount: float,
    tx_type: str,
    ref: str = None,
    desc: str = "Test Narration",
) -> Transaction:
    return Transaction(
        account_id=account_id,
        date=tx_date,
        amount=amount,
        transaction_type=tx_type,
        description=desc,
        reference_number=ref,
        is_self_transfer=False,
    )


def test_exact_same_day_opposite_direction_match():
    d1 = date(2024, 5, 10)
    t_debit = create_tx(account_id=1, tx_date=d1, amount=15000.0, tx_type="debit")
    t_credit = create_tx(account_id=2, tx_date=d1, amount=15000.0, tx_type="credit")

    pairs = detect_self_transfers([t_debit, t_credit])
    assert len(pairs) == 1
    assert t_debit.is_self_transfer is True
    assert t_credit.is_self_transfer is True


def test_same_account_not_matched():
    # Intra-account debit/credit should not be classified as cross-account self-transfer
    d1 = date(2024, 5, 10)
    t_debit = create_tx(account_id=1, tx_date=d1, amount=10000.0, tx_type="debit")
    t_credit = create_tx(account_id=1, tx_date=d1, amount=10000.0, tx_type="credit")

    pairs = detect_self_transfers([t_debit, t_credit])
    assert len(pairs) == 0
    assert t_debit.is_self_transfer is False
    assert t_credit.is_self_transfer is False


def test_different_dates_not_matched():
    t_debit = create_tx(account_id=1, tx_date=date(2024, 5, 10), amount=5000.0, tx_type="debit")
    t_credit = create_tx(account_id=2, tx_date=date(2024, 5, 12), amount=5000.0, tx_type="credit")

    # Default max_day_difference = 0
    pairs = detect_self_transfers([t_debit, t_credit], max_day_difference=0)
    assert len(pairs) == 0
    assert t_debit.is_self_transfer is False

    # If max_day_difference is set to 2, should match
    pairs_allowed = detect_self_transfers([t_debit, t_credit], max_day_difference=2)
    assert len(pairs_allowed) == 1
    assert t_debit.is_self_transfer is True
    assert t_credit.is_self_transfer is True


def test_different_amounts_not_matched():
    d1 = date(2024, 5, 10)
    t_debit = create_tx(account_id=1, tx_date=d1, amount=5000.0, tx_type="debit")
    t_credit = create_tx(account_id=2, tx_date=d1, amount=5050.0, tx_type="credit")

    pairs = detect_self_transfers([t_debit, t_credit])
    assert len(pairs) == 0
    assert t_debit.is_self_transfer is False


def test_same_direction_not_matched():
    d1 = date(2024, 5, 10)
    t_debit1 = create_tx(account_id=1, tx_date=d1, amount=5000.0, tx_type="debit")
    t_debit2 = create_tx(account_id=2, tx_date=d1, amount=5000.0, tx_type="debit")

    pairs = detect_self_transfers([t_debit1, t_debit2])
    assert len(pairs) == 0


def test_one_to_one_matching_preventing_double_link():
    d1 = date(2024, 5, 10)
    t_debit1 = create_tx(account_id=1, tx_date=d1, amount=10000.0, tx_type="debit", desc="Transfer 1")
    t_debit2 = create_tx(account_id=1, tx_date=d1, amount=10000.0, tx_type="debit", desc="Transfer 2")
    t_credit = create_tx(account_id=2, tx_date=d1, amount=10000.0, tx_type="credit")

    pairs = detect_self_transfers([t_debit1, t_debit2, t_credit])
    assert len(pairs) == 1
    # Exactly one debit should be matched
    matched_debits = [t for t in (t_debit1, t_debit2) if t.is_self_transfer]
    unmatched_debits = [t for t in (t_debit1, t_debit2) if not t.is_self_transfer]
    assert len(matched_debits) == 1
    assert len(unmatched_debits) == 1
    assert t_credit.is_self_transfer is True


def test_reference_number_disambiguation():
    d1 = date(2024, 5, 10)
    t_debit_alpha = create_tx(account_id=1, tx_date=d1, amount=25000.0, tx_type="debit", ref="REF-ALPHA")
    t_debit_beta = create_tx(account_id=1, tx_date=d1, amount=25000.0, tx_type="debit", ref="REF-BETA")
    t_credit_beta = create_tx(account_id=2, tx_date=d1, amount=25000.0, tx_type="credit", ref="REF-BETA")

    pairs = detect_self_transfers([t_debit_alpha, t_debit_beta, t_credit_beta])
    assert len(pairs) == 1
    matched_debit, matched_credit = pairs[0]
    assert matched_debit.reference_number == "REF-BETA"
    assert matched_credit.reference_number == "REF-BETA"
    assert t_debit_alpha.is_self_transfer is False


def test_category_assignment_on_match():
    d1 = date(2024, 5, 10)
    t_debit = create_tx(account_id=1, tx_date=d1, amount=8000.0, tx_type="debit")
    t_credit = create_tx(account_id=2, tx_date=d1, amount=8000.0, tx_type="credit")

    pairs = detect_self_transfers([t_debit, t_credit], self_transfer_category_id=12)
    assert len(pairs) == 1
    assert t_debit.category_id == 12
    assert t_debit.category_confidence == 1.0
    assert t_credit.category_id == 12
    assert t_credit.category_confidence == 1.0


@pytest.mark.asyncio
async def test_detect_and_update_self_transfers_db():
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import NullPool
    from app.config import get_settings

    settings = get_settings()
    test_engine = create_async_engine(settings.async_database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    test_email = f"selftransfer_{uuid.uuid4().hex[:8]}@example.com"
    test_pan = f"ABCDE{uuid.uuid4().hex[:4].upper()}Z"

    async with session_factory() as session:
        user = User(
            email=test_email,
            full_name="Self Transfer Test",
            pan=test_pan,
            hashed_password="test_secret_hash",
        )
        session.add(user)
        await session.flush()

        try:
            # Create two accounts for this user
            acc1 = Account(
                user_id=user.id,
                account_name="HDFC Savings",
                bank_name="HDFC",
                account_number_mask="*1111",
            )
            acc2 = Account(
                user_id=user.id,
                account_name="SBI Savings",
                bank_name="SBI",
                account_number_mask="*2222",
            )
            session.add(acc1)
            session.add(acc2)
            await session.flush()

            # Insert 2 matching transactions across accounts
            d = date(2024, 6, 1)
            tx1 = Transaction(
                account_id=acc1.id,
                date=d,
                amount=12000.0,
                transaction_type="debit",
                description="Transfer to SBI account",
                is_self_transfer=False,
            )
            tx2 = Transaction(
                account_id=acc2.id,
                date=d,
                amount=12000.0,
                transaction_type="credit",
                description="Transfer from HDFC account",
                is_self_transfer=False,
            )
            session.add(tx1)
            session.add(tx2)
            await session.commit()

            # Run DB detection
            matched = await detect_and_update_self_transfers_db(session=session, user_id=user.id)
            assert len(matched) == 1

            # Verify persisted state
            await session.refresh(tx1)
            await session.refresh(tx2)
            assert tx1.is_self_transfer is True
            assert tx2.is_self_transfer is True
        finally:
            # Clean up test rows
            try:
                if 'tx1' in locals():
                    await session.delete(tx1)
                if 'tx2' in locals():
                    await session.delete(tx2)
                if 'acc1' in locals():
                    await session.delete(acc1)
                if 'acc2' in locals():
                    await session.delete(acc2)
                await session.delete(user)
                await session.commit()
            except Exception:
                await session.rollback()

    await test_engine.dispose()

