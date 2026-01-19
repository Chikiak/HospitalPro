"""Add category_schedules table

Revision ID: a1b2c3d4e5f6
Revises: z6x2l9jovvi2
Create Date: 2026-01-19 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'z6x2l9jovvi2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create category_schedules table."""
    op.create_table(
        'category_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_type', sa.Enum('specialty', 'laboratory', name='categorytype'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('turn_duration', sa.Integer(), nullable=False),
        sa.Column('max_turns_per_block', sa.Integer(), nullable=False),
        sa.Column('rotation_type', sa.Enum('fixed', 'alternated', name='rotationtype'), nullable=False),
        sa.Column('rotation_weeks', sa.Integer(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_category_schedules_id'), 'category_schedules', ['id'], unique=False)
    op.create_index(op.f('ix_category_schedules_name'), 'category_schedules', ['name'], unique=False)
    
    # Add unique constraint for category_type and day_of_week
    op.create_unique_constraint(
        'uq_category_schedules_category_type_day_of_week',
        'category_schedules',
        ['category_type', 'day_of_week']
    )


def downgrade() -> None:
    """Drop category_schedules table."""
    op.drop_constraint('uq_category_schedules_category_type_day_of_week', 'category_schedules', type_='unique')
    op.drop_index(op.f('ix_category_schedules_name'), table_name='category_schedules')
    op.drop_index(op.f('ix_category_schedules_id'), table_name='category_schedules')
    op.drop_table('category_schedules')
    # Note: Enum types are automatically managed by SQLAlchemy when dropping the table
