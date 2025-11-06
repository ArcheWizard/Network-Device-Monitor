# Installation Guide

Complete installation instructions for all deployment scenarios.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Docker Installation](#docker-installation)
- [Manual Installation](#manual-installation)
- [Development Installation](#development-installation)
- [Post-Installation](#post-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+), macOS 11+, Windows 10+ (WSL2)
- **Python**: 3.11 or higher
- **RAM**: 512 MB minimum (2 GB recommended)
- **Disk**: 500 MB free space
- **Network**: Access to target network with appropriate permissions

### Required Permissions

```bash
# Linux: Required for raw socket operations (Scapy)
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)

# Or run with sudo (not recommended for production)
sudo python3 backend/app/main.py
```

### Optional Dependencies

- **InfluxDB 2.x**: For time-series metrics storage
- **Docker & Docker Compose**: For containerized deployment
- **mise**: For automatic Python version management

## Installation Methods

### Quick Comparison

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| Docker | Production, Testing | Isolated, reproducible | Requires Docker |
| Manual | Customization | Full control | Manual dependency management |
| Development | Contributors | Hot reload, debugging | Requires more setup |

## Docker Installation

### Using Docker Compose

```bash
# Clone repository
git clone <repository-url>
cd Network-Device-Monitor

# Build and start services
cd docker
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Access API
curl http://localhost:8000/health
```

### Configuration

Edit `docker/.env` before starting:

```env
NETWORK_CIDR=192.168.1.0/24
SNMP_COMMUNITY=public
INFLUX_URL=http://influxdb:8086
```

## Manual Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd Network-Device-Monitor
```

### Step 2: Set Up Python Environment

```bash
# Using venv
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements/prod.txt
```

### Step 3: Configure Environment

```bash
# Create .env file in backend directory
cat > backend/.env << EOF
NETWORK_CIDR=192.168.1.0/24
INTERFACE=eth0
SNMP_COMMUNITY=public
EOF
```

### Step 4: Initialize Database

```bash
# SQLite database is created automatically on first run
# Optional: Pre-seed OUI database
bash scripts/seed_oui.sh
```

### Step 5: Start Backend

```bash
cd backend
python -m app.main
```

Backend will be available at `http://localhost:8000`

### Step 6: Install Frontend (Optional)

```bash
cd frontend/pyqt
pip install -r requirements.txt
python src/app.py
```

## Development Installation

### Using mise (Recommended)

```bash
# Install mise if not already installed
curl https://mise.run | sh

# Install Python version automatically
mise install

# Install development dependencies
cd backend
pip install -r requirements/dev.txt

# Install pre-commit hooks
pre-commit install
```

### Manual Development Setup

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install with dev dependencies
cd backend
pip install -r requirements/dev.txt

# Install project in editable mode
pip install -e .
```

## Post-Installation

### Optional: InfluxDB Setup

```bash
# Using Docker
docker run -d -p 8086:8086 \
  --name influxdb \
  -v influxdb-data:/var/lib/influxdb2 \
  influxdb:2.7

# Access UI: http://localhost:8086
# Create organization, bucket, and token
# Update backend/.env with credentials
```

### Optional: System Service

Create `/etc/systemd/system/network-monitor.service`:

```ini
[Unit]
Description=Network Device Monitor
After=network.target

[Service]
Type=simple
User=monitor
WorkingDirectory=/opt/network-monitor/backend
Environment="PATH=/opt/network-monitor/venv/bin"
ExecStart=/opt/network-monitor/venv/bin/python -m app.main
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable network-monitor
sudo systemctl start network-monitor
```

## Verification

### Backend Health Check

```bash
# API health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2024-01-01T00:00:00Z"}
```

### Test Discovery

```bash
# Trigger discovery
curl -X POST http://localhost:8000/api/devices/discover

# Check discovered devices
curl http://localhost:8000/api/devices
```

### Frontend Connection

```bash
# Launch PyQt frontend
cd frontend/pyqt
python src/app.py

# Should connect to backend and display dashboard
```

## Troubleshooting

### Permission Errors

**Symptom**: "Operation not permitted" when discovering devices

**Solution**:

```bash
# Grant CAP_NET_RAW capability
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)

# Or run with sudo
sudo python3 backend/app/main.py
```

### Port Already in Use

**Symptom**: "Address already in use" on port 8000

**Solution**:

```bash
# Find process using port
lsof -i :8000

# Kill process or change port in config.py
# Set PORT environment variable
PORT=8001 python -m app.main
```

### InfluxDB Connection Failed

**Symptom**: Cannot connect to InfluxDB

**Solution**:

- Verify InfluxDB is running: `docker ps | grep influxdb`
- Check credentials in `.env`
- Test connection: `curl http://localhost:8086/health`
- Backend will fall back to SQLite if InfluxDB unavailable

### No Devices Discovered

**Symptom**: Discovery returns empty list

**Solution**:

- Verify NETWORK_CIDR matches your network
- Check interface: `ip addr` or `ifconfig`
- Ensure target devices are powered on
- Test manually: `ping 192.168.1.1`
- Check firewall rules

### Import Errors

**Symptom**: `ModuleNotFoundError` when starting

**Solution**:

```bash
# Reinstall dependencies
pip install -r backend/requirements/prod.txt

# Verify Python version
python --version  # Should be 3.11+

# Check virtual environment is activated
which python  # Should point to venv
```

## Next Steps

- [Configuration Guide](03-configuration.md) - Customize settings
- [Quick Start](01-quick-start.md) - 5-minute getting started
- [Development Guide](10-development.md) - Set up development environment
- [API Reference](40-api-reference.md) - REST API documentation
