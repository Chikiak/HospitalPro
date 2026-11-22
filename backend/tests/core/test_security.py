"""Tests de seguridad para F1-08: JWT (PyJWT) y hashing (bcrypt directo).

Los valores "legados" (LEGACY_JOSE_TOKEN y LEGACY_BCRYPT_HASH) se generaron
una vez con las librerías anteriores (python-jose y passlib/bcrypt 3.2.2) y se
embeben como constantes para verificar que decode_access_token / verify_password
siguen aceptando tokens y hashes creados con la librería antigua.
"""
import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)

# Token JWS HS256 firmado con python-jose, clave de test, exp lejano.
LEGACY_JOSE_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiIxMjM0NTY3OCIsInJvbGUiOiJhZG1pbiIsImV4cCI6NDEwMjM1ODQwMH0."
    "X3ya6DYoNj0FiMqrYvbYgF_U7cedOoZwt5KyOsPUtTY"
)

# Hash bcrypt de "contraseña-legacy" generado con passlib CryptContext(bcrypt).
LEGACY_BCRYPT_HASH = (
    "$2b$12$c5yMyFDOdH4q0y9CKjRaiOBdFgh.bJrmOUOt8QCPLFKOLQyuLnpny"
)


def test_token_roundtrip():
    token = create_access_token({"sub": "12345678", "role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "12345678"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_decode_invalid_token_returns_none():
    assert decode_access_token("not.a.token") is None
    wrong_secret_token = create_access_token({"sub": "1"}, expires_delta=None)
    # Firmado con la clave correcta pero el test de "clave equivocada" se hace
    # construyendo un token con otra clave directamente.
    import jwt

    other = jwt.encode(
        {"sub": "1", "role": "user"},
        "wrong-secret-do-not-use",
        algorithm="HS256",
    )
    assert decode_access_token(other) is None


def test_legacy_token_still_decodes():
    payload = decode_access_token(LEGACY_JOSE_TOKEN)
    assert payload is not None
    assert payload["sub"] == "12345678"
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_password_hash_and_verify():
    h = get_password_hash("testpass123")
    assert h.startswith("$2b$")
    assert verify_password("testpass123", h) is True
    assert verify_password("wrong-password", h) is False


def test_legacy_hash_still_verifies():
    assert verify_password("contraseña-legacy", LEGACY_BCRYPT_HASH) is True
