"""Tests para hash_config_passwords.py (AC4).

Ejecutan convert_key directamente contra la BD de prueba (importando el módulo,
no vía subprocess), con asserts de idempotencia (segunda ejecución no re-hashea).
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select

from app.core.security import verify_password
from app.models.system_config import SystemConfig
from scripts.hash_config_passwords import convert_key, is_bcrypt_hash, main

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.asyncio
async def test_hash_config_passwords_converts_plaintext_and_is_idempotent(test_db, capsys):
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

    # Capturar stdout de la primera ejecución
    out_first = capsys.readouterr().out
    assert "Convertido: staff_password" in out_first
    assert "Convertido: admin_password" in out_first

    # Segunda ejecución: idempotente, no re-hashea
    converted_staff_again = await convert_key(test_db, "staff_password", "mi-password-en-plano")
    converted_admin_again = await convert_key(test_db, "admin_password", "admin-en-plano")
    assert converted_staff_again is False
    assert converted_admin_again is False

    out_second = capsys.readouterr().out
    assert "Ya hasheado: staff_password" in out_second
    assert "Ya hasheado: admin_password" in out_second

    # Los hashes no deben haber cambiado
    result = await test_db.execute(select(SystemConfig).where(SystemConfig.key == "staff_password"))
    staff_config2 = result.scalar_one()
    assert staff_config2.value == staff_config.value

    result = await test_db.execute(select(SystemConfig).where(SystemConfig.key == "admin_password"))
    admin_config2 = result.scalar_one()
    assert admin_config2.value == admin_config.value


@pytest.mark.asyncio
async def test_hash_config_passwords_main_nothing_to_convert(test_db, monkeypatch, capsys):
    """main() sin STAFF_PASSWORD ni ADMIN_PASSWORD devuelve 0 e imprime 'Nada que convertir'."""
    monkeypatch.delenv("STAFF_PASSWORD", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    ret = await main()
    assert ret == 0

    out = capsys.readouterr().out
    assert "Nada que convertir" in out


def test_hash_config_passwords_cli_no_module_not_found(tmp_path, monkeypatch):
    """CLI del script desde la raíz del repo sin PYTHONPATH no falla con ModuleNotFoundError."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    # STAFF_PASSWORD/ADMIN_PASSWORD se definen porque Settings las exige como campos obligatorios.
    # El script intentará conectar a la BD (no disponible aquí) pero nunca debe fallar por
    # ModuleNotFoundError de app.*.
    env["STAFF_PASSWORD"] = "cli-staff-pass-1234"
    env["ADMIN_PASSWORD"] = "cli-admin-pass-1234"
    env["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
    env["POSTGRES_USER"] = "test_user"
    env["POSTGRES_PASSWORD"] = "test_password"
    env["POSTGRES_DB"] = "test_db"
    env["POSTGRES_HOST"] = "localhost"
    env["POSTGRES_PORT"] = "5432"
    env["ALGORITHM"] = "HS256"
    env["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

    script = REPO_ROOT / "backend" / "scripts" / "hash_config_passwords.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert "ModuleNotFoundError" not in result.stderr
    assert "ModuleNotFoundError" not in result.stdout


@pytest.mark.asyncio
async def test_is_bcrypt_hash_detects_plaintext(test_db):
    """is_bcrypt_hash identifica correctamente hashes y texto plano."""
    assert is_bcrypt_hash("$2b$12$abcdefghijklmnopqrstuv") is True
    assert is_bcrypt_hash("texto-en-plano") is False
    assert is_bcrypt_hash(None) is False
    assert is_bcrypt_hash("") is False
