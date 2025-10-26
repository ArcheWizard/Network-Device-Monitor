# Next Steps: Milestone 2 — SNMP & Advanced Metrics

## Goal

Add SNMP-based interface statistics and bandwidth tracking, expose metrics via API, and visualize history in the PyQt UI. Improve alerting.

## Outcomes

- SNMP interface table discovery (indexes, descriptions, speeds)
- Periodic polling of byte counters (ifInOctets/ifOutOctets)
- Bandwidth calculation (bps) and storage in InfluxDB
- New REST endpoint: `GET /api/metrics/bandwidth`
- PyQt charts for latency and bandwidth over time
- Improved alerting pipeline (thresholds → events)

## Plan

### 1) SNMP Interface Table (HIGH)

Files: `backend/app/services/snmp.py`, `backend/app/services/identification.py`

- Implement `snmp_get_table(target, base_oid)` helper
- Retrieve: `ifIndex`, `ifDescr`, `ifSpeed`, `ifInOctets`, `ifOutOctets`
- Map interfaces by index and cache on first poll per device
- Respect settings: community, port, timeout

### 2) Bandwidth Poller (HIGH)

Files: `backend/app/scheduler/jobs.py`, `backend/app/storage/influx.py`

- Add periodic job to read ifIn/OutOctets for devices with SNMP enabled
- Compute deltas/interval → `in_bps`, `out_bps` with counter wrap handling
- Write points to InfluxDB: measurement `bandwidth`, tags `{device_id, ifIndex}`, fields `{in_bps, out_bps}`

### 3) API: GET /api/metrics/bandwidth (MEDIUM)

Files: `backend/app/api/routers/metrics.py`

- Add query handler mirroring latency endpoint contract
- Params: `device_id`, `ifIndex?`, `limit`, `start` (Influx duration)
- Response: `{ device_id, ifIndex?, points: [{ ts, in_bps, out_bps }] }`

### 4) PyQt Charts (MEDIUM)

Files: `frontend/pyqt/src/main_window.py` (or new chart widget)

- Add simple time-series charts for latency and bandwidth (pick lightweight lib or QtCharts)
- Toggle device/iface selection and timeframe (e.g., 1h/24h)
- Keep updates lightweight; pull snapshots via REST and stream deltas via WS (future)

### 5) Alerts (MEDIUM)

Files: `backend/app/services/notifications.py`, `backend/app/scheduler/jobs.py`

- Trigger alerts when `packet_loss > ALERT_PACKET_LOSS` or `ms > ALERT_LATENCY_MS`
- Extend for bandwidth thresholds (optional)
- Broadcast alert events on WebSocket; log to stdout/file

## Success Criteria

- [ ] Bandwidth points written to InfluxDB for at least one interface per device
- [ ] `GET /api/metrics/bandwidth` returns series with `in_bps/out_bps`
- [ ] Charts render latency and bandwidth for selected device
- [ ] Alerts are emitted on threshold breach and visible in logs/WS
- [ ] Unit tests cover SNMP helpers and bandwidth math

## Estimates

- SNMP table + polling: 8h
- Influx write/query for bandwidth: 3h
- API endpoint + tests: 3h
- PyQt chart + wiring: 4h
- Alerts integration: 2h
- Buffer for polish: 2h
- Total: ~22h

## Notes

- Keep SNMP v2c for now; consider v3 later
- Use exponential backoff on SNMP timeouts
- Limit interfaces polled (skip down/loopback)
