# Current Status

## Completed (Milestone 0: Scaffolding)

- [x] Repository structure with backend/frontend/docs/docker/scripts
- [x] FastAPI backend skeleton with health endpoint
- [x] PyQt6 frontend window placeholder
- [x] InfluxDB Docker Compose setup
- [x] Auto-detect network interfaces utility
- [x] CI/CD workflows (backend lint/test, frontend placeholder)
- [x] Development environment setup (Makefile, scripts, .env)
- [x] Documentation structure (architecture, API, database, roadmap, ops, security)

## In Progress (Milestone 1: MVP - Discovery & Storage)

### Phase 1A: Discovery Service (COMPLETED ✅)

- [x] Implement ARP scan using scapy (`backend/app/services/discovery.py`)
- [x] Implement async ICMP ping sweep
- [x] Add mDNS/Bonjour discovery via zeroconf
- [x] Wire auto-detect interfaces to discovery service
- [x] Add POST /api/discovery/scan endpoint with CIDR/interface/timeout overrides
- [x] Add minimal unit test for discovery API (monkeypatched)
- [x] Add logging and error handling with parameterized timeouts

### Phase 1B: Storage Layer (COMPLETED ✅)

- [x] Implement SQLite repository with aiosqlite (`backend/app/storage/sqlite.py`)
- [x] Create device inventory schema (see `docs/database.md`)
- [x] Add device upsert/query methods (upsert_device, list_devices, get_device)
- [x] Initialize SQLite on app startup and attach to app.state
- [x] Wire POST /api/discovery/scan to persist discovered devices
- [x] Add GET /api/devices/{device_id} endpoint
- [x] Add repository unit tests (`backend/tests/test_sqlite_repo.py`)

### Phase 1C: Device Identification (COMPLETED ✅)

- [x] Download and cache IEEE OUI database (`backend/app/utils/oui.py`)
- [x] Implement MAC → vendor lookup with normalization
- [x] Add SNMP queries (sysName, sysDescr, sysUpTime, sysContact, sysLocation) in `backend/app/services/snmp.py`
- [x] Implement device identification service (`backend/app/services/identification.py`)
- [x] Wire identification to discovery scan endpoint with optional flags
- [x] Create OUI database download script (`scripts/seed_oui.sh`)
- [x] Add OUI lookup unit tests (`backend/tests/test_oui_lookup.py`)
- [x] Add identification service unit tests (`backend/tests/test_identification.py`)

### Phase 1D: Monitoring & Metrics (COMPLETED ✅)

- [x] Implement ping monitoring in `backend/app/services/monitoring.py`
  - Track latency (avg, min, max in ms)
  - Track packet loss percentage
  - Detect device up/down status
- [x] Implement InfluxDB writer in `backend/app/storage/influx.py`
  - Create InfluxMetricsWriter class with write_metric() and query_metrics()
  - Support tags and fields for flexible metric storage
  - Graceful fallback if InfluxDB not configured
- [x] Wire monitoring to scheduler (monitoring_tick every 5s)
  - Ping all devices from SQLite inventory
  - Write metrics to InfluxDB
  - Update device status in SQLite
  - Detect and log status transitions
- [x] Add GET `/api/metrics/latency` endpoint
  - Query metrics from InfluxDB
  - Support time range and limit parameters
- [x] Add device status field to SQLite schema
- [x] Add monitoring unit tests (`backend/tests/test_monitoring.py`)

### Phase 1E: WebSocket Streaming (COMPLETED ✅)

- [x] Implement ConnectionManager in `backend/app/api/routers/ws.py`
  - Handle connect/disconnect for multiple WebSocket clients
  - Broadcast messages to all connected clients
  - Send messages to specific clients
- [x] Add WebSocket endpoint `/ws/stream`
  - Send hello message on connection
  - Keep connection alive for real-time events
- [x] Wire discovery_job to broadcast device_discovered events
  - Detect newly discovered devices
  - Broadcast device details with timestamp
- [x] Wire monitoring_tick to broadcast metrics
  - Stream latency metrics for devices with status "up"
  - Broadcast device_up/device_down status change events
- [x] Define event message formats
  - hello: Initial connection greeting
  - device_discovered: New device found during scan
  - device_up: Device status changed to up
  - device_down: Device status changed to down
  - latency: Real-time latency metrics
- [x] Add WebSocket unit tests (`backend/tests/test_websocket.py`)
  - Test ConnectionManager connect/disconnect
  - Test broadcast to multiple clients
  - Test event message formats
  - Test graceful handling of disconnected clients

### Phase 1F: PyQt UI (NEXT)

- [ ] Device table widget with real-time updates
- [ ] API client implementation (`frontend/pyqt/src/api_client.py`)
- [ ] WebSocket subscription thread
- [ ] Basic metrics display (latency, status)

## Backlog (Future Milestones)

- SNMP bandwidth tracking
- Historical analytics & charts
- Topology visualization
- Notification system (email/webhook)
- Router API integrations
- Security features (unauthorized device detection)

## Technical Debt

- Add type stubs for scapy/pysnmp (mypy errors expected)
- Implement proper error handling in discovery services
- Add integration tests for scapy (requires elevated permissions)
- Document OUI database update procedure
