from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.endpoints import admin
from app.api.endpoints import auth
from app.api.endpoints import appointments
from app.api.endpoints import patients
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(title="SGT-H API", version="0.1.0", lifespan=lifespan)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Middlewares
# Note: Middleware is applied in reverse order (last added = outermost layer)
# We want: HTTPS Redirect -> Trusted Host -> CORS

# Get environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# HTTPS Redirect Middleware - Forces all HTTP traffic to HTTPS (301 redirect)
# Only enabled in production (when ENVIRONMENT is set to 'production')
if ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Trusted Host Middleware - Prevents HTTP Host Header attacks
# Configure allowed hosts based on environment
if ENVIRONMENT == "production":
    # In production, ALLOWED_HOSTS must be explicitly set
    allowed_hosts_env = os.getenv("ALLOWED_HOSTS", "")
    if not allowed_hosts_env:
        raise ValueError(
            "ALLOWED_HOSTS environment variable must be set in production mode. "
            "Example: ALLOWED_HOSTS=api.hospital.com,hospital.com"
        )
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(",") if host.strip()]
else:
    # In development, use localhost by default but allow override
    allowed_hosts_env = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(",") if host.strip()]
    # Add wildcard support for development for easier testing
    ALLOWED_HOSTS.append("*")

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS
)

# Configure CORS
origins = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to SGT-H API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Include routers
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(patients.router)
