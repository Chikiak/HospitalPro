"""Convierte valores en texto plano de system_config a hash bcrypt.

Recorre las claves staff_password y admin_password. Para las que no
estén hasheadas, guarda el hash y anuncia por stdout qué claves convirtió.
Es seguro ejecutarlo varias veces (idempotente).

Uso:
    STAFF_PASSWORD=... ADMIN_PASSWORD=... python backend/scripts/hash_config_passwords.py

No se importa en main.py ni se ejecuta en el arranque: la conversión es
siempre un paso explícito de despliegue (script CLI).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import get_password_hash
from app.models.system_config import SystemConfig

HASH_PREFIX = "$2b$"

KEYS = ("staff_password", "admin_password")


def is_bcrypt_hash(value: str | None) -> bool:
    """Devuelve True si el valor tiene forma de hash bcrypt ($2b$)."""
    return bool(value) and value.startswith(HASH_PREFIX)


async def convert_key(session, key: str, plain_value: str) -> bool:
    """Guarda el hash de plain_value bajo la clave dada si no está ya hasheado.

    Returns True si se convirtió (valor previo en texto plano o ausencia),
    False si ya tenía hash bcrypt (no se re-hashea).
    """
    result = await session.execute(select(SystemConfig).where(SystemConfig.key == key))
    config = result.scalar_one_or_none()

    if config is None:
        config = SystemConfig(key=key, value=get_password_hash(plain_value))
        session.add(config)
        await session.commit()
        print(f"Convertido: {key}")
        return True

    if is_bcrypt_hash(config.value):
        print(f"Ya hasheado: {key}")
        return False

    config.value = get_password_hash(plain_value)
    await session.commit()
    print(f"Convertido: {key}")
    return True


async def main() -> int:
    """Punto de entrada CLI. Lee STAFF_PASSWORD y ADMIN_PASSWORD del entorno."""
    staff_password = os.getenv("STAFF_PASSWORD")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not staff_password and not admin_password:
        print("Nada que convertir: no se definieron STAFF_PASSWORD ni ADMIN_PASSWORD")
        return 0

    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        if staff_password:
            await convert_key(session, "staff_password", staff_password)
        if admin_password:
            await convert_key(session, "admin_password", admin_password)

    return 0


if __name__ == "__main__":
    import asyncio

    sys.exit(asyncio.run(main()))
