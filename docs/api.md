# API (initial)

## REST

- GET /api/health
- GET /api/devices (returns list of all devices from SQLite)
- GET /api/devices/{device_id} (get device by ID)
- POST /api/discovery/scan (trigger on-demand; optional body: {cidr, interface, arp_timeout, ping_timeout, persist})
  - Response: {count, devices, persisted}
- GET /api/metrics/latency?device_id=&limit=
- GET /api/metrics/bandwidth?device_id=&limit=

## WebSocket

- /ws/stream
  - event payloads:
    - { "type": "device_up|device_down", "device_id": "...", "ip": "...", "ts": ... }
    - { "type": "latency", "device_id": "...", "ms": 12.4, "loss": 0.0, "ts": ... }
  - { "type": "alert", "severity": "warn|crit", "message": "...", "ts": ... }
