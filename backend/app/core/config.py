from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True)
    
    # Database - No defaults for production security
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "hospital_pro"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # Security - Must be set via environment variable (no insecure defaults)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    STAFF_PASSWORD: str  # Obligatorio: sin valor por defecto (F1-05)
    ADMIN_PASSWORD: str  # Obligatorio: sin valor por defecto (F1-05)
    
    # Runtime - configurables por entorno con defaults seguros (F1-05)
    SQL_ECHO: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:5173"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct async database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
