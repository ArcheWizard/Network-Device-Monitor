# Ops

## Running

- Dev (backend): `make dev` or `./scripts/run_backend.sh`
- Dev (frontend): `./scripts/run_frontend_pyqt.sh`
- Direct (backend): `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend`
- Health: `GET http://localhost:8000/api/health` → `{ "status": "ok" }`

## Permissions

- scapy needs CAP_NET_RAW; use `setcap` on venv python.
- Example: `sudo setcap cap_net_raw,cap_net_admin=eip "$(readlink -f .venv/bin/python)"`

## Docker

- `docker compose -f docker/docker-compose.yml up -d`
  - starts InfluxDB 2.x and (later) a backend container

## Logs/Env

- backend/.env controls network ranges, SNMP, and InfluxDB endpoints.
- copy template: `cp backend/.env.example backend/.env`
- do not commit real tokens; use `.env` locally and secrets in CI/CD
