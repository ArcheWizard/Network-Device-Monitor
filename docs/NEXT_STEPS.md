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

### 5) Alerts Enhancement (MEDIUM)

Files: `backend/app/services/notifications.py`, `backend/app/scheduler/jobs.py`, `backend/app/models/alert.py`

**Current State:**

- Basic threshold checking for latency and packet loss
- Simple logging to stdout
- No alert state management or deduplication

**Improvements Needed:**

#### Alert Management System

- **Alert State Tracking**
  - Track active alerts per device/metric
  - Prevent duplicate alerts (alert deduplication)
  - Auto-resolve when condition clears
  - Alert history with timestamps

- **Alert Severity Levels**
  - `info`: Minor issues, FYI notifications
  - `warning`: Attention needed but not critical
  - `critical`: Immediate action required
  - Configurable severity thresholds per metric

- **Alert Rules Engine**
  - Flexible rule definition (YAML or database)
  - Multiple conditions per rule (AND/OR logic)
  - Time-based conditions (persist for N seconds)
  - Rate of change detection (sudden spikes)

#### Notification Channels

- **WebSocket Broadcast** (already partially implemented)
  - Real-time push to connected clients
  - Alert priority indication
  - Acknowledgement support

- **Email Notifications**
  - SMTP integration
  - HTML email templates
  - Configurable recipients per severity
  - Digest mode (batch alerts)

- **Webhook Support**
  - POST alert JSON to configured URLs
  - Integration with Slack, Discord, MS Teams
  - Custom payload formatting
  - Retry logic for failed deliveries

- **Logging Enhancement**
  - Structured logging (JSON format)
  - Separate alert log file
  - Log rotation and retention
  - Searchable alert history

#### Alert Types

- **Device Alerts**
  - Device offline/online
  - New device discovered
  - Device not seen for X minutes

- **Performance Alerts**
  - Latency exceeds threshold
  - Packet loss exceeds threshold
  - Bandwidth utilization high/low
  - Interface status change (up/down)

- **System Alerts**
  - Discovery scan failures
  - SNMP query failures
  - Database connectivity issues
  - InfluxDB write failures

#### Configuration

```python
# Example alert configuration
ALERTS = {
    "latency_high": {
        "condition": "latency_ms > ALERT_LATENCY_MS",
        "duration": 30,  # persist for 30s before alerting
        "severity": "warning",
        "channels": ["websocket", "email"],
        "message": "High latency detected on {device_hostname} ({device_ip}): {latency_ms}ms"
    },
    "device_offline": {
        "condition": "status == 'down'",
        "duration": 60,  # 1 minute offline
        "severity": "critical",
        "channels": ["websocket", "email", "webhook"],
        "message": "Device {device_hostname} ({device_ip}) is offline"
    },
    "bandwidth_spike": {
        "condition": "bandwidth_utilization > 80%",
        "duration": 120,
        "severity": "warning",
        "channels": ["websocket"],
        "message": "Bandwidth utilization high on {device_hostname}: {bandwidth_utilization}%"
    }
}
```

#### Implementation Tasks

- [ ] Create `Alert` model with state tracking
- [ ] Implement alert rule engine with condition evaluation
- [ ] Add alert deduplication logic
- [ ] Build email notification service (SMTP)
- [ ] Add webhook notification support
- [ ] Create alert history storage (SQLite table)
- [ ] Add alert acknowledgement API endpoint
- [ ] Implement alert muting/snoozing
- [ ] Build alert configuration UI in PyQt
- [ ] Add alert dashboard/log viewer
- [ ] Write comprehensive tests for alert logic

#### API Additions

```python
GET /api/alerts              # List active alerts
GET /api/alerts/history      # Alert history with filters
POST /api/alerts/{id}/ack    # Acknowledge alert
POST /api/alerts/{id}/mute   # Mute alert for duration
GET /api/alerts/config       # Get alert configuration
PUT /api/alerts/config       # Update alert rules
```

#### Success Metrics

- Alert response time < 5 seconds from condition detection
- Zero duplicate alerts for same condition
- Email delivery success rate > 95%
- Alert acknowledgement within UI updates alert state
- Historical alert query performance < 100ms

---

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
