"""Política mínima de contraseñas (F2-08).

Centraliza la regla de longitud mínima reutilizable para todos los esquemas
de creación y cambio de contraseña (PatientCreate, UserCreate,
StaffPasswordUpdateRequest, AdminVerifyRequest), sin tocar hashes
almacenados y sin añadir reglas de composición no solicitadas.
"""

MIN_PASSWORD_LENGTH = 8
MIN_PASSWORD_MESSAGE = f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"


def validate_min_password_length(value: str) -> str:
    """Valida que la contraseña tenga al menos 8 caracteres (F2-08).

    Devuelve el valor sin cambios cuando cumple la regla y lanza
    ValueError con un mensaje claro en español en caso contrario.
    """
    if not isinstance(value, str) or len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError(MIN_PASSWORD_MESSAGE)
    return value
