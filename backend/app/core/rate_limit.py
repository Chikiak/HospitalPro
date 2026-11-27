"""Rate limiting configuration using slowapi.

Combina dos ejes de protección sin entremezclarlos:

1. **Límite por IP** (mantenido): ``get_client_ip`` lee la IP de la conexión
   directa (``request.client.host``). Nunca se confía ciegamente en
   ``X-Forwarded-For``: solo se usa si la conexión directa proviene de un proxy
   configurado explícitamente como confiable (ver :data:`TRUSTED_PROXIES`).
   Los headers ``X-Forwarded-For`` spoofed no cambian la clave de IP por
   defecto.

2. **Límite por identidad normalizada**: DNI para login paciente/staff y
   registro, y ``sub`` (DNI) del JWT para ``/appointments/book``. Como el
   ``key_func`` del decorador de slowapi se ejecuta *antes* de que FastAPI
   parsee el cuerpo, no puede leer el DNI del body sin doble consumo. Por eso
   los endpoints de identidad no usan el decorador para el límite por
   identidad: realizan un *check manual en frontera* después de validar el
   cuerpo (y, en book, autenticar al usuario), llamando a la API pública de la
   librería ``limits`` a través de ``limiter.limiter.hit``.

El almacenamiento es **in-memory (MemoryStorage) por proceso**: no coordina
entre workers ni nodos. En despliegues multiworker cada proceso mantiene su
propio contador, por lo que el límite efectivo se multiplica por el número de
workers. Para coordinación distribuida se requiere un backend compartido
(Redis, etc.) mediante ``storage_uri``. Esto se documenta y no se afirma
coordinación distribuida sin ese backend.
"""

from __future__ import annotations

import logging

from fastapi import Request
from limits import RateLimitItem, parse_many
from limits.storage import MemoryStorage
from limits.strategies import STRATEGIES
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.wrappers import Limit

logger = logging.getLogger(__name__)

# Limiter por IP (protección existente). key_func ignora X-Forwarded-For salvo
# configuración explícita de proxies confiables (ver TRUSTED_PROXIES).
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# Storage compartido (in-memory, por proceso) usado tanto por el limiter de IP
# como por los checks manuales de identidad. Misma instancia: las claves son
# distintas ("ip:..." vs "login:..." / "register:..." / "book:...") por lo que
# no interfieren.
_identity_storage: MemoryStorage = limiter._storage  # type: ignore[assignment]
_identity_strategy = STRATEGIES["fixed-window"](_identity_storage)

# Límites por identidad (criterios F2-10). Ajustables por variable de entorno.
LOGIN_IDENTITY_LIMIT = "5/minute"
REGISTER_IDENTITY_LIMIT = "5/minute"
BOOK_IDENTITY_LIMIT = "10/minute"
IP_LIMIT = "200/minute"  # coincide con default_limits del limiter de IP

# Prefijos de clave por tipo de identidad, para evitar colisiones entre
# DNI de login y sub de book aunque coincidan en valor.
KEY_PREFIX_LOGIN = "login"
KEY_PREFIX_REGISTER = "register"
KEY_PREFIX_BOOK = "book"
KEY_PREFIX_IP = "ip"

# Proxies confiables (vacío por defecto: nunca se usa X-Forwarded-For).
TRUSTED_PROXIES: set[str] = set()


def configure_trusted_proxies(proxies: list[str] | None) -> None:
    """Configura proxies cuya IP directa autoriza leer X-Forwarded-For.

    Solo se llama en arranque si el operador define explícitamente proxies
    confiables. Sin llamada, X-Forwarded-For se ignora por completo (protege
    contra spoofing).
    """
    global TRUSTED_PROXIES
    TRUSTED_PROXIES = set(proxies or [])


def get_client_ip(request: Request) -> str:
    """Devuelve la IP del cliente para rate limiting por IP.

    Por defecto usa la conexión directa (``request.client.host``). Solo consulta
    ``X-Forwarded-For`` si la conexión directa proviene de un proxy configurado
    como confiable, tomando el primer valor de la cabecera (el cliente más
    cercano al proxy de confianza). Headers spoofed desde una conexión directa
    no confiable no cambian la clave.
    """
    direct = request.client.host if request.client else "127.0.0.1"
    if not TRUSTED_PROXIES or direct not in TRUSTED_PROXIES:
        return direct or "127.0.0.1"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # El primer valor es el origen original más cercano al proxy confiable.
        return forwarded.split(",")[0].strip() or direct
    return direct


def normalize_identity(value: str | None) -> str | None:
    """Normaliza un identificador de identidad (DNI / sub) para usarlo como clave.

    Quita espacios. No loguea ni expone el valor crudo.
    """
    if value is None:
        return None
    normalized = "".join(str(value).split()).strip()
    return normalized or None


def identity_key(kind: str, value: str | None) -> str | None:
    """Construye la clave de rate limit por identidad: ``kind:normalized``."""
    norm = normalize_identity(value)
    if not norm:
        return None
    return f"{kind}:{norm}"


def _parse_limit(limit_string: str) -> RateLimitItem:
    items = list(parse_many(limit_string))
    if not items:
        raise ValueError(f"Invalid rate limit string: {limit_string!r}")
    return items[0]


def _build_limit_object(limit_item: RateLimitItem, key: str, scope: str) -> Limit:
    return Limit(
        limit=limit_item,
        key_func=lambda _req: key,
        scope=scope,
        per_method=False,
        methods=None,
        error_message=None,
        exempt_when=None,
        cost=1,
        override_defaults=True,
    )


def check_limit(
    request: Request,
    limit_string: str,
    key: str,
    scope: str,
) -> None:
    """Aplica un límite en frontera (IP o identidad), tras validar cuerpo/auth.

    Consume un hit en el storage compartido. Si se agota el límite, lanza
    :class:`RateLimitExceeded` (429) seteando ``request.state.view_rate_limit``
    para que el handler registrado inyecte los headers ``X-RateLimit-*`` y
    ``Retry-After``, manteniendo el contrato de respuestas 429 existente.

    Nunca registra ni devuelve el valor crudo de identidad (DNI/token) en logs
    ni en la respuesta 429; el log solo usa el prefijo de la clave.
    """
    if not key:
        return
    limit_item = _parse_limit(limit_string)
    allowed = _identity_strategy.hit(limit_item, key, scope)
    if not allowed:
        limit_obj = _build_limit_object(limit_item, key, scope)
        request.state.view_rate_limit = (limit_obj, [key, scope])
        logger.warning(
            "Rate limit exceeded for scope=%s key_prefix=%s",
            scope,
            key.split(":")[0] if ":" in key else "?",
        )
        raise RateLimitExceeded(limit_obj)
