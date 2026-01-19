"""Add STAFF role to UserRole enum

Revision ID: 89d56489277a
Revises: 87050a2c6794
Create Date: 2026-01-19 16:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89d56489277a'
down_revision: Union[str, Sequence[str], None] = '87050a2c6794'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add STAFF to UserRole enum."""
    # For PostgreSQL, we need to use ALTER TYPE to add a new enum value
    op.execute('ALTER TYPE "userrole" ADD VALUE IF NOT EXISTS \'staff\'')


def downgrade() -> None:
    """Remove STAFF from UserRole enum.
    
    Note: PostgreSQL does not support removing enum values directly.
    This would require recreating the enum type and updating all tables.
    For safety, we leave this as a no-op.
    """
    pass
