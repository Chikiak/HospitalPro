"""Rate limiting configuration using slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
# Default limit: 200 requests per minute for general endpoints
# Specific endpoints will have their own stricter limits
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
