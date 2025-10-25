#!/usr/bin/env bash
set -euo pipefail
# Backend dev server and InfluxDB using compose
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."

if ! command -v docker &>/dev/null; then
  echo "Docker not found, skipping InfluxDB compose"
else
  docker compose -f "${ROOT_DIR}/docker/docker-compose.yml" up -d
fi

cd "${ROOT_DIR}/backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir .
