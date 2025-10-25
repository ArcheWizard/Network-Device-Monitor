# Network Device Mapper & Monitor

**Status:** 🚧 In Development - MVP Discovery, Storage, Identification, Monitoring & WebSocket Streaming Complete

Async Python backend + PyQt frontend to discover devices on local networks, identify type/manufacturer, and monitor health (latency, uptime, bandwidth, connectivity) with alerts and history.

**Current Phase:** Milestone 1F - PyQt UI Development

## Features (Planned)

- ✅ Network discovery: ARP (scapy), ICMP ping sweep, mDNS/Bonjour (zeroconf)
- ✅ Device identification: OUI lookup (IEEE database), SNMP v2c (sysName, sysDescr, etc.)
- ✅ Health monitoring: periodic ping latency + packet loss stored in InfluxDB
- ✅ Real-time WebSocket streaming: device discovery, status changes, latency metrics
- 🚧 Notifications: device offline/online, high latency thresholds
- ✅ Data persistence: SQLite for inventory + InfluxDB for time-series metrics
- ⏳ PyQt6 desktop GUI with real-time updates

**Legend:** ✅ Complete | 🚧 In Progress | ⏳ Planned

## High-level Architecture

- **Backend** (FastAPI + asyncio)
  - Services: discovery, identification, monitoring, notifications
  - Scheduler: APScheduler for periodic scans and checks
  - API: REST + WebSocket streaming updates
  - Storage: SQLite (inventory) + InfluxDB (metrics)
- **Frontend** (PyQt6)
  - Real-time device list, status, metrics
  - Network topology visualization (future)

See detailed docs:

- 📋 [Current Status](docs/CURRENT_STATUS.md) - What's done and what's next
- 🎯 [Next Steps](docs/NEXT_STEPS.md) - Detailed implementation plan for current phase
- 🏗️ [Architecture](docs/architecture.md) - System design and data flow
- 📡 [API Reference](docs/api.md) - REST and WebSocket endpoints
- 💾 [Database Schema](docs/database.md) - SQLite and InfluxDB structure
- 🛣️ [Roadmap](docs/roadmap.md) - Complete feature timeline
- 🔧 [Development Guide](docs/DEVELOPMENT.md) - Setup, testing, debugging
- 🚀 [Operations](docs/ops.md) - Running and deploying
- 🔒 [Security](docs/security.md) - Security considerations

## Quick Start

### Prerequisites

- Python 3.11+
- Docker + Docker Compose (for InfluxDB)
- libpcap: `sudo apt-get install -y libpcap-dev python3-dev`

### Setup

```bash
# Clone and create virtual environment
git clone <your-repo-url> Network-Device-Monitor
cd Network-Device-Monitor
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements/dev.txt

# Configure environment
cp backend/.env.example backend/.env

# Grant raw socket capability (for scapy without sudo)
sudo setcap cap_net_raw,cap_net_admin=eip "$(readlink -f .venv/bin/python)"

# Start InfluxDB
docker compose -f docker/docker-compose.yml up -d
```

### Run Backend

```bash
# Option 1: Makefile
make -C backend dev

# Option 2: Helper script
./scripts/dev.sh

# Access API docs at http://127.0.0.1:8000/docs
```

### Run PyQt Frontend

```bash
pip install -r frontend/pyqt/requirements.txt
python frontend/pyqt/src/app.py
```

## Current Status

**✅ Completed (Milestone 0 + Phases 1A-1E):**

- Project structure and scaffolding
- FastAPI backend with health endpoint
- **Network discovery service (ARP/ICMP/mDNS)** ✨
- **SQLite storage for device inventory** ✨
- **Discovery persistence and scheduling** ✨
- **OUI lookup for vendor identification** ✨
- **SNMP device queries (sysName, sysDescr, etc.)** ✨
- **Ping monitoring and latency metrics** ✨
- **InfluxDB metrics writer for time-series data** ✨
- **WebSocket streaming for real-time updates** ✨
  - Device discovery events
  - Status change notifications (up/down)
  - Live latency metrics streaming
- PyQt6 frontend window shell
- Auto-detect network interfaces utility
- InfluxDB Docker setup
- CI/CD workflows
- Comprehensive documentation

**⏳ Next Up (Phase 1F):**

- PyQt device table UI with real-time WebSocket updates
- API client implementation
- Status indicators and metrics display

See full [Roadmap](docs/roadmap.md) for future milestones.

## Configuration

Edit `backend/.env`:

```bash
# Network scanning (leave empty for auto-detect)
NETWORK_CIDR=
INTERFACE=

# SNMP credentials
SNMP_COMMUNITY=public
SNMP_PORT=161

# InfluxDB connection
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=dev-token
INFLUX_ORG=local
INFLUX_BUCKET=network_metrics

# Alert thresholds
ALERT_LATENCY_MS=200
ALERT_PACKET_LOSS=0.5
```

## Development

### Linting & Formatting

This project uses `ruff` for linting and formatting.

### Common Commands

```bash
# Run tests
make test

# Lint code
make lint

# Type checking
make typecheck

# View all available commands
make help

# Clean build artifacts
make clean
```

See [Development Guide](docs/DEVELOPMENT.md) for detailed instructions.

## Project Structure

```text
Network-Device-Monitor/
├── backend/
│   ├── app/
│   │   ├── api/routers/      # FastAPI endpoints
│   │   ├── models/           # Pydantic models
│   │   ├── services/         # Business logic
│   │   ├── storage/          # Database repositories
│   │   ├── scheduler/        # Background jobs
│   │   └── utils/            # Helpers
│   ├── requirements/         # Dependencies
│   └── tests/               # Pytest tests
├── frontend/pyqt/           # PyQt6 desktop app
├── docs/                    # Documentation
├── docker/                  # Docker Compose + Dockerfiles
├── scripts/                 # Helper scripts
└── .github/workflows/       # CI/CD
```

## Contributing

This is currently a personal project in active development. Contributions welcome once MVP is complete.

## License

MIT License - See [LICENSE](LICENSE)

## Roadmap Highlights

- **v0.1.0** (MVP) - Discovery, monitoring, basic UI
- **v0.2.0** - SNMP metrics, bandwidth tracking, charts
- **v0.3.0** - Network topology visualization
- **v0.4.0** - Notifications, reporting, anomaly detection
- **v1.0.0** - Production-ready with security hardening

See full [Roadmap](docs/roadmap.md) for details.

---

**Next Implementation Phase:** [Milestone 1F - PyQt UI Development](docs/NEXT_STEPS.md)
