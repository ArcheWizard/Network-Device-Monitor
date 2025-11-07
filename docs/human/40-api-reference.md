# REST API Reference

Complete REST API documentation for Network Device Monitor.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. API is designed for local network access.

**Future**: JWT bearer token authentication will be added.

## Common Headers

```http
Content-Type: application/json
Accept: application/json
```

## Error Responses

All endpoints follow consistent error response format:

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET/PUT/DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side error |

## Endpoints

### Health Check

#### GET /health

Check API health status.

**Request**

```bash
curl http://localhost:8000/health
```

**Response** `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

### Devices

#### GET /api/devices

List all discovered devices.

**Request**

```bash
curl http://localhost:8000/api/devices
```

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | all | Filter by status: `up`, `down`, `unknown`, `all` |
| limit | integer | 100 | Maximum number of results |
| offset | integer | 0 | Pagination offset |

**Example with filters**

```bash
curl "http://localhost:8000/api/devices?status=up&limit=10"
```

**Response** `200 OK`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "ip": "192.168.1.10",
    "mac": "00:11:22:33:44:55",
    "hostname": "router.local",
    "vendor": "Cisco",
    "device_type": "Router",
    "status": "up",
    "first_seen": "2024-01-15T08:00:00Z",
    "last_seen": "2024-01-15T10:29:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "ip": "192.168.1.20",
    "mac": "AA:BB:CC:DD:EE:FF",
    "hostname": "switch.local",
    "vendor": "HP",
    "device_type": "Switch",
    "status": "up",
    "first_seen": "2024-01-15T08:05:00Z",
    "last_seen": "2024-01-15T10:28:30Z"
  }
]
```

#### GET /api/devices/{device_id}

Get details of a specific device.

**Request**

```bash
curl http://localhost:8000/api/devices/550e8400-e29b-41d4-a716-446655440000
```

