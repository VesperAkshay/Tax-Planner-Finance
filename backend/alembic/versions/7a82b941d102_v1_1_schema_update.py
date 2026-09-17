"""v1_1_schema_update

Revision ID: 7a82b941d102
Revises: 22ed5cc19d46
Create Date: 2026-09-17 12:45:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '7a82b941d102'
down_revision: Union[str, Sequence[str], None] = '22ed5cc19d46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SEEDED_CATALOG = [
    {
        "id": uuid.uuid4(),
        "section_code": "80C",
        "display_name": "Investments & Insurance (PPF, EPF/VPF, ELSS, life insurance, home loan principal, Sukanya Samriddhi, NSC, 5-yr tax-saver FD, children's tuition)",
        "description": "Combined tax deduction for statutory savings, provident funds, life insurance premiums, pension plans, ELSS mutual funds, and tuition fees under Section 80C.",
        "applicable_regimes": "old_only",
        "cap_type": "fixed",
        "cap_amount": 150000.0,
        "cap_formula": "min(total_investments, 150000)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80CCD(1B)",
        "display_name": "Additional NPS (self-contribution)",
        "description": "Additional voluntary employee contribution to National Pension System (NPS Tier 1) over and above the Section 80C limit.",
        "applicable_regimes": "old_only",
        "cap_type": "fixed",
        "cap_amount": 50000.0,
        "cap_formula": "min(nps_self_contribution, 50000)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80CCD(2)",
        "display_name": "Employer's NPS contribution",
        "description": "Employer's contribution to employee's NPS account. Deductible under both tax regimes up to 14% of basic salary.",
        "applicable_regimes": "both",
        "cap_type": "percentage_of_salary",
        "cap_amount": None,
        "cap_formula": "min(employer_nps, 0.14 * basic_salary)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80D",
        "display_name": "Health insurance (self/family)",
        "description": "Health insurance premiums paid for self, spouse, and dependent children, including up to ₹5,000 for preventive health checkups.",
        "applicable_regimes": "old_only",
        "cap_type": "age_based",
        "cap_amount": 25000.0,
        "cap_formula": "25000 (below 60) or 50000 (senior citizen)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80D (parents)",
        "display_name": "Health insurance (parents)",
        "description": "Medical insurance premium paid for parents. Additional deduction of ₹25,000 for parents below 60 years or ₹50,000 for senior citizen parents.",
        "applicable_regimes": "old_only",
        "cap_type": "age_based",
        "cap_amount": 50000.0,
        "cap_formula": "25000 (below 60) or 50000 (senior citizen)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80DD",
        "display_name": "Maintenance/treatment of disabled dependent",
        "description": "Deduction for medical treatment, nursing, training, and rehabilitation of a dependent with disability (₹75,000 for 40%-80% disability, ₹1,25,000 for severe disability >80%).",
        "applicable_regimes": "old_only",
        "cap_type": "severity_based",
        "cap_amount": 125000.0,
        "cap_formula": "75000 (disability >= 40%) or 125000 (severe >= 80%)",
        "requires_eligibility_check": True,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80DDB",
        "display_name": "Treatment for specified diseases",
        "description": "Medical expenditure incurred on treatment of specified chronic diseases/ailments (e.g. cancer, neurological diseases) for self or dependent (₹40,000 or ₹1,00,000 for senior citizens).",
        "applicable_regimes": "old_only",
        "cap_type": "age_based",
        "cap_amount": 100000.0,
        "cap_formula": "min(actual_expense, 40000 if age < 60 else 100000)",
        "requires_eligibility_check": True,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80E",
        "display_name": "Education loan interest",
        "description": "Interest paid on loan taken for higher education of self, spouse, or children. Available for up to 8 consecutive years with no upper monetary cap.",
        "applicable_regimes": "old_only",
        "cap_type": "no_cap",
        "cap_amount": None,
        "cap_formula": "actual_interest_paid",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80EEA",
        "display_name": "Additional home loan interest (first-time buyers)",
        "description": "Additional interest deduction up to ₹1,50,000 for first-time home buyers for affordable housing sanctioned between 01-Apr-2019 and 31-Mar-2022 (stamp value <= ₹45L).",
        "applicable_regimes": "old_only",
        "cap_type": "fixed",
        "cap_amount": 150000.0,
        "cap_formula": "min(interest_paid_above_24b, 150000)",
        "requires_eligibility_check": True,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80G",
        "display_name": "Donations to eligible institutions",
        "description": "Donations to specified charitable funds and relief funds. 50% or 100% deduction subject to qualifying limits and 80G registration certificates.",
        "applicable_regimes": "old_only",
        "cap_type": "formula",
        "cap_amount": None,
        "cap_formula": "percentage_eligible_donation(institution, amount)",
        "requires_eligibility_check": True,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80GG",
        "display_name": "Rent paid, no HRA in salary",
        "description": "Deduction for rent paid by an individual who does not receive House Rent Allowance (HRA) from employer and does not own residential accommodation in the city.",
        "applicable_regimes": "old_only",
        "cap_type": "formula",
        "cap_amount": 60000.0,
        "cap_formula": "min(5000 * months, rent - 0.10 * total_income, 0.25 * total_income)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80GGC",
        "display_name": "Donations to political parties",
        "description": "Deduction for any sum contributed to a registered political party or electoral trust (non-cash payments only).",
        "applicable_regimes": "old_only",
        "cap_type": "no_cap",
        "cap_amount": None,
        "cap_formula": "actual_donation_non_cash",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80TTA",
        "display_name": "Savings account interest (general)",
        "description": "Deduction up to ₹10,000 on interest earned from savings bank accounts held with banks, co-operative societies, or post office (individuals below 60).",
        "applicable_regimes": "old_only",
        "cap_type": "fixed",
        "cap_amount": 10000.0,
        "cap_formula": "min(savings_interest, 10000)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80TTB",
        "display_name": "Savings account interest (senior citizens)",
        "description": "Deduction up to ₹50,000 for senior citizens (age 60+) on interest income from deposits (both savings and fixed/recurring deposits).",
        "applicable_regimes": "old_only",
        "cap_type": "fixed",
        "cap_amount": 50000.0,
        "cap_formula": "min(total_interest_income, 50000)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "80U",
        "display_name": "Self disability",
        "description": "Fixed deduction for resident individual certified with a disability (₹75,000 for disability >= 40%, ₹1,25,000 for severe disability >= 80%).",
        "applicable_regimes": "old_only",
        "cap_type": "severity_based",
        "cap_amount": 125000.0,
        "cap_formula": "75000 (disability >= 40%) or 125000 (severe >= 80%)",
        "requires_eligibility_check": True,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "24(b)",
        "display_name": "Home loan interest, self-occupied",
        "description": "Interest payable on borrowed capital for acquisition or construction of self-occupied house property (capped at ₹2,00,000).",
        "applicable_regimes": "old_only",
        "cap_type": "fixed",
        "cap_amount": 200000.0,
        "cap_formula": "min(home_loan_interest, 200000)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "10(13A)",
        "display_name": "HRA exemption",
        "description": "House Rent Allowance exemption under Section 10(13A) calculated as the least of: actual HRA received, rent paid excess of 10% salary, or 50%/40% of basic salary.",
        "applicable_regimes": "old_only",
        "cap_type": "formula",
        "cap_amount": None,
        "cap_formula": "least(actual_hra, rent - 0.10*basic, metro_pct*basic)",
        "requires_eligibility_check": False,
    },
    {
        "id": uuid.uuid4(),
        "section_code": "10(5)",
        "display_name": "LTA exemption",
        "description": "Leave Travel Allowance exemption for travel within India for self and family, eligible for two journeys in a block of four calendar years against actual travel tickets.",
        "applicable_regimes": "old_only",
        "cap_type": "employer_defined",
        "cap_amount": None,
        "cap_formula": "min(actual_travel_expense, lta_received)",
        "requires_eligibility_check": False,
    },
]


def upgrade() -> None:
    # 1. Extend user_declared_deductions with status column
    op.add_column(
        'user_declared_deductions',
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False, server_default='declared'),
    )

    # 2. Create deduction_catalog table
    deduction_catalog_table = op.create_table(
        'deduction_catalog',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('section_code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('display_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('applicable_regimes', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default='old_only'),
        sa.Column('cap_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False, server_default='fixed'),
        sa.Column('cap_amount', sa.Float(), nullable=True),
        sa.Column('cap_formula', sa.Text(), nullable=True),
        sa.Column('requires_eligibility_check', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_deduction_catalog_section_code'), 'deduction_catalog', ['section_code'], unique=True)

    # 3. Create elicitation_progress table
    op.create_table(
        'elicitation_progress',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('financial_year', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('section_code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('state', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default='pending'),
        sa.Column('skip_reason', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_elicitation_progress_financial_year'), 'elicitation_progress', ['financial_year'], unique=False)
    op.create_index(op.f('ix_elicitation_progress_section_code'), 'elicitation_progress', ['section_code'], unique=False)
    op.create_index(op.f('ix_elicitation_progress_user_id'), 'elicitation_progress', ['user_id'], unique=False)

    # 4. Extend statement_uploads with date_range_start & date_range_end
    op.add_column('statement_uploads', sa.Column('date_range_start', sa.Date(), nullable=True))
    op.add_column('statement_uploads', sa.Column('date_range_end', sa.Date(), nullable=True))

    # 5. Extend transactions with financial_year
    op.add_column('transactions', sa.Column('financial_year', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True))
    op.create_index(op.f('ix_transactions_financial_year'), 'transactions', ['financial_year'], unique=False)

    # 6. Seed deduction_catalog with all 18 canonical sections
    op.bulk_insert(deduction_catalog_table, SEEDED_CATALOG)


def downgrade() -> None:
    op.drop_index(op.f('ix_transactions_financial_year'), table_name='transactions')
    op.drop_column('transactions', 'financial_year')

    op.drop_column('statement_uploads', 'date_range_end')
    op.drop_column('statement_uploads', 'date_range_start')

    op.drop_index(op.f('ix_elicitation_progress_user_id'), table_name='elicitation_progress')
    op.drop_index(op.f('ix_elicitation_progress_section_code'), table_name='elicitation_progress')
    op.drop_index(op.f('ix_elicitation_progress_financial_year'), table_name='elicitation_progress')
    op.drop_table('elicitation_progress')

    op.drop_index(op.f('ix_deduction_catalog_section_code'), table_name='deduction_catalog')
    op.drop_table('deduction_catalog')

    op.drop_column('user_declared_deductions', 'status')
