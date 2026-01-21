"""Merge multiple heads

Revision ID: 1d415741cff2
Revises: 89d56489277a, a1b2c3d4e5f6
Create Date: 2026-01-19 19:34:03.116166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d415741cff2'
down_revision: Union[str, Sequence[str], None] = ('89d56489277a', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
