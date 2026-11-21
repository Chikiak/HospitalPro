"""Tests for application settings (F1-05).

Settings are instantiated directly with a monkeypatched environment so no
real secrets are required. The conftest provides test values before the app
is imported; each test controls the variables it needs.

Los tests que construyen Settings ignoran cualquier fichero `.env` local
para ser hermeticos (no dependen de credenciales del entorno del desarrollador).
"""
import pytest
from pydantic import ConfigDict, ValidationError

from app.core.config import Settings


class _SettingsNoEnvFile(Settings):
    """Settings que ignora el .env local para pruebas hermeticas."""
    model_config = ConfigDict(env_file="")


def test_settings_requires_secrets(monkeypatch):
    """AC1: arrancar sin SECRET_KEY/ADMIN_PASSWORD/STAFF_PASSWORD falla con ValidationError."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("STAFF_PASSWORD", raising=False)
    with pytest.raises(ValidationError) as excinfo:
        _SettingsNoEnvFile()
    missing = {str(e["loc"][0]) for e in excinfo.value.errors()}
    assert {"SECRET_KEY", "ADMIN_PASSWORD", "STAFF_PASSWORD"} <= missing


def test_settings_defaults_correct():
    """AC4/AC6: con entorno de pruebas, SQL_ECHO desactivado y ALLOWED_ORIGINS por defecto."""
    settings = Settings()
    assert settings.SQL_ECHO is False
    assert settings.ALLOWED_ORIGINS == "http://localhost:5173"


def test_database_echo_defaults_false():
    """AC4: sin variable SQL_ECHO, el motor no hace echo."""
    settings = Settings()
    assert settings.SQL_ECHO is False


def test_database_echo_can_be_enabled(monkeypatch):
    """AC4: con SQL_ECHO=true, el motor hace echo."""
    monkeypatch.setenv("SQL_ECHO", "true")
    settings = Settings()
    assert settings.SQL_ECHO is True
