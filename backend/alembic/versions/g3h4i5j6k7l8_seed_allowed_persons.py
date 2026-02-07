"""Seed allowed_persons with test DNIs

Revision ID: g3h4i5j6k7l8
Revises: f2g3h4i5j6k7
Create Date: 2026-02-07 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g3h4i5j6k7l8'
down_revision: Union[str, Sequence[str], None] = 'f2g3h4i5j6k7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Seed allowed_persons table with test DNIs."""
    # Generate 60 test DNIs in the format of 11 digits
    test_persons = []
    
    # First 10 with names
    for i in range(10):
        dni = f"{20000000000 + i}"
        full_name = f"Paciente Prueba {i+1}"
        test_persons.append({"dni": dni, "full_name": full_name})
    
    # Next 50 without names
    for i in range(10, 60):
        dni = f"{20000000000 + i}"
        test_persons.append({"dni": dni, "full_name": None})
    
    # Insert test DNIs
    op.bulk_insert(
        sa.table(
            'allowed_persons',
            sa.column('dni', sa.String),
            sa.column('full_name', sa.String),
            sa.column('is_registered', sa.Boolean),
        ),
        [
            {
                'dni': person['dni'],
                'full_name': person['full_name'],
                'is_registered': False
            }
            for person in test_persons
        ]
    )


def downgrade() -> None:
    """Remove seed data from allowed_persons table."""
    # Delete all test DNIs starting with "20000000"
    op.execute(
        "DELETE FROM allowed_persons WHERE dni LIKE '20000000%'"
    )
