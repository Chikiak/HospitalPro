"""Add medical_records table

Revision ID: f2g3h4i5j6k7
Revises: e1f2a3b4c5d6
Create Date: 2026-02-07 18:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f2g3h4i5j6k7'
down_revision: Union[str, Sequence[str], None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create medical_records table."""
    op.create_table(
        'medical_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('registration_survey', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('entries', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text("timezone('UTC', now())"), nullable=False),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text("timezone('UTC', now())"), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medical_records_id'), 'medical_records', ['id'], unique=False)
    op.create_index(op.f('ix_medical_records_patient_id'), 'medical_records', ['patient_id'], unique=True)


def downgrade() -> None:
    """Drop medical_records table."""
    op.drop_index(op.f('ix_medical_records_patient_id'), table_name='medical_records')
    op.drop_index(op.f('ix_medical_records_id'), table_name='medical_records')
    op.drop_table('medical_records')
