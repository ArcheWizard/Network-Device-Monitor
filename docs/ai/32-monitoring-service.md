# Monitoring Service Interface

## Overview

The Monitoring Service provides health check and metrics collection capabilities for discovered network devices using ICMP ping.

**Module:** `app.services.monitoring`
**Location:** `backend/app/services/monitoring.py`

## Public Functions

### `async def ping_device(ip, count, timeout) -> Dict[str, Any]`

Ping a device and collect latency and packet loss metrics.

**Parameters:**

- `ip` (str): IP address to ping
- `count` (int): Number of ping packets to send. Default: 4
- `timeout` (float): Timeout in seconds per ping. Default: 2.0

**Returns:** Dictionary with monitoring metrics:

- `ip` (str): IP address pinged
- `status` (str): Device status ("up", "down", "error")
- `latency_avg` (Optional[float]): Average latency in milliseconds
- `latency_min` (Optional[float]): Minimum latency in milliseconds
- `latency_max` (Optional[float]): Maximum latency in milliseconds
- `packet_loss` (float): Packet loss percentage (0.0 to 100.0)

**Example:**

```python
from app.services import monitoring

result = await monitoring.ping_device(
    ip="192.168.1.1",
    count=4,
    timeout=2.0
)

print(f"Status: {result['status']}")
print(f"Avg Latency: {result['latency_avg']}ms")
print(f"Packet Loss: {result['packet_loss']}%")
```

**Implementation Details:**

- Uses system `ping` command via subprocess
- Parses output to extract latency statistics
- Handles unreachable hosts gracefully
- Non-blocking async execution

---

### `async def tick_all()`

Monitor all devices in inventory (scheduled task placeholder).

**Parameters:** None

**Returns:** None

**Notes:**

- Currently a placeholder for scheduler integration
- Will be called periodically by APScheduler
- Intended to iterate through all devices and collect metrics

**Future Implementation:**

```python
async def tick_all(app_state):
    repo = app_state.inventory_repo
    influx = app_state.influx_writer

    devices = await repo.list_devices()
    for device in devices:
        if device.get('ip'):
            result = await ping_device(device['ip'])

            # Update device status in repo
            await repo.upsert_device({
                'id': device['id'],
                'status': result['status'],
                'last_seen': int(time.time()) if result['status'] == 'up' else None
            })

            # Write metrics to InfluxDB
            if influx and result['latency_avg'] is not None:
                await influx.write_metric(
                    measurement='latency',
                    tags={'device_id': device['id'], 'ip': device['ip']},
                    fields={
                        'ms': result['latency_avg'],
                        'loss': result['packet_loss'] / 100.0,
                        'min_ms': result['latency_min'],
                        'max_ms': result['latency_max']
                    }
                )
```

---

## Integration Example

```python
from app.services import monitoring
from app.storage.influx import get_writer
import time

async def monitor_devices(devices: list):
    influx = get_writer()

    for device in devices:
        ip = device.get('ip')
        if not ip:
            continue

        # Ping device
        result = await monitoring.ping_device(ip, count=4, timeout=2.0)

        # Store metrics in InfluxDB
        if influx and result['latency_avg'] is not None:
            await influx.write_metric(
                measurement='latency',
                tags={
                    'device_id': device['id'],
                    'ip': ip
                },
                fields={
                    'ms': result['latency_avg'],
                    'loss': result['packet_loss'] / 100.0,
                    'min_ms': result['latency_min'],
                    'max_ms': result['latency_max']
                },
                timestamp=None  # Use current time
            )

        # Broadcast status change via WebSocket
        if result['status'] == 'down':
            # Send device_down message
            pass
        elif result['status'] == 'up':
            # Send latency message
            pass

    return results
```

---

## Scheduled Monitoring

Monitoring is typically triggered periodically by APScheduler:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services import monitoring

scheduler = AsyncIOScheduler()

async def monitoring_job(app):
    # Get devices from repo
    repo = app.state.inventory_repo
    devices = await repo.list_devices()

    # Monitor each device
    for device in devices:
        if device.get('ip'):
            result = await monitoring.ping_device(device['ip'])
            # Process result...

# Schedule every 60 seconds
scheduler.add_job(
    monitoring_job,
    'interval',
    seconds=60,
    args=[app]
)
scheduler.start()
```

---

## Metrics Storage

Monitoring metrics are stored in InfluxDB:

**Measurement:** `latency`
**Tags:** `device_id`, `ip`
**Fields:** `ms`, `loss`, `min_ms`, `max_ms`

**Query Example:**

```python
from app.storage.influx import get_writer

influx = get_writer()
points = await influx.query_metrics(
    measurement='latency',
    device_id='192.168.1.1',
    start='-1h',
    limit=100
)

for point in points:
    print(f"{point['time']}: {point['value']}ms")
```

---

## Alerting Integration

The monitoring service can trigger alerts based on thresholds:

```python
from app.config import settings

async def check_alerts(result):
    if result['latency_avg'] and result['latency_avg'] > settings.ALERT_LATENCY_MS:
        await send_alert(f"High latency on {result['ip']}: {result['latency_avg']}ms")

    if result['packet_loss'] > settings.ALERT_PACKET_LOSS * 100:
        await send_alert(f"High packet loss on {result['ip']}: {result['packet_loss']}%")
```

**Configuration:**

```bash
ALERT_LATENCY_MS=200.0      # Alert if latency > 200ms
ALERT_PACKET_LOSS=0.5       # Alert if packet loss > 50%
```

---

## Error Handling

The monitoring service handles errors gracefully:

```python
result = await monitoring.ping_device("192.168.1.100")

# If device is down:
# {
#     'ip': '192.168.1.100',
#     'status': 'down',
#     'latency_avg': None,
#     'latency_min': None,
#     'latency_max': None,
#     'packet_loss': 100.0
# }

# If ping command fails:
# {
#     'ip': '192.168.1.100',
#     'status': 'error',
#     'latency_avg': None,
#     'latency_min': None,
#     'latency_max': None,
#     'packet_loss': 100.0
# }
```

---

## Performance Considerations

- **Single device ping:** ~1-2 seconds (depends on timeout)
- **Parallel monitoring:** Use `asyncio.gather()` for multiple devices
- **Network size:** For 100+ devices, consider batching or longer intervals

**Optimized Batch Monitoring:**

```python
import asyncio

async def monitor_batch(devices, batch_size=50):
    for i in range(0, len(devices), batch_size):
        batch = devices[i:i+batch_size]
        tasks = [
            monitoring.ping_device(d['ip'])
            for d in batch if d.get('ip')
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Process results...
        await asyncio.sleep(1)  # Brief pause between batches
```

---

## Testing

```python
# Run monitoring service tests
pytest backend/tests/test_monitoring.py
```

---

## Dependencies

- System utility: `ping` command
- Python standard library: `asyncio`, `subprocess`, `re`

---

## Configuration

Monitoring behavior can be configured via environment variables:

```python
# Example custom configuration
MONITORING_INTERVAL=60       # Seconds between monitoring cycles
MONITORING_PING_COUNT=4      # Number of ping packets
MONITORING_PING_TIMEOUT=2.0  # Timeout per ping
```

See `backend/app/config.py` and `backend/app/scheduler/jobs.py` for integration.
