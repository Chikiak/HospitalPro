"""Tests para create_admin.py (AC5, AC6).

Ejecutan ensure_admin/ensure_staff directamente contra la BD de prueba
(importando el módulo, no vía subprocess), con asserts de idempotencia.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.security import verify_password
from app.models.user import User, UserRole
from scripts.create_admin import ensure_admin, ensure_staff, main

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.asyncio
async def test_create_admin_idempotent(test_db):
    """AC5: ejecutado dos veces no crea duplicados."""
    user1 = await ensure_admin(test_db, "12345678901", "AdminPass1234", "Admin Uno")
    assert user1.role == UserRole.ADMIN
    assert user1.is_active is True
    assert verify_password("AdminPass1234", user1.hashed_password) is True

    # Segunda ejecución: idempotente, devuelve el mismo usuario
    user2 = await ensure_admin(test_db, "12345678901", "AdminPass1234", "Admin Uno")
    assert user2.id == user1.id

    # No hay duplicados en BD
    result = await test_db.execute(select(User).where(User.dni == "12345678901"))
    users = result.scalars().all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_create_admin_rejects_wrong_role_if_exists(test_db):
    """AC5: si el DNI ya existe con otro rol, levanta ValueError claro."""
    # Crear primero un paciente con ese DNI
    existing = User(
        dni="12345678901",
        hashed_password="hash-whatever",
        full_name="Paciente Existente",
        role=UserRole.PATIENT,
        is_active=True,
    )
    test_db.add(existing)
    await test_db.commit()

    with pytest.raises(ValueError, match="ya existe con rol"):
        await ensure_admin(test_db, "12345678901", "AdminPass1234", "Admin")


@pytest.mark.asyncio
async def test_create_admin_validates_min_length_8(test_db):
    """AC5: contraseña menor a 8 caracteres falla."""
    with pytest.raises(ValueError, match="al menos 8 caracteres"):
        await ensure_admin(test_db, "12345678901", "short", "Admin")


@pytest.mark.asyncio
async def test_bootstrap_admin_can_login(test_db, client: AsyncClient):
    """AC6: admin creado por bootstrap puede autenticarse en /auth/login/access-token."""
    admin = await ensure_admin(test_db, "12345678901", "AdminPass1234", "Admin Bootstrap")
    assert admin.role == UserRole.ADMIN

    response = await client.post(
        "/auth/login/access-token",
        json={"dni": "12345678901", "password": "AdminPass1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["dni"] == "12345678901"
    assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_create_staff_optional(test_db):
    """Staff puede crearse opcionalmente con STAFF_DNI/STAFF_PASSWORD."""
    staff = await ensure_staff(test_db, "11111111111", "StaffPass1234", "Staff Uno")
    assert staff.role == UserRole.STAFF
    assert staff.is_active is True
    assert verify_password("StaffPass1234", staff.hashed_password) is True

    # Idempotente para staff también
    staff2 = await ensure_staff(test_db, "11111111111", "StaffPass1234", "Staff Uno")
    assert staff2.id == staff.id


@pytest.mark.asyncio
async def test_create_admin_main_missing_admin_dni(monkeypatch, capsys):
    """main() sin ADMIN_DNI devuelve 1 e imprime error en stderr."""
    monkeypatch.delenv("ADMIN_DNI", raising=False)
    monkeypatch.setenv("ADMIN_PASSWORD", "AdminPass1234")

    ret = await main()
    assert ret == 1

    err = capsys.readouterr().err
    assert "ADMIN_DNI es obligatorio" in err


@pytest.mark.asyncio
async def test_create_admin_main_missing_admin_password(monkeypatch, capsys):
    """main() sin ADMIN_PASSWORD devuelve 1 e imprime error en stderr."""
    monkeypatch.setenv("ADMIN_DNI", "12345678901")
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    ret = await main()
    assert ret == 1

    err = capsys.readouterr().err
    assert "ADMIN_PASSWORD es obligatorio" in err


def test_create_admin_cli_no_module_not_found(tmp_path, monkeypatch):
    """CLI del script desde la raíz del repo sin PYTHONPATH no falla con ModuleNotFoundError."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    # ADMIN_DNI a propósito NO se define: el script debe salir antes de tocar la BD.
    env["ADMIN_PASSWORD"] = "AdminPass1234"
    env["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
    env["POSTGRES_USER"] = "test_user"
    env["POSTGRES_PASSWORD"] = "test_password"
    env["POSTGRES_DB"] = "test_db"
    env["POSTGRES_HOST"] = "localhost"
    env["POSTGRES_PORT"] = "5432"
    env["STAFF_PASSWORD"] = "test-staff-password-do-not-use-in-production"
    env["ALGORITHM"] = "HS256"
    env["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

    script = REPO_ROOT / "backend" / "scripts" / "create_admin.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, result.stderr
    assert "ADMIN_DNI es obligatorio" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
    assert "ModuleNotFoundError" not in result.stdout
