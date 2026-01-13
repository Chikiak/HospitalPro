"""Tests for Oracle adapter implementation.

These tests use mocks to avoid connecting to a real Oracle database.
All database interactions are strictly mocked to ensure tests are fast,
reliable, and don't depend on external services.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.adapters.oracle_adapter import OracleAdapter
from app.schemas.legacy import PatientHistory
from app.exceptions import ServiceUnavailable


class TestOracleAdapter:
    """Test suite for OracleAdapter class."""
    
    @pytest.fixture
    def adapter(self):
        """Create an OracleAdapter instance for testing."""
        return OracleAdapter(
            user='test_user',
            password='test_password',
            dsn='test_dsn'
        )
    
    def test_initialization_with_parameters(self):
        """Test adapter initialization with explicit parameters."""
        adapter = OracleAdapter(
            user='test_user',
            password='test_password',
            dsn='test_dsn'
        )
        assert adapter.user == 'test_user'
        assert adapter.password == 'test_password'
        assert adapter.dsn == 'test_dsn'
    
    def test_initialization_with_env_vars(self):
        """Test adapter initialization using environment variables."""
        with patch.dict('os.environ', {
            'ORACLE_USER': 'env_user',
            'ORACLE_PASSWORD': 'env_password',
            'ORACLE_DSN': 'env_dsn'
        }):
            adapter = OracleAdapter()
            assert adapter.user == 'env_user'
            assert adapter.password == 'env_password'
            assert adapter.dsn == 'env_dsn'
    
    def test_initialization_missing_credentials(self):
        """Test that initialization fails when credentials are missing."""
        with pytest.raises(ValueError, match="Oracle credentials not provided"):
            OracleAdapter()
    
    @patch('app.adapters.oracle_adapter.oracledb.connect')
    def test_connection_failure_raises_service_unavailable(
        self,
        mock_connect,
        adapter
    ):
        """Test that connection failures raise ServiceUnavailable exception.
        
        This verifies that Oracle-specific errors are abstracted away
        and the application receives a generic ServiceUnavailable exception.
        """
        import oracledb
        
        # Simulate connection failure
        mock_connect.side_effect = oracledb.Error("Connection timeout")
        
        with pytest.raises(ServiceUnavailable, match="Failed to connect to Oracle database"):
            adapter.get_patient_history("12345678")
    
    @patch('app.adapters.oracle_adapter.oracledb.connect')
    def test_empty_result_returns_none(self, mock_connect, adapter):
        """Test that empty query results return None.
        
        When a patient is not found in the database, the adapter
        should return None rather than raising an exception.
        """
        # Create mock connection and cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        
        mock_connection = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value.__exit__.return_value = None
        
        mock_connect.return_value = mock_connection
        
        result = adapter.get_patient_history("99999999")
        
        assert result is None
        mock_cursor.execute.assert_called_once()
    
    @patch('app.adapters.oracle_adapter.oracledb.connect')
    def test_successful_patient_retrieval(self, mock_connect, adapter):
        """Test successful retrieval of patient data from Oracle database."""
        # Mock database row
        mock_row = (
            '12345678',  # dni
            '  John Doe  ',  # full_name (with whitespace to test sanitization)
            datetime(1980, 5, 15),  # birth_date
            ' O+ ',  # blood_type (with whitespace)
            'Penicillin, Aspirin ',  # allergies (comma-separated)
            'Metformin, Lisinopril',  # medications
            '  Previous surgery in 2020  ',  # medical_history
            datetime(2023, 12, 1)  # last_visit
        )
        
        # Mock column descriptions
        mock_description = [
            ('DNI',), ('FULL_NAME',), ('BIRTH_DATE',), ('BLOOD_TYPE',),
            ('ALLERGIES',), ('MEDICATIONS',), ('MEDICAL_HISTORY',), ('LAST_VISIT',)
        ]
        
        # Create mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = mock_row
        mock_cursor.description = mock_description
        
        # Create mock connection
        mock_connection = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value.__exit__.return_value = None
        
        mock_connect.return_value = mock_connection
        
        # Execute
        result = adapter.get_patient_history("12345678")
        
        # Verify
        assert result is not None
        assert isinstance(result, PatientHistory)
        assert result.dni == '12345678'
        assert result.full_name == 'John Doe'  # Whitespace stripped
        assert result.birth_date == datetime(1980, 5, 15)
        assert result.blood_type == 'O+'  # Whitespace stripped
        assert result.allergies == ['Penicillin', 'Aspirin']  # Parsed and stripped
        assert result.medications == ['Metformin', 'Lisinopril']
        assert result.medical_history == 'Previous surgery in 2020'  # Whitespace stripped
        assert result.last_visit == datetime(2023, 12, 1)
        
        # Verify query was executed with correct DNI
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert 'dni' in call_args[0][1]
        assert call_args[0][1]['dni'] == '12345678'
    
    @patch('app.adapters.oracle_adapter.oracledb.connect')
    def test_connection_context_manager_closes_on_error(self, mock_connect, adapter):
        """Test that connections are properly closed even when errors occur.
        
        This verifies that the context manager pattern ensures resources
        are cleaned up even in error scenarios.
        """
        import oracledb
        
        # Create a mock connection that raises an error during query
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = oracledb.Error("Query execution failed")
        
        mock_connection = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value.__exit__.return_value = None
        
        mock_connect.return_value = mock_connection
        
        # Attempt to get patient history
        with pytest.raises(ServiceUnavailable):
            adapter.get_patient_history("12345678")
        
        # Verify context manager's __exit__ was called
        mock_connection.__exit__.assert_called()
    
    @patch('app.adapters.oracle_adapter.oracledb.connect')
    def test_empty_allergies_and_medications(self, mock_connect, adapter):
        """Test handling of empty/null allergies and medications fields."""
        mock_row = (
            '12345678',
            'Jane Smith',
            datetime(1990, 3, 20),
            'A+',
            None,  # No allergies
            '',    # Empty medications
            'Healthy',
            datetime(2024, 1, 10)
        )
        
        mock_description = [
            ('DNI',), ('FULL_NAME',), ('BIRTH_DATE',), ('BLOOD_TYPE',),
            ('ALLERGIES',), ('MEDICATIONS',), ('MEDICAL_HISTORY',), ('LAST_VISIT',)
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = mock_row
        mock_cursor.description = mock_description
        
        mock_connection = MagicMock()
        mock_connection.__enter__.return_value = mock_connection
        mock_connection.__exit__.return_value = None
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connection.cursor.return_value.__exit__.return_value = None
        
        mock_connect.return_value = mock_connection
        
        result = adapter.get_patient_history("12345678")
        
        assert result is not None
        assert result.allergies == []
        assert result.medications == []
