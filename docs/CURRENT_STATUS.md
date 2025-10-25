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

## Completed (Milestone 1: MVP - Discovery & Monitoring)

All phases of Milestone 1 are finished and verified with tests and documentation. See `docs/MILESTONE_1_COMPLETION.md` for a full summary.

### Phase 1A: Discovery Service (COMPLETED ✅)

- [x] Implement ARP scan using scapy (`backend/app/services/discovery.py`)
- [x] Implement async ICMP ping sweep
- [x] Add mDNS/Bonjour discovery via zeroconf
- [x] Wire auto-detect interfaces to discovery service
- [x] Add POST /api/discovery/scan endpoint with CIDR/interface/timeout/persist/identify overrides
- [x] **BONUS:** WiFi fallback using `arp-scan` and system ARP cache for compatibility
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
- [x] Add SNMP queries (sysName, sysDescr, sysUpTime, sysContact, sysLocation, sysObjectID) in `backend/app/services/snmp.py`
- [x] Implement device identification service (`backend/app/services/identification.py`)
- [x] Wire identification to discovery scan endpoint with optional flags
- [x] Create OUI database download script (`scripts/seed_oui.sh`)
- [x] Add OUI lookup unit tests (`backend/tests/test_oui_lookup.py`)
- [x] Add identification service unit tests (`backend/tests/test_identification.py`)
- [x] **BONUS:** DNS reverse lookup for hostname resolution when SNMP unavailable

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
  - Broadcast status changes via WebSocket
  - Update last_seen timestamp
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

### Phase 1F: PyQt UI (COMPLETED ✅)

**Backend Integration:**

- [x] Implement REST API client in `frontend/pyqt/src/api_client.py`
  - [x] `fetch_devices() -> list[Device]` using httpx.AsyncClient
  - [x] `trigger_scan()` with optional parameters
  - [x] WebSocket streaming with auto-reconnect and exponential backoff
  - [x] Helper function `_http_to_ws()` for URL conversion
  - [x] Graceful `aclose()` for cleanup

**UI Components:**

- [x] Create MainWindow in `frontend/pyqt/src/main_window.py`
  - [x] Backend URL input field
  - [x] Refresh and Scan buttons
  - [x] Device table with 8 columns (ID, IP, MAC, Hostname, Vendor, Status, Latency, Loss)
  - [x] Status bar for user feedback
  - [x] QThread worker classes (FetchDevicesWorker, TriggerScanWorker, EventStreamWorker)
  - [x] Worker `_run()` methods implemented with proper async/await
  - [x] `upsert_device_row()` logic for table population
  - [x] `on_event()` WebSocket handler for real-time updates
  - [x] Thread cleanup in `closeEvent()` and `on_app_quit()`

**Entry Point:**

- [x] Create `frontend/pyqt/src/app.py` with PyQt6 imports
  - [x] Support both script and module import contexts
  - [x] Proper `app.exec()` usage for PyQt6

**Testing:**

- [x] Add `frontend/pyqt/tests/test_api_client.py` with mocked httpx/websockets
- [x] Add `frontend/pyqt/tests/test_workers.py` for QThread workers
- [x] Add `frontend/pyqt/tests/test_main_window.py` for UI logic

**Status:** ✅ COMPLETE - Fully functional PyQt6 desktop UI with real-time WebSocket updates, device table, and background workers.

## Milestone 1 Status: ✅ COMPLETE (100%)

For what’s next, see `docs/roadmap.md` and `docs/NEXT_STEPS.md`.
