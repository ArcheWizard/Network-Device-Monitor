# Network Device Mapper & Monitor

![Backend CI](https://github.com/ArcheWizard/Network-Device-Monitor/workflows/Backend%20CI/badge.svg)
![Frontend CI](https://github.com/ArcheWizard/Network-Device-Monitor/workflows/Frontend%20(PyQt)%20CI/badge.svg)
![Lint](https://github.com/ArcheWizard/Network-Device-Monitor/workflows/Lint%20Markdown/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.2-009688.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.1-41CD52.svg)

**Status:** ✅ **MVP Complete** - Milestone 1 finished! Discovery, Storage, Identification, Monitoring, WebSocket Streaming & PyQt UI all operational.

Async Python backend + PyQt6 frontend to discover devices on local networks, identify type/manufacturer, and monitor health (latency, uptime, bandwidth, connectivity) with alerts and history.

**Current Phase:** Milestone 1 Complete - Ready for Milestone 2 (SNMP & Advanced Metrics)

## Features

- ✅ Network discovery: ARP (scapy), ICMP ping sweep, mDNS/Bonjour (zeroconf), WiFi fallback
- ✅ Device identification: OUI lookup (IEEE database), SNMP v2c (sysName, sysDescr, etc.), DNS reverse lookup
- ✅ Health monitoring: periodic ping latency + packet loss stored in InfluxDB
- ✅ Real-time WebSocket streaming: device discovery, status changes, latency metrics
- ✅ Data persistence: SQLite for inventory + InfluxDB for time-series metrics
- ✅ PyQt6 desktop GUI with real-time updates, device table, and monitoring metrics
- 🚧 Notifications: device offline/online, high latency thresholds (basic implementation, needs enhancement)

**Legend:** ✅ Complete | 🚧 In Progress | ⏳ Planned

## Screenshots

### PyQt6 Desktop Interface

![PyQt6 main window](docs/screenshots/Frontend_Normal.png)

_Main window with live device table, vendor identification, and status._

![PyQt6 discovery](docs/screenshots/Frontend_Discovering.png)

_Discovery completed — statuses reflect up/down with live updates._

![PyQt6 scan](docs/screenshots/Frontend_Scanning_Done.png)

_Scan completed — all devices monitored with real-time metrics._

> Note: If images do not render on GitHub, ensure the files exist at
> docs/screenshots/Frontend_Normal.png and docs/screenshots/Frontend_Discovering.png
> (you can rename your screenshots to match or update these links).

**Key UI Features:**

- **Device Table**: Live view of all discovered devices with IP, MAC, hostname, vendor, and status
- **Real-time Updates**: WebSocket-powered instant updates when devices come online/offline
- **Discovery Controls**: On-demand network scanning with configurable parameters
- **Status Bar**: Connection status and live event notifications
- **Metrics Display**: Current latency and packet loss for monitored devices

### Backend API (Swagger UI)

![API Swagger Docs](docs/screenshots/API_Normal.png)

**Available Endpoints:**

- `GET /api/health` - Health check
- `GET /api/devices` - List all discovered devices
- `POST /api/discovery/scan` - Trigger network scan
- `GET /api/metrics/latency` - Query time-series latency data
- `WS /ws/stream` - Real-time event streaming

### InfluxDB Metrics Dashboard

![InfluxDB Latency Dashboard](docs/screenshots/InfluxDB_Normal.png)

_Time-series latency and packet loss metrics stored in InfluxDB._

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

**✅ Completed (Milestone 0 + Milestone 1 A–F):**

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

**⏳ Next Up (Milestone 2 — SNMP & Advanced Metrics):**

- SNMP interface table (ifIndex/ifDescr/ifSpeed)
- Bandwidth tracking via ifIn/OutOctets → bps
- Metrics charts in PyQt (latency + bandwidth)
- Improved alerts (thresholds via WS/log)

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

**Next Implementation Phase:** [Milestone 2 — SNMP & Advanced Metrics](docs/NEXT_STEPS.md)
