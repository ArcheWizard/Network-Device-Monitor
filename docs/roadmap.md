# Roadmap

## ✅ Milestone 0: Scaffolding (COMPLETED)

- [x] Repository structure (backend/frontend/docs/docker/scripts)
- [x] Backend FastAPI skeleton + health endpoint
- [x] PyQt6 frontend window shell
- [x] Auto-detect network interfaces utility
- [x] InfluxDB Docker Compose setup
- [x] CI/CD workflows (backend lint/test)
- [x] Development environment (Makefile, .env, scripts)
- [x] Documentation (architecture, API, database, ops, security)

## 🚧 Milestone 1: MVP - Core Discovery & Monitoring (IN PROGRESS)

**Goal:** Discover devices on local network, identify them, monitor basic health, and display in UI.

### Phase 1A: Discovery Service (COMPLETED ✅ - ~8 hours)

- [x] Implement ARP scan with scapy in `backend/app/services/discovery.py`
- [x] Implement async ICMP ping sweep
- [x] Add mDNS/Bonjour discovery via zeroconf
- [x] Wire auto-detect interfaces to discovery
- [x] Add `POST /api/discovery/scan` endpoint with CIDR/interface/timeout overrides
- [x] Wire discovery to scheduler for periodic scans
- [x] Add unit tests with mocked scapy responses
- [x] Add robust logging and error handling

### Phase 1B: Storage Layer (COMPLETED ✅ - ~6 hours)

- [x] Create SQLite schema for device inventory
- [x] Implement `backend/app/storage/sqlite.py` with aiosqlite
  - [x] `upsert_device(data: dict)`
  - [x] `list_devices() -> list[dict]`
  - [x] `get_device(id: str) -> dict | None`
- [x] Initialize databases on app startup
- [x] Add repository integration tests
- [x] Wire discovery to persist results to SQLite
- [x] Add GET `/api/devices/{device_id}` endpoint

### Phase 1C: Device Identification (COMPLETED ✅ - ~4 hours)

- [x] Download IEEE OUI database (via `scripts/seed_oui.sh`)
- [x] Implement OUI lookup in `backend/app/utils/oui.py`
  - Parse and cache OUI data (CSV format)
  - `lookup_vendor(mac: str) -> str | None`
  - Auto-download from IEEE or Wireshark sources
- [x] Add SNMP queries in `backend/app/services/snmp.py`
  - `snmp_get(target, oid)` - single OID query
  - `snmp_get_bulk(target, oids)` - parallel queries
  - `snmp_identify(target)` - common identification OIDs
- [x] Implement device identification in `backend/app/services/identification.py`
  - `identify_device(ip, mac, use_oui, use_snmp)`
  - Merge OUI and SNMP results
- [x] Wire identification to discovery scan endpoint with optional flags
- [x] Add unit tests for OUI lookup and identification

### Phase 1D: Monitoring Service (COMPLETED ✅ - ~6 hours)

- [x] Implement ping monitoring in `backend/app/services/monitoring.py`
  - Track latency (avg, min, max in ms) and packet loss percentage
  - Use asyncio subprocess with ping command
  - Parse ping output with regex for metrics extraction
- [x] Implement InfluxDB writer in `backend/app/storage/influx.py`
  - `init_influx()` to create client and connect
  - `write_metric(measurement, tags, fields)` for storing metrics
  - `query_metrics(measurement, device_id, start, limit)` for reading data
- [x] Store metrics to InfluxDB with tags (device_id, ip) and fields (latency_*, packet_loss)
- [x] Wire to scheduler (`monitoring_tick` job every 5s)
  - Fetch all devices from SQLite
  - Ping each device and collect metrics
  - Write to InfluxDB
  - Update device status in SQLite
  - Log status transitions (up/down)
- [x] Detect device up/down transitions
- [x] Add GET `/api/metrics/latency` endpoint to query InfluxDB
- [x] Add status field to device model and SQLite schema
- [x] Add unit tests for ping parsing

### Phase 1E: WebSocket Streaming (COMPLETED ✅ - ~3 hours)

- [x] Implement WebSocket connection manager in `backend/app/api/routers/ws.py`
  - `ConnectionManager` class with connect/disconnect/broadcast
  - Handle multiple concurrent WebSocket clients
- [x] Add WebSocket endpoint `/ws/stream`
  - Send hello message on connection
  - Keep connection alive for streaming events
- [x] Broadcast events: `device_discovered`, `device_up`, `device_down`, `latency`
  - Wire discovery_job to broadcast newly discovered devices
  - Wire monitoring_tick to broadcast latency metrics
  - Wire monitoring_tick to broadcast status change events
