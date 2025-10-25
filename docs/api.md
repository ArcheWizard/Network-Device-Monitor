# API

Complete reference for the Network Device Monitor backend.

## REST Endpoints

### GET /api/health

Health check for the API.

- Response: `{ "status": "ok" }`

### GET /api/devices

List all devices from the SQLite inventory.

- Response: `Device[]`
- Device model fields:
  - `id: string`
  - `ip?: string`
  - `mac?: string`
  - `hostname?: string`
  - `vendor?: string`
  - `device_type?: string`
  - `status?: "up" | "down" | "unknown"`
  - `first_seen?: int` (unix ts)
  - `last_seen?: int` (unix ts)
  - `tags: Record<string, string>`

### GET /api/devices/{device_id}

Get a single device by ID.

- Path params:
  - `device_id: string`
- Response: `Device`

### POST /api/discovery/scan

Trigger an on-demand discovery scan. Optionally identify devices and persist to SQLite.

- Body (all optional):
  - `cidr: string` (e.g., "192.168.1.0/24")
  - `interface: string` (network interface to use)
  - `arp_timeout: number` (seconds)
  - `ping_timeout: number` (seconds)
  - `persist: boolean` (default: true) — write to SQLite
  - `identify: boolean` (default: true) — OUI + SNMP + DNS
- Response: `{ count: number, devices: Device[], persisted: boolean }`

### GET /api/metrics/latency

Get latency metrics for a device from InfluxDB.

- Query params:
  - `device_id: string` (required)
  - `limit: number` (default 100)
  - `start: string` (InfluxDB duration, e.g., "-1h", default: "-1h")
- Response: `{ device_id: string, points: { ts: int, ms: float, loss: float }[] }`
- Error (if Influx disabled): `{ error: string }`

Note: `GET /api/metrics/bandwidth` is reserved for Milestone 2 (SNMP bandwidth tracking).

## WebSocket

### ws://localhost:8000/ws/stream

Subscribe for real-time events. On connect, server sends a `hello` event.

Event types:

- `hello` — `{ type: "hello", ts: int }`
- `device_discovered` — `{ type: "device_discovered", ts: int, device: Device }`
- `device_up` — `{ type: "device_up", ts: int, device_id: string }`
- `device_down` — `{ type: "device_down", ts: int, device_id: string }`
- `latency` — `{ type: "latency", ts: int, device_id: string, ms: float, loss: float }`

Behavior:

- Discovery job broadcasts `device_discovered` for new/updated devices.
- Monitoring tick broadcasts `device_up`/`device_down` on status changes and `latency` for periodic measurements.
- Multiple clients supported; messages are broadcast to all connected clients.
