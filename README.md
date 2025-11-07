# Network Device Monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Backend CI](https://github.com/ArcheWizard/Network-Device-Monitor/workflows/Backend%20CI/badge.svg)](https://github.com/ArcheWizard/Network-Device-Monitor/actions)

A powerful network monitoring and device discovery tool built with Python, FastAPI, and PyQt6. Monitor your network devices in real-time, track metrics, and gain insights into your network topology.

## ✨ Features

### � Authentication & Security (NEW in v0.2.0)

- **JWT Token Authentication** - Secure token-based API authentication
- **User Management** - Multi-user support with registration and login
- **Role-Based Access Control** - Admin, Operator, and Viewer roles
- **Password Security** - Bcrypt hashing with strength validation
- **Optional Authentication** - Can be enabled/disabled via configuration

### �🔍 Network Discovery

- **Automated ARP Scanning** - Discover devices on your network using ARP
- **Ping Sweep** - Fast parallel ping scanning with configurable concurrency
- **mDNS/Zeroconf Discovery** - Detect services advertised via mDNS/Bonjour
- **SNMP Identification** - Query device information via SNMPv2c
- **Vendor Identification** - MAC address to vendor mapping using IEEE OUI database
- **DNS Reverse Lookup** - Resolve hostnames for discovered devices

### 📊 Monitoring & Metrics

- **Real-time Device Monitoring** - Continuous health checks and metrics collection
- **Latency Tracking** - Monitor network latency with min/avg/max measurements
- **Packet Loss Detection** - Track packet loss percentages
- **Time-series Storage** - Store metrics in InfluxDB for historical analysis
- **Device Status Tracking** - Monitor device up/down status

### 🖥️ User Interface

- **Desktop Application** - Native PyQt6 GUI for cross-platform use
- **Real-time Updates** - WebSocket-based live device status updates
- **Device Inventory** - View and manage discovered devices
- **Metrics Visualization** - Display latency and packet loss data

### 🔧 Backend API

- **RESTful API** - FastAPI-based REST endpoints for all operations
- **WebSocket Streaming** - Real-time event streaming
- **SQLite Inventory** - Persistent device storage
- **InfluxDB Integration** - Time-series metrics storage
- **Scheduled Tasks** - Automated discovery and monitoring jobs

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (for InfluxDB)
- **Linux**: `libpcap-dev` and `python3-dev` packages
- **macOS**: Xcode command line tools
- **Windows**: WSL2 recommended

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/ArcheWizard/Network-Device-Monitor.git
   cd Network-Device-Monitor
   ```

2. **Create virtual environment and install dependencies**

   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r backend/requirements/dev.txt
   ```

3. **Configure environment**

   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your settings
   ```

4. **Grant network permissions (Linux only)**

   ```bash
   sudo setcap cap_net_raw,cap_net_admin=eip "$(readlink -f .venv/bin/python)"
   ```

5. **Start InfluxDB**

   ```bash
   docker compose -f docker/docker-compose.yml up -d influxdb
   ```

   Visit <http://localhost:8086> to complete InfluxDB setup and get your token.

6. **Update `.env` with InfluxDB credentials**

   ```bash
   # Edit backend/.env
   INFLUX_URL=http://localhost:8086
   INFLUX_TOKEN=your-token-here
   INFLUX_ORG=local
   INFLUX_BUCKET=network_metrics
   ```

### Running the Application

#### Backend (API Server)

```bash
make dev
# Or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend
```

The API will be available at <http://localhost:8000>

#### Frontend (PyQt GUI)

```bash
make run-frontend
# Or: python frontend/pyqt/src/app.py
```

#### Using Docker Compose (Full Stack)

```bash
docker compose -f docker/docker-compose.yml up -d
```

## 📖 Documentation

Comprehensive documentation is available in the `docs/` directory:

### For Users & Developers

- **[Quick Start Guide](docs/human/01-quick-start.md)** - Get up and running in 5 minutes
- **[Installation Guide](docs/human/02-installation.md)** - Detailed installation instructions
- **[Configuration Guide](docs/human/03-configuration.md)** - Environment variables and settings
- **[Development Guide](docs/human/10-development.md)** - Development workflow and best practices
- **[Architecture Overview](docs/human/11-architecture.md)** - System design and components
- **[API Reference](docs/human/40-api-reference.md)** - REST API documentation

### For AI/Automation

- **[AI Documentation](docs/ai/)** - Machine-readable JSON schemas and specifications

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PyQt6 Desktop UI                        │
│              (Real-time WebSocket Updates)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend API                       │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   Discovery  │  │  Monitoring  │  │  Identification │  │
│  │   Service    │  │   Service    │  │     Service     │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │     SNMP     │  │  OUI Lookup  │  │  DNS Resolver   │  │
│  │    Client    │  │   (Vendor)   │  │                 │  │
│  └──────────────┘  └──────────────┘  └─────────────────┘  │
└───────────┬────────────────────────────────┬───────────────┘
            │                                │
            ▼                                ▼
┌───────────────────────┐      ┌───────────────────────────┐
│   SQLite Database     │      │    InfluxDB (Time-Series) │
│  (Device Inventory)   │      │     (Metrics Storage)     │
└───────────────────────┘      └───────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Network Layer                          │
│      ARP • ICMP • SNMP • mDNS/Zeroconf • DNS               │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **Backend API** - FastAPI application providing REST endpoints and WebSocket streaming
- **Discovery Service** - Network scanning using ARP, ping, and mDNS
- **Identification Service** - Device identification via SNMP, OUI lookup, and DNS
- **Monitoring Service** - Health checks and metrics collection
- **SQLite Repository** - Persistent device inventory storage
- **InfluxDB Writer** - Time-series metrics storage and retrieval
- **Scheduler** - APScheduler for periodic discovery and monitoring tasks
- **PyQt6 Frontend** - Desktop application with real-time updates

## 🧪 Testing

### Run Backend Tests

```bash
make -C backend test
# Or: pytest backend/tests/
```

### Run Frontend Tests

```bash
cd frontend/pyqt
pytest tests/
```

### Run All Tests with Coverage

```bash
pytest --cov=app --cov-report=html backend/tests/
```

### Code Quality

```bash
# Linting
make -C backend lint

