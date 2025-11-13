# Kestrel Management Plane

A management service for policies, rules, endpoint assignments, and detector configurations. Exposes a REST API to CRUD and export configurations to the analytics service.

## Features

- Manage endpoints, policies, rules, assignments, detector configurations
- Audit log of actions
- Export APIs for analytics-service to consume active configs
- SQLite by default, Postgres via `DATABASE_DSN` (supports Neon). Tables are created in the `management` schema when using Postgres.
- Optional JWT bearer auth for write operations

## Run locally (Python)

1. Create and activate a Python 3.11+ environment
2. Install dependencies
3. Run the app

```
pip install -r requirements.txt
uvicorn app:app --reload --port 8002
```

Visit http://localhost:8002/docs for interactive API docs.

### Auth

- Issue token: `POST /api/auth/login` with JSON `{ "username": "admin", "password": "your-password" }`.
- Send token in `Authorization: Bearer <token>` header for write operations (POST/PATCH/DELETE).
  - Configure credentials via env: `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` (bcrypt).
  - Generate hash: `python -m scripts.make_admin_hash <password>` and set `ADMIN_PASSWORD_HASH` to the printed value.

## Environment

- `DATABASE_DSN` (optional): e.g. `postgresql+psycopg2://user:pass@localhost:5432/kestrel`
  - If not set, a local SQLite file `management.db` is used.
  - Neon example (requires SSL):
    - `postgresql+psycopg2://<user>:<password>@<neon_host>/<database>?sslmode=require`
  - `MANAGEMENT_SCHEMA` (optional): target schema name on Postgres (default: `management`).
  - `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` for auth.
  - `DECISION_ENGINE_INTERVAL` (optional): seconds between automatic decision engine runs (e.g. `30`). If unset or `0`, runs only once at startup.

## Docker

```
docker build -t kestrel-management .
docker run -p 8002:8002 --env DATABASE_DSN="postgresql+psycopg2://<user>:<password>@<neon_host>/<db>?sslmode=require" kestrel-management
```

## Endpoints (selected)

- `GET /health` – service health
- `GET/POST /api/endpoints` – manage endpoints
- `GET/POST /api/policies` – manage policies
- `GET/POST /api/rules` – manage rules
- `GET/POST /api/assignments` – manage assignments
- `GET/POST /api/detectors` – manage detector configs
- `GET /api/export/rules` – export enabled rules for analytics-service
- `GET /api/export/detectors` – export detector configurations
- `POST /api/auth/login` – issue JWT
- `GET/POST/PATCH/DELETE /api/users` – admin-only user management
- `GET /api/alerts` – list alerts from analytics-service (backed by Postgres `public.alerts`)
  - Query params: `limit` (default 50), `offset`, `severity`, `event_type`, `agent_id`, `min_score`, `since`, `until`
- `GET /api/alerts/{id}` – fetch a single alert by ID
- `POST /api/decisions/run` – trigger decision generation pass (returns count created)
- `GET /api/decisions?status=pending` – list decisions
- `POST /api/decisions/{id}/execute` / `dismiss` – update decision status
- `GET /api/metrics/security-events-24h` – total simulated security events (24h)
- `GET /api/metrics/current-threat-level` – current 1–5 threat level
- `GET /api/metrics/security-posture-score` – 0–100 posture score
- `GET /api/metrics/active-agents` – active agents in last 5m
- `GET /api/metrics/threat-timeline` – time series for threat/security/anomaly
- `GET /api/metrics/event-classification` – pie data for event classes
- `GET /api/metrics/security-assessment` – table of recent endpoints and risk

## Seeding sample data

```
python -m scripts.init_db
python -m scripts.sample_data
python -m scripts.check_db  # verify tables in the 'management' schema (Postgres)

### Synthetic system metrics for frontend charts

If the real `system_info` table is empty, seed synthetic rows so metrics & charts render:

```

python -m scripts.generate_system_info_sample 50

```

### Manual decision generation

Trigger a pass after new alerts arrive:

```

curl -X POST http://localhost:8002/api/decisions/run

```

### Users

```

# create an admin user

python -m scripts.create_user admin "<password>" admin

# or generate a bcrypt hash to use via env

python -m scripts.make_admin_hash "<password>"

```

```

## Notes

- For production, add authentication/authorization and switch to Postgres.
- Consider Alembic migrations if schemas evolve.
