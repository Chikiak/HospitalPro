"""Fix category_schedules unique constraint to be on name+day_of_week

Revision ID: b2c3d4e5f6g7
Revises: 1d415741cff2
Create Date: 2026-01-21 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = '1d415741cff2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change unique constraint from (category_type, day_of_week) to (name, day_of_week)."""
    # Drop the old constraint
    op.drop_constraint('uq_category_schedules_category_type_day_of_week', 'category_schedules', type_='unique')
    
    # Add the new constraint allowing multiple specialties/labs on the same day
    op.create_unique_constraint(
        'uq_category_schedules_name_day_of_week',
        'category_schedules',
        ['name', 'day_of_week']
    )


def downgrade() -> None:
    """Revert to the old constraint."""
    op.drop_constraint('uq_category_schedules_name_day_of_week', 'category_schedules', type_='unique')
    op.create_unique_constraint(
        'uq_category_schedules_category_type_day_of_week',
        'category_schedules',
        ['category_type', 'day_of_week']
    )
