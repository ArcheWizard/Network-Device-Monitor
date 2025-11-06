# Quick Start Guide

Get Network Device Monitor up and running in 5 minutes.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Linux: libpcap headers (`sudo apt-get install libpcap-dev python3-dev`)

## Installation

### 1. Clone and Setup

```bash
git clone <repo-url> Network-Device-Monitor
cd Network-Device-Monitor
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements/dev.txt
```

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env - set INFLUX_TOKEN after step 4
```

### 3. Grant Network Permissions (Linux)

```bash
sudo setcap cap_net_raw,cap_net_admin=eip "$(readlink -f .venv/bin/python)"
```

### 4. Start InfluxDB

```bash
docker compose -f docker/docker-compose.yml up -d
```

Get your InfluxDB token:

1. Visit <http://localhost:8086>
2. Login: admin / admin12345
3. Data → Tokens → Generate Token
4. Copy token to `backend/.env` as `INFLUX_TOKEN`

### 5. Run Backend

```bash
make dev
```

### 6. Run Frontend (Optional)

```bash
pip install -r frontend/pyqt/requirements.txt
python frontend/pyqt/src/app.py
```

## Verify Installation

### Check API Health

```bash
curl http://localhost:8000/api/health
# Should return: {"status":"ok"}
```

### Trigger Discovery

```bash
curl -X POST http://localhost:8000/api/discovery/scan \
  -H "Content-Type: application/json" \
  -d '{"persist": true, "identify": true}'
```

### List Discovered Devices

```bash
curl http://localhost:8000/api/devices | jq
```

## Access Points

- **API**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>
- **InfluxDB UI**: <http://localhost:8086>
- **WebSocket**: ws://localhost:8000/ws/stream

## Next Steps

- Read [Configuration Guide](03-configuration.md) for customization
- See [Development Guide](10-development.md) for development workflow
- Check [Troubleshooting](31-troubleshooting.md) if you encounter issues

## Common Issues

**Permission denied with scapy?**

```bash
sudo setcap cap_net_raw,cap_net_admin=eip "$(readlink -f .venv/bin/python)"
```

**InfluxDB connection refused?**

```bash
docker compose -f docker/docker-compose.yml ps  # Check if running
docker compose -f docker/docker-compose.yml logs influxdb  # Check logs
```

**Port 8000 already in use?**

```bash
lsof -i :8000  # Find process
kill -9 <PID>  # Kill it
```