# Type checking
make -C backend typecheck

# Format code
ruff format backend/
```

## 🔧 Configuration

Configuration is managed through environment variables. Key settings include:

| Variable | Description | Default |
|----------|-------------|---------|
| `NETWORK_CIDR` | Network range to scan | `192.168.1.0/24` |
| `INTERFACE` | Network interface to use | Auto-detect |
| `SNMP_COMMUNITY` | SNMP community string | `public` |
| `SNMP_TIMEOUT` | SNMP query timeout (seconds) | `1.0` |
| `INFLUX_URL` | InfluxDB server URL | `http://localhost:8086` |
| `INFLUX_TOKEN` | InfluxDB authentication token | - |
| `INFLUX_ORG` | InfluxDB organization | `local` |
| `INFLUX_BUCKET` | InfluxDB bucket name | `network_metrics` |
| `ALERT_LATENCY_MS` | Latency threshold for alerts (ms) | `200.0` |
| `ALERT_PACKET_LOSS` | Packet loss threshold for alerts | `0.5` |

See [Configuration Guide](docs/human/03-configuration.md) for complete details.

## 📋 API Endpoints

### Device Management

- `GET /api/devices` - List all discovered devices
- `GET /api/devices/{device_id}` - Get device details
- `POST /api/discovery/scan` - Trigger network discovery scan

### Metrics

- `GET /api/metrics/latency` - Get latency metrics for a device

### WebSocket

- `WS /ws/stream` - Real-time device updates and metrics stream

### Health Check

- `GET /api/health` - API health status

See [API Reference](docs/human/40-api-reference.md) for complete documentation.

## 🛣️ Roadmap

### Milestone 1: MVP - Discovery & Monitoring ✅ (COMPLETED)

- [x] Network discovery (ARP, ping, mDNS)
- [x] Device identification (SNMP, OUI, DNS)
- [x] Basic monitoring (ping-based)
- [x] SQLite inventory
- [x] InfluxDB metrics storage
- [x] REST API
- [x] WebSocket streaming
- [x] PyQt6 frontend

### Milestone 2: Advanced Features (PLANNED)

- [ ] Network topology visualization
- [ ] SNMP monitoring (bandwidth, CPU, memory)
- [ ] Alerting system (email, webhook)
- [ ] Device grouping and tagging
- [ ] Custom monitoring schedules
- [ ] Historical metrics analysis

### Milestone 3: Enterprise Features (FUTURE)

- [ ] Multi-site support
- [ ] Role-based access control
- [ ] Advanced alerting rules
- [ ] Integration with ticketing systems
- [ ] Performance optimization
- [ ] Web frontend

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Setting up development environment
- Code style and quality standards
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Scapy** - Network packet manipulation
- **FastAPI** - Modern Python web framework
- **PyQt6** - Cross-platform GUI framework
- **InfluxDB** - Time-series database
- **IEEE OUI Database** - MAC address vendor lookup

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/ArcheWizard/Network-Device-Monitor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ArcheWizard/Network-Device-Monitor/discussions)

## 🔒 Security

This tool requires elevated network permissions for packet capture and raw socket operations. See [Security Considerations](docs/human/03-configuration.md#security-settings) for best practices.

---

**Built with ❤️ by [ArcheWizard](https://github.com/ArcheWizard)**
