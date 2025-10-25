# Next Steps: Milestone 1F - PyQt UI Development

## Goal

Implement PyQt6 desktop UI with device table, real-time WebSocket updates, and monitoring metrics display.

## Implementation Plan

### Step 1: REST API Client (Priority: HIGH)

**File:** `frontend/pyqt/src/api_client.py`

**Tasks:**

1. Implement `APIClient` class with async HTTP methods
2. Add `fetch_devices() -> list[dict]` to get all devices from `/api/devices`
3. Add `trigger_scan(cidr: str = None) -> dict` to POST `/api/discovery/scan`
4. Add error handling and connection retry logic
5. Support configurable backend URL (default: <http://localhost:8000>)

**Example Code Pattern:**

```python
import httpx
from typing import Optional

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def fetch_devices(self) -> list[dict]:
        response = await self.client.get("/api/devices")
        response.raise_for_status()
        return response.json()

    async def trigger_scan(self, cidr: Optional[str] = None) -> dict:
        payload = {}
        if cidr:
            payload["cidr"] = cidr
        response = await self.client.post("/api/discovery/scan", json=payload)
        response.raise_for_status()
        return response.json()
```

- `{"type": "latency", "device_id": "...", "latency_avg": 12.4, "packet_loss": 0.0, "ts": 123456789}`

### Step 3: Metrics Streaming (Priority: MEDIUM)

**Tasks:**

1. Stream latency metrics in real-time from monitoring_tick()
2. Include device_id, latency metrics, and timestamp
3. Throttle updates to avoid overwhelming clients (e.g., max 1 update per device per second)

### Step 4: Testing (Priority: LOW)

**File:** `backend/tests/test_websocket.py` (new file)

**Tasks:**

1. Test WebSocket connection/disconnection
2. Test broadcast to multiple clients
3. Test event message formats
4. Test graceful handling of client disconnections

## Success Criteria (WebSocket)

- [ ] Multiple WebSocket clients can connect simultaneously
- [ ] Device discovery results broadcast to all connected clients
- [ ] Status changes (up/down) broadcast in real-time
- [ ] Latency metrics stream to connected clients
- [ ] Clients can reconnect after disconnect
- [ ] Unit tests pass

## Estimated Effort (WebSocket)

- Connection manager: 1 hour
- Event broadcasting integration: 2 hours
- Metrics streaming: 1 hour
- Testing: 1 hour
- **Total: ~5 hours**

## Next After This

Once WebSocket streaming works, proceed to:

1. **Phase 1F:** PyQt UI with device list and real-time updates
2. **Phase 1G:** Notification system for alerts
3. Implement `write_metric(measurement: str, tags: dict, fields: dict)`
4. Use `influxdb_client.Point` to construct data points
5. Handle connection errors gracefully

**Example Code Pattern:**

```python
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

async def write_metric(measurement: str, tags: dict, fields: dict):
    """Write metric to InfluxDB."""
    async with InfluxDBClientAsync(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG) as client:
        write_api = client.write_api()
        point = Point(measurement).tag(**tags).field(**fields)
        await write_api.write(bucket=INFLUX_BUCKET, record=point)
```

### Step 3: Monitoring Job (Priority: MEDIUM)

**File:** `backend/app/scheduler/jobs.py`

**Tasks:**

1. Update `monitoring_tick()` to fetch all devices from SQLite
2. For each device, call `monitoring.ping_device(ip)`
3. Write metrics to InfluxDB via `influx.write_metric()`
4. Update device status in SQLite (last_seen timestamp)
5. Detect state transitions (up → down, down → up) and log

### Step 4: Metrics API Endpoint (Priority: MEDIUM)

**File:** `backend/app/api/routers/metrics.py`

**Tasks:**

1. Add `GET /api/metrics/{device_id}` to fetch metrics from InfluxDB
2. Query last N minutes of latency/packet loss data
3. Return time-series array for charting

### Step 5: Testing (Priority: LOW)

**File:** `backend/tests/test_monitoring.py` (new file)

**Tasks:**

1. Mock subprocess ping output for unit tests
2. Test metric parsing (latency, packet loss)
3. Test InfluxDB writer with in-memory mock
4. Test monitoring job with fake device list

## Success Criteria (Monitoring)

- [ ] Monitoring job runs every 5-10 seconds and pings all devices
- [ ] Metrics (latency, packet loss) stored in InfluxDB
- [ ] `GET /api/metrics/{device_id}` returns time-series data
- [ ] Device status (up/down) updated in SQLite
- [ ] Logs show state transitions (device offline/online)
- [ ] Unit tests pass

## Estimated Effort

- Ping monitoring service: 2-3 hours
- InfluxDB writer: 2 hours
- Monitoring job integration: 2 hours
- Metrics API endpoint: 1-2 hours
- Testing + debugging: 2 hours
- **Total: ~10 hours**

## Next After This (Monitoring)

Once monitoring works, proceed to:

1. **Phase 1E:** WebSocket streaming for real-time updates
2. **Phase 1F:** PyQt UI with device list and metrics
3. **Phase 1G:** Notification system for alerts
