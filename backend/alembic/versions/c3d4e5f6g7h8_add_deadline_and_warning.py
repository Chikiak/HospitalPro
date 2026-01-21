"""Add deadline_time and warning_message to category_schedules

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-21 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add deadline_time and warning_message columns to category_schedules."""
    op.add_column('category_schedules', sa.Column('deadline_time', sa.Time(), nullable=True))
    op.add_column('category_schedules', sa.Column('warning_message', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Remove deadline_time and warning_message columns."""
    op.drop_column('category_schedules', 'warning_message')
    op.drop_column('category_schedules', 'deadline_time')
