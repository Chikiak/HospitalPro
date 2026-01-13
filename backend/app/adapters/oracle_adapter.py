"""Oracle database adapter for patient data.

This module implements the Adapter pattern to integrate with legacy Oracle database.
It translates Oracle-specific operations into the generic PatientProvider interface.
"""
import os
from typing import Optional
from datetime import datetime
import oracledb

from app.schemas.legacy import PatientHistory
from app.exceptions import ServiceUnavailable


class OracleAdapter:
    """Adapter for Oracle legacy database.
    
    This adapter implements the PatientProvider protocol and handles
    connection management, resilience, and data transformation from
    the Oracle database to our domain models.
    """
    
    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        dsn: Optional[str] = None
    ):
        """Initialize the Oracle adapter.
        
        Args:
            user: Oracle database user (defaults to ORACLE_USER env var)
            password: Oracle database password (defaults to ORACLE_PASSWORD env var)
            dsn: Oracle database DSN (defaults to ORACLE_DSN env var)
        """
        self.user = user or os.getenv('ORACLE_USER')
        self.password = password or os.getenv('ORACLE_PASSWORD')
        self.dsn = dsn or os.getenv('ORACLE_DSN')
        
        if not all([self.user, self.password, self.dsn]):
            raise ValueError(
                "Oracle credentials not provided. Set ORACLE_USER, "
                "ORACLE_PASSWORD, and ORACLE_DSN environment variables."
            )
    
    def get_patient_history(self, dni: str) -> Optional[PatientHistory]:
        """Retrieve patient history from Oracle database.
        
        Args:
            dni: Patient DNI/identification number
            
        Returns:
            PatientHistory object if found, None otherwise
            
        Raises:
            ServiceUnavailable: If unable to connect to Oracle database
        """
        try:
            # Use context manager to ensure connection is always closed
            with oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            ) as connection:
                with connection.cursor() as cursor:
                    # Execute query to fetch patient data
                    query = """
                        SELECT 
                            dni,
                            full_name,
                            birth_date,
                            blood_type,
                            allergies,
                            medications,
                            medical_history,
                            last_visit
                        FROM patient_history
                        WHERE dni = :dni
                    """
                    cursor.execute(query, {'dni': dni})
                    row = cursor.fetchone()
                    
                    if row is None:
                        return None
                    
                    # Transform Oracle data to PatientHistory model
                    return self._row_to_patient_history(row, cursor.description)
                    
        except oracledb.Error as e:
            # Convert Oracle-specific errors to generic ServiceUnavailable
            raise ServiceUnavailable(
                f"Failed to connect to Oracle database: {str(e)}"
            ) from e
    
    def _row_to_patient_history(
        self,
        row: tuple,
        description: list
    ) -> PatientHistory:
        """Convert Oracle row to PatientHistory model.
        
        Args:
            row: Database row tuple
            description: Column description from cursor
            
        Returns:
            PatientHistory object
        """
        # Create column name to value mapping
        columns = [desc[0].lower() for desc in description]
        data = dict(zip(columns, row))
        
        # Parse comma-separated strings into lists
        allergies = []
        if data.get('allergies'):
            allergies = [a.strip() for a in data['allergies'].split(',') if a.strip()]
        
        medications = []
        if data.get('medications'):
            medications = [m.strip() for m in data['medications'].split(',') if m.strip()]
        
        # Build PatientHistory object
        return PatientHistory(
            dni=data.get('dni', ''),
            full_name=data.get('full_name', ''),
            birth_date=data.get('birth_date'),
            blood_type=data.get('blood_type'),
            allergies=allergies,
            medications=medications,
            medical_history=data.get('medical_history'),
            last_visit=data.get('last_visit')
        )
