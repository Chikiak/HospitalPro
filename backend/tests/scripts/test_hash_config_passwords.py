"""Tests para hash_config_passwords.py (AC4).

Ejecutan convert_key directamente contra la BD de prueba (importando el módulo,
no vía subprocess), con asserts de idempotencia (segunda ejecución no re-hashea).
"""

import pytest
from sqlalchemy import select

from app.core.security import verify_password
from app.models.system_config import SystemConfig
from scripts.hash_config_passwords import convert_key, is_bcrypt_hash


@pytest.mark.asyncio
async def test_hash_config_passwords_converts_plaintext_and_is_idempotent(test_db):
    """AC4: convierte texto plano a hash, es idempotente e informa por stdout."""
    # Simular valores en texto plano ya existentes en system_config
    test_db.add(SystemConfig(key="staff_password", value="mi-password-en-plano"))
    test_db.add(SystemConfig(key="admin_password", value="admin-en-plano"))
    await test_db.commit()

    # Primera ejecución: convierte ambos
    converted_staff = await convert_key(test_db, "staff_password", "mi-password-en-plano")
    converted_admin = await convert_key(test_db, "admin_password", "admin-en-plano")
    assert converted_staff is True
    assert converted_admin is True

    # Verificar que los valores ahora son hashes bcrypt válidos
    result = await test_db.execute(select(SystemConfig).where(SystemConfig.key == "staff_password"))
    staff_config = result.scalar_one()
    assert staff_config.value.startswith("$2b$")
    assert verify_password("mi-password-en-plano", staff_config.value) is True

    result = await test_db.execute(select(SystemConfig).where(SystemConfig.key == "admin_password"))
    admin_config = result.scalar_one()
    assert admin_config.value.startswith("$2b$")
    assert verify_password("admin-en-plano", admin_config.value) is True

    # Segunda ejecución: idempotente, no re-hashea
    converted_staff_again = await convert_key(test_db, "staff_password", "mi-password-en-plano")
    converted_admin_again = await convert_key(test_db, "admin_password", "admin-en-plano")
    assert converted_staff_again is False
    assert converted_admin_again is False

    # Los hashes no deben haber cambiado
    result = await test_db.execute(select(SystemConfig).where(SystemConfig.key == "staff_password"))
    staff_config2 = result.scalar_one()
    assert staff_config2.value == staff_config.value

    result = await test_db.execute(select(SystemConfig).where(SystemConfig.key == "admin_password"))
    admin_config2 = result.scalar_one()
    assert admin_config2.value == admin_config.value


@pytest.mark.asyncio
async def test_is_bcrypt_hash_detects_plaintext(test_db):
    """is_bcrypt_hash identifica correctamente hashes y texto plano."""
    assert is_bcrypt_hash("$2b$12$abcdefghijklmnopqrstuv") is True
    assert is_bcrypt_hash("texto-en-plano") is False
    assert is_bcrypt_hash(None) is False
    assert is_bcrypt_hash("") is False
