"""Refactor TriageData fields

Revision ID: z6x2l9jovvi2
Revises: 87050a2c6794
Create Date: 2026-01-19 16:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z6x2l9jovvi2'
down_revision: Union[str, Sequence[str], None] = '87050a2c6794'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Modify triage_data table: change medical_history to JSON and add last_updated."""
    # Add last_updated column with default value (UTC timestamp)
    op.add_column('triage_data', sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.func.timezone('UTC', sa.func.now())))
    
    # Create a trigger to automatically update last_updated on row modifications
    op.execute("""
        CREATE OR REPLACE FUNCTION update_triage_data_last_updated()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.last_updated = timezone('UTC', now());
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER triage_data_last_updated_trigger
        BEFORE UPDATE ON triage_data
        FOR EACH ROW
        EXECUTE FUNCTION update_triage_data_last_updated();
    """)
    
    # Change medical_history from Text to JSON
    # First, we need to handle existing data - convert text to JSON format
    # For PostgreSQL, we can use ALTER COLUMN with USING clause
    op.execute("""
        ALTER TABLE triage_data 
        ALTER COLUMN medical_history TYPE JSON 
        USING CASE 
            WHEN medical_history IS NULL THEN NULL
            WHEN medical_history = '' THEN NULL
            ELSE json_build_object('legacy_text', medical_history)
        END
    """)


def downgrade() -> None:
    """Revert triage_data table changes: change medical_history to Text and remove last_updated."""
    # Convert JSON back to Text, extracting legacy_text field if it exists
    op.execute("""
        ALTER TABLE triage_data 
        ALTER COLUMN medical_history TYPE TEXT 
        USING CASE 
            WHEN medical_history IS NULL THEN NULL
            WHEN medical_history ? 'legacy_text' THEN medical_history->>'legacy_text'
            ELSE medical_history::TEXT
        END
    """)
    
    # Drop the trigger and function
    op.execute("""
        DROP TRIGGER IF EXISTS triage_data_last_updated_trigger ON triage_data;
        DROP FUNCTION IF EXISTS update_triage_data_last_updated();
    """)
    
    # Remove last_updated column
    op.drop_column('triage_data', 'last_updated')
