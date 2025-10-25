# Development Guide

## Prerequisites

- Python 3.11+
- Docker + Docker Compose (for InfluxDB)
- libpcap development headers: `sudo apt-get install libpcap-dev python3-dev`
- Git

## Initial Setup

```bash
# Clone repository
git clone <your-repo> Network-Device-Monitor
cd Network-Device-Monitor

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements/dev.txt

# Copy environment template
cp backend/.env.example backend/.env

# Grant raw socket capability to Python (for scapy)
sudo setcap cap_net_raw,cap_net_admin=eip "$(readlink -f .venv/bin/python)"

# Start InfluxDB
docker compose -f docker/docker-compose.yml up -d

# Verify InfluxDB is running
curl http://localhost:8086/health
```

## Running Services

### Backend API (Development Mode)

```bash
# Option 1: Using Makefile (from project root)
make dev

# Option 2: Direct uvicorn
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir .

# Option 3: Using helper script
./scripts/run_backend.sh
```

Access API docs: <http://127.0.0.1:8000/docs>

### PyQt Frontend

```bash
# Install PyQt dependencies
pip install -r frontend/pyqt/requirements.txt

# Run application
python frontend/pyqt/src/app.py

# Or use script
./scripts/run_frontend_pyqt.sh
```

### Combined Dev Environment

```bash
# Starts InfluxDB + backend in one command
./scripts/dev.sh
```

## Testing

```bash
# Run all tests (from project root)
make test

# Or from backend directory
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api_smoke.py -v

# Run tests matching pattern
pytest -k "test_health"
```

## Code Quality

### Linting & Formatting

This project uses `ruff` for both linting and formatting.

```bash
# Lint code (from project root)
make lint

# Type checking
make typecheck

# Run all quality checks
make lint && make typecheck && make test

# View all available commands
make help

# Clean build artifacts
make clean
```

**Note:** The backend-specific Makefile commands still work:

```bash
make -C backend lint
make -C backend typecheck
```

## Database Management

### SQLite (Inventory)

```bash
# Database will be created at backend/data/devices.db (auto-created)
# View schema
sqlite3 backend/data/devices.db ".schema"

# Query devices
sqlite3 backend/data/devices.db "SELECT * FROM devices;"
```

### InfluxDB (Metrics)

```bash
# Access InfluxDB UI
open http://localhost:8086

# Login credentials (from docker-compose.yml)
Username: admin
Password: admin12345
Organization: local
Bucket: network_metrics

# Query via CLI (install influx CLI first)
influx query 'from(bucket:"network_metrics") |> range(start: -1h)'
```

## Troubleshooting

### Scapy Permission Errors

```bash
# Error: Operation not permitted
# Solution: Grant capabilities
sudo setcap cap_net_raw,cap_net_admin=eip "$(readlink -f .venv/bin/python)"

# Verify
getcap "$(readlink -f .venv/bin/python)"
# Should show: cap_net_admin,cap_net_raw=eip
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Docker Issues

```bash
# Reset InfluxDB
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f
```

## Project Structure

```text
Network-Device-Monitor/
├── backend/
│   ├── app/
│   │   ├── api/routers/      # FastAPI endpoints
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # Business logic (discovery, monitoring, etc.)
│   │   ├── storage/          # Database repositories
│   │   ├── scheduler/        # APScheduler jobs
│   │   └── utils/            # Helpers (network, OUI)
│   ├── requirements/         # Dependencies
│   ├── tests/               # Pytest tests
│   └── .env                 # Configuration (gitignored)
├── frontend/
│   └── pyqt/                # PyQt6 desktop app
├── docs/                    # Documentation
├── docker/                  # Docker Compose + Dockerfiles
├── scripts/                 # Helper scripts
└── .github/workflows/       # CI/CD
```

## Environment Variables

Key settings in `backend/.env`:

```bash
# Network scanning (leave empty for auto-detect)
NETWORK_CIDR=
INTERFACE=

# SNMP credentials
SNMP_COMMUNITY=public

# InfluxDB connection
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=dev-token
INFLUX_ORG=local
INFLUX_BUCKET=network_metrics

# Alert thresholds
ALERT_LATENCY_MS=200
ALERT_PACKET_LOSS=0.5
```

## Adding New Features

1. Update `docs/roadmap.md` with task
2. Create feature branch: `git checkout -b feature/name`
3. Implement in appropriate service/router
4. Add tests in `backend/tests/`
5. Update API docs in `docs/api.md` if adding endpoints
6. Run quality checks: `make lint && make typecheck && make test`
7. Commit and push: `git push origin feature/name`
8. CI will run automatically on push

## Debugging

### Enable Debug Logging

```python
# In backend/app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect WebSocket Messages

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/stream
```

### Profile Performance

```bash
# Install profiling tools
pip install py-spy

# Profile running backend
py-spy top --pid <backend-pid>
```
