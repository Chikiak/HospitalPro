"""Custom exceptions for the application."""


class ServiceUnavailable(Exception):
    """Exception raised when an external service is unavailable.
    
    This exception is used to abstract away implementation details
    of external services (like Oracle DB) from the rest of the application.
    """
    pass
