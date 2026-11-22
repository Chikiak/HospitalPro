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

La suite corre sin necesidad de un archivo `.env` ni variables de entorno definidas (`POSTGRES_*`, `SECRET_KEY`...):

- `tests/conftest.py` define valores de prueba para `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, `SECRET_KEY`, `ALGORITHM` y `ACCESS_TOKEN_EXPIRE_MINUTES` **solo cuando no están ya definidos** en el entorno (`os.environ.setdefault`).
- Los tests usan una base de datos SQLite en memoria, así que no se necesita PostgreSQL real.

### Resultados esperados por fichero (F1-01)

Cada fichero de test reparado en `F1-01` termina en verde (`exit 0`) de forma aislada:

```powershell
python -m pytest tests/api/test_appointments.py -q      # 3 passed
python -m pytest tests/api/test_admin.py -q             # 10 passed
python -m pytest tests/api/test_allowed_persons.py -q   # 8 passed (admin + staff parametrizado)
python -m pytest tests/api/test_category_slots.py -q    # 1 passed
python -m pytest tests/api/test_patients.py -q          # 3 passed, 1 fallo pre-existente (ver nota abajo)
```

### Nota real sobre el suite completo (`python -m pytest -q`)

El suite completo se ejecuta sin `.env` gracias a `tests/conftest.py`, pero **hoy no termina al 100% en verde**: presenta **5 fallos pre-existentes heredados de `main`** (98 passed, 2 skipped, 5 failed), debidos a `server_default=func.timezone('UTC', func.now())` y `onupdate=func.timezone(...)` en el modelo `TriageData` de `backend/app/models/patient.py:26-27`, que PostgreSQL entiende pero SQLite no (`unknown function: timezone()`):

- `tests/api/test_auth_middleware.py` × 3
- `tests/api/test_medical_records.py` × 1
- `tests/api/test_patients.py::test_list_all_patients_with_data` × 1

Estos 5 fallos están fuera del alcance de `F1-01` (no se modifica nada en `backend/app/` ni en `backend/requirements.txt`) y se resuelven en fases posteriores (requieren cambio en `app/` o PostgreSQL real). Quedan anotados y no se ocultan: `test_register_non_patient_without_whitelist` y los tests de `test_patients.py` que afirman el bug E-01 se mantienen sin tocar y se reescriben en `F1-03`.

## Notas

- No se requieren credenciales reales ni una base de datos PostgreSQL para correr los tests.
- La sección de frontend y CI de este documento la completa F1-02.
