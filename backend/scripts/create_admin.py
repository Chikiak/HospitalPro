"""Bootstrap del primer usuario admin (y opcionalmente staff) desde variables de entorno.

Lee ADMIN_DNI (obligatorio) y ADMIN_PASSWORD (obligatorio, mínimo 8).
Crea el usuario si no existe (por DNI) o falla con mensaje claro si ya existe
con otro rol. Idempotente: ejecutado dos veces no crea duplicados.

Opcionalmente lee STAFF_DNI / STAFF_PASSWORD para crear un usuario staff.

No se importa en main.py ni se ejecuta en el arranque: el bootstrap es siempre
un paso explícito de despliegue (script CLI).
"""

import os
import sys

from app.core.security import get_password_hash
from app.models.user import User, UserRole


async def ensure_admin(session, dni: str, password: str, full_name: str = "Administrador") -> User:
    """Crea o devuelve el usuario admin con el DNI dado.

    - Si no existe: crea con rol ADMIN, is_active=True, contraseña hasheada.
    - Si existe con rol ADMIN: devuelve el existente (idempotente).
    - Si existe con otro rol: levanta ValueError con mensaje claro.
    """
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.dni == dni))
    existing = result.scalar_one_or_none()

    if existing is not None:
        if existing.role == UserRole.ADMIN:
            return existing
        raise ValueError(
            f"El DNI {dni} ya existe con rol '{existing.role.value}'. "
            f"No se puede sobrescribir como administrador."
        )

    if len(password) < 8:
        raise ValueError("La contraseña de administrador debe tener al menos 8 caracteres")

    user = User(
        dni=dni,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    print(f"Creado administrador: dni={dni}")
    return user


async def ensure_staff(
    session, dni: str, password: str, full_name: str = "Personal Administrativo"
) -> User:
    """Crea o devuelve el usuario staff con el DNI dado (opcional)."""
    from sqlalchemy import select

    result = await session.execute(select(User).where(User.dni == dni))
    existing = result.scalar_one_or_none()

    if existing is not None:
        if existing.role == UserRole.STAFF:
            return existing
        raise ValueError(
            f"El DNI {dni} ya existe con rol '{existing.role.value}'. "
            f"No se puede sobrescribir como staff."
        )

    if len(password) < 8:
        raise ValueError("La contraseña de staff debe tener al menos 8 caracteres")

    user = User(
        dni=dni,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        role=UserRole.STAFF,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    print(f"Creado staff: dni={dni}")
    return user


async def main() -> int:
    """Punto de entrada CLI. Lee variables de entorno y ejecuta el bootstrap."""
    admin_dni = os.getenv("ADMIN_DNI")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_dni:
        print("ERROR: ADMIN_DNI es obligatorio", file=sys.stderr)
        return 1
    if not admin_password:
        print("ERROR: ADMIN_PASSWORD es obligatorio", file=sys.stderr)
        return 1

    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            await ensure_admin(session, admin_dni, admin_password)

            staff_dni = os.getenv("STAFF_DNI")
            staff_password = os.getenv("STAFF_PASSWORD")
            if staff_dni and staff_password:
                await ensure_staff(session, staff_dni, staff_password)

        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            await session.rollback()
            return 1

    return 0


if __name__ == "__main__":
    import asyncio

    sys.exit(asyncio.run(main()))