- [x] Define JSON event message formats for all event types
- [x] Test with multiple concurrent WebSocket clients
- [x] Add unit tests for ConnectionManager (`tests/test_websocket.py`)

### Phase 1F: PyQt UI - Device List (NEXT - ~8 hours)

- [ ] Implement REST API client in `frontend/pyqt/src/api_client.py`
  - `fetch_devices() -> list[Device]`
  - `trigger_scan()`
- [ ] Implement WebSocket subscriber (separate thread)
- [ ] Create device table widget in `frontend/pyqt/src/main_window.py`
  - Show IP, MAC, vendor, hostname, status
  - Update in real-time from WebSocket
- [ ] Add "Scan Network" button
- [ ] Show latency/packet loss in table
- [ ] Add status indicators (online/offline/high latency)

### Phase 1G: Basic Alerts (~2 hours)

- [ ] Implement notification service in `backend/app/services/notifications.py`
- [ ] Log alerts to console/file
- [ ] Push alerts via WebSocket
- [ ] Show alerts in PyQt UI (toast/notification area)

**Total Estimated Effort:** ~37 hours

**Definition of Done:**

- Network scan discovers devices on local subnet
- Devices stored in SQLite with vendor identification
- Latency metrics tracked and stored in InfluxDB
- PyQt UI shows real-time device list with status
- Alerts triggered when device goes offline or latency high

## 📋 Milestone 2: SNMP & Advanced Metrics (~20 hours)

- [ ] SNMP interface table queries (ifIndex, ifDescr, ifSpeed)
- [ ] Bandwidth tracking via SNMP counters (ifInOctets, ifOutOctets)
- [ ] Calculate bandwidth usage (bps) from counter deltas
- [ ] Store bandwidth metrics to InfluxDB
- [ ] Add metrics charts to PyQt UI (latency/bandwidth over time)
- [ ] Add GET `/api/metrics/bandwidth` endpoint
- [ ] Historical data export (CSV/JSON)

## 📋 Milestone 3: Topology & Integrations (~30 hours)

- [ ] Detect device relationships (ARP table parsing, LLDP/CDP)
- [ ] Build network topology graph (routers, switches, endpoints)
- [ ] Implement topology visualization in `frontend/pyqt/src/topology_view.py`
  - Use networkx for graph computation
  - Use PyQt graphics view for rendering
- [ ] Router API integrations:
  - [ ] UniFi Controller API
  - [ ] pfSense API
  - [ ] MikroTik RouterOS API
- [ ] Enhanced device classification (IoT, server, workstation, mobile)
- [ ] Device grouping and tagging

## 📋 Milestone 4: Notifications & Reporting (~15 hours)

- [ ] Email notifications (SMTP)
- [ ] Webhook notifications (Slack, Discord, generic HTTP)
- [ ] Notification rules engine (threshold-based, device-specific)
- [ ] Generate network health reports (PDF/HTML)
- [ ] Anomaly detection (baseline deviations)
- [ ] Scheduled reports (daily/weekly summaries)

## 📋 Milestone 5: Security & Hardening (~10 hours)

- [ ] API authentication (JWT tokens or API keys)
- [ ] TLS/HTTPS support
- [ ] Detect unauthorized devices (MAC whitelist/blacklist)
- [ ] ARP spoofing detection
- [ ] Audit logging (track all scans and changes)
- [ ] Role-based access control (admin/viewer)

## 📋 Milestone 6: Packaging & Deployment (~12 hours)

- [ ] Package PyQt app as standalone binary (PyInstaller/cx_Freeze)
- [ ] Create Windows installer (NSIS/Inno Setup)
- [ ] Create Linux AppImage/Flatpak
- [ ] Dockerize backend for production
- [ ] Docker Compose production setup (backend + InfluxDB + reverse proxy)
- [ ] Kubernetes manifests (optional)
- [ ] Automated releases via GitHub Actions

## 🔮 Future Enhancements (Backlog)

- [ ] Mobile app (Flutter companion)
- [ ] Multi-site support (monitor multiple networks remotely)
- [ ] SNMP traps receiver
- [ ] NetFlow/sFlow analysis
- [ ] Port mirroring and packet capture integration
- [ ] Integration with Grafana for dashboards
- [ ] Plugin system for custom integrations
- [ ] REST API documentation (OpenAPI/Swagger export)

## Version Targets

- **v0.1.0** - Milestone 1 complete (MVP)
- **v0.2.0** - Milestone 2 complete (SNMP + metrics)
- **v0.3.0** - Milestone 3 complete (topology)
- **v0.4.0** - Milestone 4 complete (notifications)
- **v1.0.0** - Milestones 5-6 complete (production-ready)
