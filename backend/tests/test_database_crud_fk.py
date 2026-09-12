from datetime import date, datetime, timezone
import pytest
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    Account,
    Category,
    ReconciliationFlag,
    SalarySlip,
    StatementUpload,
    TaxComputation,
    TaxRuleVersion,
    Transaction,
    User,
    UserDeclaredDeduction,
)


@pytest.fixture(name="db_session")
def db_session_fixture():
    # SQLite in-memory with foreign keys explicitly enabled
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


def test_insert_and_read_all_ten_tables(db_session: Session):
    """Task 1.7: Insert one row per table, read it back, confirm data integrity."""

    # 1. User
    user = User(
        email="testuser@taxplanner.local",
        hashed_password="hashed_pw_secret_123",
        full_name="Akshay Test",
        pan="ABCDE1234F",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    assert user.id is not None

    user_read = db_session.exec(select(User).where(User.id == user.id)).first()
    assert user_read is not None
    assert user_read.email == "testuser@taxplanner.local"

    # 2. Account (FK -> User)
    account = Account(
        user_id=user.id,
        account_name="HDFC Main",
        bank_name="HDFC Bank",
        account_number_mask="XX9876",
        account_type="savings",
        currency="INR",
        current_balance=75000.0,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    assert account.id is not None

    account_read = db_session.exec(select(Account).where(Account.id == account.id)).first()
    assert account_read is not None
    assert account_read.account_name == "HDFC Main"

    # 3. Category
    category = Category(
        name="Dining",
        description="Restaurants and Food Delivery",
        is_income=False,
        is_system=True,
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    assert category.id is not None

    cat_read = db_session.exec(select(Category).where(Category.id == category.id)).first()
    assert cat_read is not None
    assert cat_read.name == "Dining"

    # 4. StatementUpload (FK -> User, Account)
    upload = StatementUpload(
        user_id=user.id,
        account_id=account.id,
        file_name="hdfc_statement_may2025.pdf",
        file_path="/storage/statements/hdfc_may2025.pdf",
        file_type="pdf_text",
        file_hash="abc123hash",
        parse_status="completed",
        parse_confidence=0.98,
        balance_reconciled=True,
        opening_balance=50000.0,
        closing_balance=75000.0,
        statement_start_date=date(2025, 5, 1),
        statement_end_date=date(2025, 5, 31),
        needs_review=False,
    )
    db_session.add(upload)
    db_session.commit()
    db_session.refresh(upload)
    assert upload.id is not None

    upload_read = db_session.exec(select(StatementUpload).where(StatementUpload.id == upload.id)).first()
    assert upload_read is not None
    assert upload_read.file_name == "hdfc_statement_may2025.pdf"

    # 5. Transaction (FK -> Account, Upload, Category)
    tx = Transaction(
        account_id=account.id,
        upload_id=upload.id,
        category_id=category.id,
        date=date(2025, 5, 10),
        description="UPI/SWIGGY/123456",
        cleaned_description="Swiggy Food Order",
        amount=540.0,
        transaction_type="debit",
        balance=74460.0,
        reference_number="UPI123456789",
        parse_confidence=0.99,
        parse_status="parsed",
        balance_reconciled=True,
        category_confidence=0.94,
        is_self_transfer=False,
        needs_review=False,
    )
    db_session.add(tx)
    db_session.commit()
    db_session.refresh(tx)
    assert tx.id is not None

    tx_read = db_session.exec(select(Transaction).where(Transaction.id == tx.id)).first()
    assert tx_read is not None
    assert tx_read.amount == 540.0

    # 6. SalarySlip (FK -> User)
    slip = SalarySlip(
        user_id=user.id,
        file_name="payslip_may_2025.pdf",
        file_path="/storage/slips/may_2025.pdf",
        month=5,
        year=2025,
        financial_year="2025-2026",
        basic=70000.0,
        hra=35000.0,
        lta=5000.0,
        special_allowance=30000.0,
        gross_pay=140000.0,
        employee_pf=8400.0,
        employer_pf=8400.0,
        professional_tax=200.0,
        tds=12000.0,
        total_deductions=20600.0,
        net_pay=119400.0,
        extraction_confidence=0.98,
        is_gross_valid=True,
        needs_review=False,
    )
    db_session.add(slip)
    db_session.commit()
    db_session.refresh(slip)
    assert slip.id is not None

    slip_read = db_session.exec(select(SalarySlip).where(SalarySlip.id == slip.id)).first()
    assert slip_read is not None
    assert slip_read.net_pay == 119400.0

    # 7. ReconciliationFlag (FK -> User, SalarySlip, Transaction)
    flag = ReconciliationFlag(
        user_id=user.id,
        salary_slip_id=slip.id,
        transaction_id=tx.id,
        month=5,
        year=2025,
        flag_type="mismatched_amount",
        expected_amount=119400.0,
        actual_amount=115000.0,
        difference=4400.0,
        status="pending",
    )
    db_session.add(flag)
    db_session.commit()
    db_session.refresh(flag)
    assert flag.id is not None

    flag_read = db_session.exec(select(ReconciliationFlag).where(ReconciliationFlag.id == flag.id)).first()
    assert flag_read is not None
    assert flag_read.status == "pending"

    # 8. UserDeclaredDeduction (FK -> User)
    ded = UserDeclaredDeduction(
        user_id=user.id,
        financial_year="2025-2026",
        section="80C",
        amount=150000.0,
        source="agent_elicited",
        metadata_json={"elss": 100000.0, "ppf": 50000.0},
    )
    db_session.add(ded)
    db_session.commit()
    db_session.refresh(ded)
    assert ded.id is not None

    ded_read = db_session.exec(select(UserDeclaredDeduction).where(UserDeclaredDeduction.id == ded.id)).first()
    assert ded_read is not None
    assert ded_read.section == "80C"
    assert ded_read.amount == 150000.0

    # 9. TaxRuleVersion
    rule_version = TaxRuleVersion(
        financial_year="2025-2026",
        version_tag="v1.0",
        is_active=True,
        rules={"new_regime": {"standard_deduction": 75000}},
    )
    db_session.add(rule_version)
    db_session.commit()
    db_session.refresh(rule_version)
    assert rule_version.id is not None

    rule_read = db_session.exec(select(TaxRuleVersion).where(TaxRuleVersion.id == rule_version.id)).first()
    assert rule_read is not None
    assert rule_read.financial_year == "2025-2026"

    # 10. TaxComputation (FK -> User)
    computation = TaxComputation(
        user_id=user.id,
        financial_year="2025-2026",
        gross_income=1680000.0,
        old_regime_taxable_income=1430000.0,
        old_regime_tax=241500.0,
        old_regime_cess=9660.0,
        old_regime_total_liability=251160.0,
        new_regime_taxable_income=1605000.0,
        new_regime_tax=141000.0,
        new_regime_cess=5640.0,
        new_regime_total_liability=146640.0,
        recommended_regime="new",
        tax_savings=104520.0,
    )
    db_session.add(computation)
    db_session.commit()
    db_session.refresh(computation)
    assert computation.id is not None

    comp_read = db_session.exec(select(TaxComputation).where(TaxComputation.id == computation.id)).first()
    assert comp_read is not None
    assert comp_read.recommended_regime == "new"
    assert comp_read.tax_savings == 104520.0


def test_foreign_key_rejects_orphaned_account(db_session: Session):
    """Task 1.7: Confirm foreign key constraints reject an orphaned insert."""
    orphaned_account = Account(
        user_id=999999,  # Non-existent user
        account_name="Orphaned Account",
        bank_name="Test Bank",
    )
    db_session.add(orphaned_account)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_foreign_key_rejects_orphaned_transaction(db_session: Session):
    """Task 1.7: Confirm orphaned transaction with invalid account_id is rejected."""
    orphaned_tx = Transaction(
        account_id=888888,  # Non-existent account
        date=date(2025, 5, 1),
        description="Ghost payment",
        amount=100.0,
        transaction_type="debit",
    )
    db_session.add(orphaned_tx)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_foreign_key_rejects_orphaned_salary_slip(db_session: Session):
    """Task 1.7: Confirm orphaned salary slip with invalid user_id is rejected."""
    orphaned_slip = SalarySlip(
        user_id=777777,  # Non-existent user
        file_name="ghost.pdf",
        file_path="/ghost.pdf",
        month=1,
        year=2025,
        gross_pay=50000.0,
        net_pay=45000.0,
    )
    db_session.add(orphaned_slip)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
