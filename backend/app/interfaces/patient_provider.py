"""Patient data provider interface.

This module defines the port (interface) for patient data providers.
The rest of the application should depend on this interface, not on
specific implementations (like Oracle adapter).
"""
from typing import Protocol, Optional
from app.schemas.legacy import PatientHistory


class PatientProvider(Protocol):
    """Protocol for patient data providers.
    
    This is the port in the Adapter pattern. Different adapters
    (Oracle, MySQL, REST API, etc.) can implement this interface.
    """
    
    def get_patient_history(self, dni: str) -> Optional[PatientHistory]:
        """Retrieve patient history by DNI.
        
        Args:
            dni: Patient DNI/identification number
            
        Returns:
            PatientHistory object if found, None otherwise
            
        Raises:
            ServiceUnavailable: If the service is unavailable
        """
        ...
