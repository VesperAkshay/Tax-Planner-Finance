"""create_user_llm_keys

Revision ID: c4e5f6a7b8c9
Revises: 7a82b941d102
Create Date: 2026-09-18 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = '7a82b941d102'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_llm_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=120), nullable=False),
        sa.Column('custom_base_url', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('encrypted_key', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_llm_keys_provider'), 'user_llm_keys', ['provider'], unique=False)
    op.create_index(op.f('ix_user_llm_keys_user_id'), 'user_llm_keys', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_llm_keys_user_id'), table_name='user_llm_keys')
    op.drop_index(op.f('ix_user_llm_keys_provider'), table_name='user_llm_keys')
    op.drop_table('user_llm_keys')
