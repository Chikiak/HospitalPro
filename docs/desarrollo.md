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

## Scripts de seguridad (F1-06)

### `backend/scripts/hash_config_passwords.py`

Convierte valores en texto plano de `system_config` (claves `staff_password` y `admin_password`) a hash bcrypt. Es idempotente: ejecutarlo varias veces no re-hashea valores ya convertidos.

```powershell
# Ejecutar con credenciales de entorno
$env:STAFF_PASSWORD="mi-password-staff"
$env:ADMIN_PASSWORD="mi-password-admin"
python backend/scripts/hash_config_passwords.py
```

Salida esperada:
- `Convertido: staff_password` — se guardó el hash
- `Ya hasheado: admin_password` — ya tenía hash, no se tocó
- `Nada que convertir` — si no se definieron variables de entorno

No se importa en `main.py` ni se ejecuta en el arranque: la conversión es siempre un paso explícito de despliegue.

### `backend/scripts/create_admin.py`

Crea el usuario administrador inicial desde variables de entorno `ADMIN_DNI` y `ADMIN_PASSWORD` (mínimo 8 caracteres). Es idempotente: ejecutarlo dos veces no crea duplicados. Si el DNI ya existe con otro rol, falla con mensaje claro.

Opcionalmente crea un usuario staff con `STAFF_DNI` y `STAFF_PASSWORD`.

```powershell
$env:ADMIN_DNI="12345678901"
$env:ADMIN_PASSWORD="AdminPass1234"
$env:STAFF_DNI="11111111111"
$env:STAFF_PASSWORD="StaffPass1234"
python backend/scripts/create_admin.py
```

Salida esperada:
- `Creado administrador: dni=12345678901`
- `Creado staff: dni=11111111111`
- En segunda ejecución: no imprime nada de creación (idempotente)

No se importa en `main.py` ni se ejecuta en el arranque: el bootstrap es siempre un paso explícito de despliegue.

## Entorno de desarrollo · Frontend

Desde la raíz del repositorio:

```powershell
# 1. Instalar dependencias del frontend
cd frontend
npm ci

# 2. Ejecutar los tests (Vitest sobre jsdom)
npm run test:run

# 3. Lint (ESLint)
npm run lint

# 4. Build (TypeScript + Vite)
npm run build
```

La suite de frontend usa una única configuración de Vitest en
`vite.config.ts` (`globals`, `jsdom`, `setupFiles: ./src/test/setup.ts`).
Los tests se ejecutan contra la UI actual con Testing Library y mockean solo
la capa HTTP con `axios-mock-adapter`; no se mockean componentes y no se
modifica el código de la aplicación para pasar los tests.

## Ejecutar el CI en local

El pipeline de `.github/workflows/ci.yml` se dispara en `push` y
`pull_request` con jobs separados de backend y frontend; el fallo de cualquier
job rompe el pipeline. Reproducir localmente:

Backend:

```powershell
cd backend
pip install -r requirements.txt
pip install ruff pip-audit
python -m pytest -q
pip-audit -r requirements.txt
```

Frontend:

```powershell
cd frontend
npm ci
npm run lint
npm run test:run
npm run build
npm audit
```

La detección de secretos con `gitleaks` se instala en el job de CI (no se
agrega a `requirements.txt` ni a `package.json`).

