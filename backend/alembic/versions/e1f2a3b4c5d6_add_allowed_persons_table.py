"""Add allowed_persons table

Revision ID: e1f2a3b4c5d6
Revises: 44af4d1fbe4f
Create Date: 2026-02-07 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = '44af4d1fbe4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create allowed_persons table."""
    op.create_table(
        'allowed_persons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dni', sa.String(length=20), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_registered', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_allowed_persons_id'), 'allowed_persons', ['id'], unique=False)
    op.create_index(op.f('ix_allowed_persons_dni'), 'allowed_persons', ['dni'], unique=True)


def downgrade() -> None:
    """Drop allowed_persons table."""
    op.drop_index(op.f('ix_allowed_persons_dni'), table_name='allowed_persons')
    op.drop_index(op.f('ix_allowed_persons_id'), table_name='allowed_persons')
    op.drop_table('allowed_persons')
