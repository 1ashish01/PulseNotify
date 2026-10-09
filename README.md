# PulseNotify

PulseNotify is a Django REST Framework backend for monitoring mock flight prices and recording notifications when prices reach a user's configured threshold.

## Features

- User registration and login with JWT access tokens
- User profiles with `admin` and `user` roles
- User-specific flight price alerts
- Soft deletion of alerts by changing their status to `inactive`
- Mock flight price API
- Admin summary with alert, notification, and route metrics
- Celery background tasks and Celery Beat scheduling
- PostgreSQL database and Redis broker

## Prerequisites

- Python version compatible with the pinned requirements
- Docker Desktop with Docker Compose
- Git
- Postman for API testing

## Setup

### 1. Create and activate the virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set your own Django secret key and PostgreSQL credentials. Keep `.env` private and never commit it.

Ensure the settings module is configured as:

```text
DJANGO_SETTINGS_MODULE=config.settings.local
```

The local PostgreSQL configuration uses port `5434`, and Redis uses port `6380`, as configured by the supplied environment settings.

### 4. Start PostgreSQL and Redis

From the project root:

```powershell
docker compose -f docker-compose.pulsenotify.yml up -d
docker compose -f docker-compose.pulsenotify.yml ps
```

Wait until both services are healthy before continuing.

### 5. Apply database migrations

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py check
```

### 6. Run the automated tests

```powershell
python manage.py test
```

## Running the application

Keep three PowerShell terminals open in the project directory, with the virtual environment activated in each terminal.

### Terminal 1: Django API

```powershell
python manage.py runserver 8000
```

### Terminal 2: Celery worker

```powershell
celery -A config worker --loglevel=info --pool=solo
```

### Terminal 3: Celery Beat

```powershell
celery -A config beat --loglevel=info
```

Celery Beat schedules `alerts.tasks.check_prices` every 60 seconds. The worker processes price checks and notification tasks.

The mock price task calls the local API at `http://localhost:8000/api/flights/price/`.

## API endpoints

Base URL: `http://localhost:8000`

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Register a user and return an access token |
| POST | `/api/auth/login/` | Public | Authenticate and return an access token |
| POST | `/api/alerts/` | Authenticated | Create a price alert |
| GET | `/api/alerts/` | Authenticated | List the current user's alerts |
| DELETE | `/api/alerts/<id>/` | Alert owner | Mark an alert inactive |
| GET | `/api/flights/price/?route=DEL-BOM` | Public | Retrieve a mock route price |
| GET | `/api/admin/summary/` | Admin role | Retrieve aggregate platform metrics |

### Registration request

```json
{
  "username": "example_user",
  "password": "ChooseA_Strong_Password"
}
```

Successful registration returns `201 Created` with `username`, `access`, and `role`. New registrations receive the `user` role; clients cannot grant themselves admin privileges.

### Login request

```json
{
  "username": "example_user",
  "password": "ChooseA_Strong_Password"
}
```

Successful login returns `200 OK` with an access token.

### Create alert request

Send a valid JWT using the `Authorization: Bearer <access_token>` header.

```json
{
  "origin": "DEL",
  "destination": "BOM",
  "threshold_price": "4500.00"
}
```

The authenticated user is assigned by the backend.

### Mock flight routes

| Route | Mock price range |
|---|---:|
| DEL-BOM | 3000–7000 |
| BLR-HYD | 1500–4000 |
| DEL-BLR | 4000–9000 |
| BOM-GOA | 2000–5000 |

Prices are randomized within the configured range. Unknown routes return `404 Not Found`.

## Database and notification behavior

- `UserProfile` is created automatically when a user is created.
- `PriceAlert` stores the route, threshold, owner, and status.
- `NotificationLog` records the triggered price and notification message.
- Alerts are deactivated rather than physically deleted.
- A triggered alert is marked `triggered` to prevent repeated notification processing.

## Git safety

The `.gitignore` file excludes `.env`, the virtual environment, Python cache files, and generated Celery Beat schedule files.

Commit `.env.example`, not `.env`. Before pushing, inspect the staged files to ensure that credentials and generated files are excluded.

## Project status

This README documents the intended setup and API behavior. Verify the complete test suite, Postman scenarios, migrations, and deployment configuration before treating the project as submission-ready.