**Response** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "ip": "192.168.1.10",
  "mac": "00:11:22:33:44:55",
  "hostname": "router.local",
  "vendor": "Cisco",
  "device_type": "Router",
  "status": "up",
  "first_seen": "2024-01-15T08:00:00Z",
  "last_seen": "2024-01-15T10:29:00Z"
}
```

**Error Response** `404 Not Found`

```json
{
  "detail": "Device not found"
}
```

#### POST /api/devices/discover

Trigger network discovery.

**Description**: Initiates and completes a network scan synchronously to discover devices. Returns discovered devices immediately.

**Request**

```bash
curl -X POST http://localhost:8000/api/devices/discover
```

**Request Body** (optional)

```json
{
  "cidr": "192.168.1.0/24",
  "interface": "eth0",
  "arp_timeout": 3.0,
  "ping_timeout": 1.0,
  "persist": true,
  "identify": true
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| cidr | string | No | From config | Network CIDR notation |
| interface | string | No | Auto-detect | Network interface name |
| arp_timeout | float | No | 3.0 | ARP scan timeout in seconds |
| ping_timeout | float | No | 1.0 | Ping timeout in seconds |
| persist | boolean | No | true | Save discovered devices to database |
| identify | boolean | No | true | Identify devices via OUI and SNMP |

**Response** `200 OK`

```json
{
  "count": 5,
  "devices": [
    {
      "ip": "192.168.1.10",
      "mac": "aa:bb:cc:dd:ee:ff",
      "hostname": "router.local",
      "vendor": "Cisco Systems",
      "source": "arp"
    },
    {
      "ip": "192.168.1.11",
      "mac": "11:22:33:44:55:66",
      "hostname": "switch.local",
      "vendor": "HP Inc.",
      "source": "mdns"
    }
  ],
  "persisted": true,
  "identified": true
}
```

**Note**: While discovery is synchronous, device status changes and metrics are still broadcast via WebSocket to connected clients.

#### DELETE /api/devices/{device_id}

Delete a device from inventory.

**Request**

```bash
curl -X DELETE http://localhost:8000/api/devices/550e8400-e29b-41d4-a716-446655440000
```

**Response** `204 No Content`

**Error Response** `404 Not Found`

```json
{
  "detail": "Device not found"
}
```

---

### Metrics

#### GET /api/metrics/{device_id}

Get historical metrics for a device.

**Request**

```bash
curl "http://localhost:8000/api/metrics/550e8400-e29b-41d4-a716-446655440000?hours=24"
```

**Query Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| hours | integer | 24 | Time range in hours |
| metric | string | latency | Metric type: `latency`, `packet_loss`, `all` |
| aggregate | string | none | Aggregation: `none`, `avg`, `min`, `max` |

**Response** `200 OK`

```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "metric": "latency",
  "time_range": {
    "start": "2024-01-14T10:30:00Z",
    "end": "2024-01-15T10:30:00Z"
  },
  "data_points": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "latency_ms": 12.5,
      "packet_loss": 0.0
    },
    {
      "timestamp": "2024-01-15T10:00:30Z",
      "latency_ms": 15.2,
      "packet_loss": 0.0
    }
  ]
}
```

**Error Response** `404 Not Found`

```json
{
  "detail": "Device not found"
}
```

#### GET /api/metrics/summary

Get metrics summary for all devices.

**Request**

```bash
curl http://localhost:8000/api/metrics/summary
```

**Response** `200 OK`

```json
{
  "total_devices": 10,
  "devices_up": 8,
  "devices_down": 2,
  "avg_latency_ms": 18.5,
  "max_latency_ms": 150.0,
  "total_packet_loss": 0.05
}
```

---

### WebSocket

#### WS /ws/stream

Real-time event streaming.

**Connection**

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream');

ws.onopen = () => {
  console.log('Connected to event stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data);
};
```

**Python Client**

```python
import asyncio
import websockets
import json

async def listen():
    uri = "ws://localhost:8000/ws/stream"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print(f"Event: {data}")

asyncio.run(listen())
```

**Message Types**

##### hello

Sent immediately upon connection.

```json
{
  "type": "hello",
  "ts": 1705317000
}
```

##### device_discovered

New device found during discovery.

```json
{
  "type": "device_discovered",
  "ts": 1705317000,
  "device": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "ip": "192.168.1.10",
    "mac": "00:11:22:33:44:55",
    "hostname": "router.local",
    "vendor": "Cisco",
    "device_type": "Router",
    "status": "up",
    "first_seen": "2024-01-15T10:30:00Z",
    "last_seen": "2024-01-15T10:30:00Z"
  }
}
```

##### device_up

Device status changed to online.

```json
{
  "type": "device_up",
  "ts": 1705317000,
  "device_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

##### device_down

Device status changed to offline.

```json
{
  "type": "device_down",
  "ts": 1705317000,
  "device_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

##### latency

Periodic latency measurement.

```json
{
  "type": "latency",
  "ts": 1705317000,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "ms": 12.5,
  "loss": 0.0
}
```

---

## Code Examples

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# List devices
response = requests.get(f"{BASE_URL}/api/devices")
devices = response.json()

for device in devices:
    print(f"{device['ip']} - {device['hostname']} ({device['status']})")

# Trigger discovery
response = requests.post(f"{BASE_URL}/api/devices/discover")
print(response.json())

# Get device metrics
device_id = devices[0]['id']
response = requests.get(
    f"{BASE_URL}/api/metrics/{device_id}",
    params={"hours": 24}
)
metrics = response.json()
print(f"Latency data points: {len(metrics['data_points'])}")
```

### Python (httpx with async)

```python
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Health check
        r = await client.get("http://localhost:8000/health")
        print(r.json())

        # List devices
        r = await client.get("http://localhost:8000/api/devices")
        devices = r.json()

        # Get metrics for each device
        tasks = [
            client.get(f"http://localhost:8000/api/metrics/{d['id']}")
            for d in devices
        ]
        responses = await asyncio.gather(*tasks)

        for response in responses:
            print(response.json())

asyncio.run(main())
```

### JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000';

// Health check
fetch(`${BASE_URL}/health`)
  .then(response => response.json())
  .then(data => console.log(data));

// List devices
fetch(`${BASE_URL}/api/devices?status=up`)
  .then(response => response.json())
  .then(devices => {
    devices.forEach(device => {
      console.log(`${device.ip} - ${device.hostname}`);
    });
  });

// Trigger discovery
fetch(`${BASE_URL}/api/devices/discover`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    network: '192.168.1.0/24'
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# List devices (formatted)
curl http://localhost:8000/api/devices | jq '.'

# Filter devices by status
curl "http://localhost:8000/api/devices?status=up"

# Get specific device
curl http://localhost:8000/api/devices/{device_id}

# Trigger discovery
curl -X POST http://localhost:8000/api/devices/discover

# Custom network for discovery
curl -X POST http://localhost:8000/api/devices/discover \
  -H "Content-Type: application/json" \
  -d '{"cidr": "10.0.0.0/24", "persist": true}'

# Get metrics
curl "http://localhost:8000/api/metrics/{device_id}?hours=24"

# Delete device
curl -X DELETE http://localhost:8000/api/devices/{device_id}
```

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:

- **JSON**: <http://localhost:8000/openapi.json>
- **Interactive Docs (Swagger UI)**: <http://localhost:8000/docs>
- **Alternative Docs (ReDoc)**: <http://localhost:8000/redoc>

Download OpenAPI spec:

```bash
curl http://localhost:8000/openapi.json > openapi.json
```

## Rate Limiting

Currently, no rate limiting is implemented. All endpoints accept unlimited requests.

**Future**: Rate limiting will be added with headers:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705320600
```

## Pagination

Endpoints returning lists support pagination:

```bash
# First page (default)
curl "http://localhost:8000/api/devices?limit=10&offset=0"

# Second page
curl "http://localhost:8000/api/devices?limit=10&offset=10"
```

## Filtering

Devices can be filtered by status:

```bash
# Only online devices
curl "http://localhost:8000/api/devices?status=up"

# Only offline devices
curl "http://localhost:8000/api/devices?status=down"

# All devices (default)
curl "http://localhost:8000/api/devices?status=all"
```

## CORS

CORS is enabled for all origins in development. In production, restrict origins:

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Versioning

Current API version: **v1** (implicit, no version prefix)

Future versions will use URL versioning:

```
http://localhost:8000/api/v2/devices
```

## Next Steps

- [WebSocket Protocol](../ai/11-websocket-protocol.json) - Detailed WebSocket message schemas
- [Configuration](03-configuration.md) - API server configuration
- [Development](10-development.md) - Set up development environment
- [Security](42-security.md) - API security best practices
