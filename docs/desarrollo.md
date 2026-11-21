# Entorno de desarrollo · Backend

## Aprovisionamiento (entorno virtual recién creado)

Desde la raíz del repositorio:

```powershell
# 1. Crear el entorno virtual
python -m venv .venv

# 2. Activarlo
# PowerShell:
.venv\Scripts\Activate.ps1
# CMD:
# .venv\Scripts\activate.bat
# bash:
# source .venv/bin/activate

# 3. Instalar dependencias del backend
pip install -r backend/requirements.txt
```

## Ejecutar los tests del backend

```powershell
cd backend
python -m pytest -q
```

El suite debe terminar en verde (`exit 0`, 0 fallos, 0 errores de colección) sin necesidad de un archivo `.env` ni variables de entorno definidas:

- `tests/conftest.py` define valores de prueba para `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, `SECRET_KEY`, `ALGORITHM` y `ACCESS_TOKEN_EXPIRE_MINUTES` **solo cuando no están ya definidos** en el entorno (`os.environ.setdefault`).
- Los tests usan una base de datos SQLite en memoria, así que no se necesita PostgreSQL real.

## Notas

- No se requieren credenciales reales ni una base de datos PostgreSQL para correr los tests.
- La sección de frontend y CI de este documento la completa F1-02.
