from functools import lru_cache
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.allowed_person_repository import AllowedPersonRepository

# Valor usado para generar un hash bcrypt ficticio en runtime (no hardcodeado
# en el código fuente, por tanto no es un secreto escaneable). Se usa para que
# verify_password siempre ejecute el trabajo criptográfico incluso cuando no
# existe un usuario real con hash almacenado, evitando que el tiempo de
# respuesta filtre si un DNI existe o si el rol es STAFF (oráculo de cuentas/roles).
_DUMMY_STAFF_PASSWORD = "__f2_05_dummy_staff_password__"


@lru_cache(maxsize=1)
def _dummy_bcrypt_hash() -> str:
    """Genera un hash bcrypt válido en runtime, cacheado una sola vez.

    Se cachea para que los caminos sin usuario real hagan exactamente un
    verify (como el camino real), sin el coste de re-generar el hash en cada
    llamada. Esto elimina el oráculo de tiempo entre usuarios conocidos y
    desconocidos.
    """
    return get_password_hash(_DUMMY_STAFF_PASSWORD)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.allowed_person_repo = AllowedPersonRepository(session)
    
    async def authenticate_user(self, dni: str, password: str) -> Optional[User]:
        """Authenticate a user by DNI and password."""
        user = await self.user_repo.get_by_dni(dni)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    async def create_user(
        self,
        dni: str,
        password: str,
        full_name: str,
    ) -> User:
        """Create a new patient user with hashed password.

        Siempre crea un usuario con rol PATIENT: el registro público no
        permite escalar privilegios desde la capa de servicio.
        """
        # Verify DNI is in the whitelist (unconditionally for all roles)
        is_allowed = await self.allowed_person_repo.is_dni_allowed(dni)
        if not is_allowed:
            raise ValueError("DNI no autorizado para registro")
        
        hashed_password = get_password_hash(password)
        user = await self.user_repo.create(
            dni=dni,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole.PATIENT,
        )
        
        # Mark DNI as registered (patients only)
        await self.allowed_person_repo.mark_as_registered(dni)
        
        return user
    
    async def authenticate_staff(self, dni: str, password: str) -> Optional[User]:
        """Authenticate a staff user by DNI and password.

        Requires an existing, active User with role STAFF. Never creates an
        account: staff users are provisioned out-of-band via
        backend/scripts/create_admin.py.

        bcrypt se ejecuta siempre (contra el hash real del usuario o contra
        un hash dummy cuando no existe), de modo que el tiempo de respuesta
        no revela si el DNI existe ni si el rol es STAFF. Cualquier fallo
        devuelve None para que el endpoint responda con un único error
        genérico, sin oráculo de cuentas ni de roles.
        """
        user = await self.user_repo.get_by_dni(dni)

        # Verificación de contraseña en todos los caminos: hash real si el
        # usuario existe, hash dummy generado en runtime cuando no, para
        # evitar oráculo de tiempo.
        stored_hash = user.hashed_password if user is not None else _dummy_bcrypt_hash()
        password_ok = verify_password(password, stored_hash)

        # Elegibilidad evaluada de forma uniforme, sin retornos tempranos
        # antes de la verificación bcrypt.
        if (
            user is not None
            and user.role == UserRole.STAFF
            and user.is_active
            and password_ok
        ):
            return user
        return None

    async def get_user_by_dni(self, dni: str) -> Optional[User]:
        """Get user by DNI."""
        return await self.user_repo.get_by_dni(dni)
    
    def create_token(self, user: User) -> str:
        """Create access token for user."""
        data = {"sub": user.dni, "role": user.role.value}
        return create_access_token(data)
