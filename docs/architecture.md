# Architecture

## Components

- API Layer (FastAPI)
  - REST endpoints for devices, metrics, config
  - WebSocket for real-time events (device up/down, latency updates)
- Services
  - discovery: ARP sweep (scapy), ICMP ping sweep, mDNS browse (zeroconf)
  - identification: OUI lookup, banner/port scan (select ports), SNMP sysName/sysDescr
  - monitoring: scheduled pings per device, optional bandwidth via SNMP ifInOctets/ifOutOctets
  - notifications: threshold checks → send events
- Storage
  - SQLite: device inventory (devices, interfaces, tags)
  - InfluxDB: time-series (latency, packet loss, bandwidth)
  - repository: abstraction to write to either backend
- Scheduler (APScheduler)
  - periodic discovery (e.g., every 10 min)
  - monitoring ticks (e.g., every 5–10 s per device)
- Frontend (PyQt)
  - subscribes WS for updates; REST for data snapshots
  - topology view (later) using networkx + graph widget

## Data Flow

1. discovery scans subnets and publishes found MAC/IP tuples
2. identification enriches with vendor via OUI and SNMP (if available)
3. devices persisted to SQLite; metrics scheduled for monitoring
4. monitoring writes latency/loss to InfluxDB (or SQLite fallback)
5. notifications triggered by thresholds; pushed via WS and durable log

## Security/Permissions

- scapy requires CAP_NET_RAW; prefer setcap on venv python over sudo
- SNMP v2c community strings stored via environment variables
- Never expose API publicly without auth (future: JWT/API keys + TLS)
