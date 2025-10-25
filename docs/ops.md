# Ops

## Running

- dev: `uvicorn app.main:app --reload --port 8000 --app-dir backend`
- prod: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2 --app-dir backend`

## Permissions

- scapy needs CAP_NET_RAW; use `setcap` on venv python.

## Docker

- `docker compose -f docker/docker-compose.yml up -d`
  - starts InfluxDB 2.x and (later) a backend container

## Logs/Env

- backend/.env controls network ranges, SNMP, and InfluxDB endpoints.
