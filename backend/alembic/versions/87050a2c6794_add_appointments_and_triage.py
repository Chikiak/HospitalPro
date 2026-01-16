"""Add appointments and triage

Revision ID: 87050a2c6794
Revises: 4ef77cb7ca41
Create Date: 2026-01-16 15:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87050a2c6794'
down_revision: Union[str, Sequence[str], None] = '4ef77cb7ca41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create triage_data, appointments, and doctor_availability tables."""
    # Create triage_data table
    op.create_table('triage_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('medical_history', sa.Text(), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_triage_data_id'), 'triage_data', ['id'], unique=False)
    op.create_index(op.f('ix_triage_data_patient_id'), 'triage_data', ['patient_id'], unique=False)
    
    # Create appointments table
    op.create_table('appointments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('appointment_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('scheduled', 'confirmed', 'cancelled', 'completed', name='appointmentstatus'), nullable=False),
        sa.Column('specialty', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointments_appointment_date'), 'appointments', ['appointment_date'], unique=False)
    op.create_index(op.f('ix_appointments_doctor_id'), 'appointments', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_appointments_id'), 'appointments', ['id'], unique=False)
    op.create_index(op.f('ix_appointments_patient_id'), 'appointments', ['patient_id'], unique=False)
    op.create_index(op.f('ix_appointments_specialty'), 'appointments', ['specialty'], unique=False)
    
    # Create doctor_availability table
    op.create_table('doctor_availability',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Enum('0', '1', '2', '3', '4', '5', '6', name='dayofweek'), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('specialty', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_doctor_availability_doctor_id'), 'doctor_availability', ['doctor_id'], unique=False)
    op.create_index(op.f('ix_doctor_availability_id'), 'doctor_availability', ['id'], unique=False)


def downgrade() -> None:
    """Drop triage_data, appointments, and doctor_availability tables."""
    # Drop doctor_availability table
    op.drop_index(op.f('ix_doctor_availability_id'), table_name='doctor_availability')
    op.drop_index(op.f('ix_doctor_availability_doctor_id'), table_name='doctor_availability')
    op.drop_table('doctor_availability')
    
    # Drop appointments table
    op.drop_index(op.f('ix_appointments_specialty'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_patient_id'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_id'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_doctor_id'), table_name='appointments')
    op.drop_index(op.f('ix_appointments_appointment_date'), table_name='appointments')
    op.drop_table('appointments')
    
    # Drop triage_data table
    op.drop_index(op.f('ix_triage_data_patient_id'), table_name='triage_data')
    op.drop_index(op.f('ix_triage_data_id'), table_name='triage_data')
    op.drop_table('triage_data')
