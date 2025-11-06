# Monitoring Feature

Device monitoring provides continuous health checks and metrics collection for discovered network devices.

## Overview

The monitoring system tracks device health using ICMP ping and collects performance metrics:

- **Latency** - Round-trip time in milliseconds
- **Packet Loss** - Percentage of lost packets
- **Device Status** - Up/down/unknown
- **Availability** - Historical uptime percentage

## Quick Start

Monitoring runs automatically after discovery. Metrics are stored in InfluxDB and accessible via API:

```bash
# Get latency metrics for a device
curl "http://localhost:8000/api/metrics/latency?device_id=192.168.1.1&start=-1h&limit=100"
```

## How It Works

1. **Scheduled Monitoring** - APScheduler runs monitoring jobs at regular intervals
2. **Ping Devices** - System `ping` command checks each device
3. **Collect Metrics** - Parse ping output for latency and packet loss
4. **Store in InfluxDB** - Write time-series metrics
5. **Update Status** - Update device status in SQLite
6. **WebSocket Broadcast** - Send real-time updates to connected clients

## Monitoring Configuration

```bash
# Monitoring interval (in scheduler configuration)
MONITORING_INTERVAL=60    # Seconds between monitoring cycles

# Alert thresholds
ALERT_LATENCY_MS=200.0    # Alert if latency > 200ms
ALERT_PACKET_LOSS=0.5     # Alert if packet loss > 50%
```

## Metrics

### Latency

**Measurement:** `latency`
**Tags:** `device_id`, `ip`
**Fields:**
- `ms` - Average latency in milliseconds
- `loss` - Packet loss ratio (0.0 to 1.0)
- `min_ms` - Minimum latency
- `max_ms` - Maximum latency

### Device Status

- **up** - Device responding to ping
- **down** - Device not responding
- **unknown** - Not yet monitored

## Viewing Metrics

### Via API

```bash
# Last hour of metrics
curl "http://localhost:8000/api/metrics/latency?device_id=192.168.1.1&start=-1h"

# Last 24 hours
curl "http://localhost:8000/api/metrics/latency?device_id=192.168.1.1&start=-24h&limit=1000"
```

### Via InfluxDB UI

1. Open http://localhost:8086
2. Navigate to Data Explorer
3. Query the `network_metrics` bucket:

```flux
from(bucket: "network_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "latency")
  |> filter(fn: (r) => r["device_id"] == "192.168.1.1")
```

## Alerting

Configure alert thresholds in `.env`:

```bash
ALERT_LATENCY_MS=200.0      # Latency threshold in ms
ALERT_PACKET_LOSS=0.5       # Packet loss threshold (0.0-1.0)
```

When thresholds are exceeded, the system can trigger notifications (future feature).

## Performance Considerations

- **Monitoring interval:** 60 seconds is typical; adjust based on needs
- **Device count:** Up to 100 devices can be monitored comfortably
- **Large deployments:** Consider batching or longer intervals

## Troubleshooting

### No Metrics Appearing

**Check InfluxDB connection:**
```bash
# Verify env variables
echo $INFLUX_URL
echo $INFLUX_TOKEN

# Test connection
curl $INFLUX_URL/health
```

### Metrics Not Updating

**Check scheduler status:**
```bash
# Look for scheduler logs in backend output
# Should see "Monitoring job started" messages
```

### High Latency Values

- Verify network path to devices
- Check for network congestion
- Consider adjusting `ALERT_LATENCY_MS` threshold

## Best Practices

1. **Set realistic thresholds** - Based on your network baseline
2. **Monitor monitoring** - Track monitoring job execution time
3. **Archive old data** - Configure InfluxDB retention policies
4. **Optimize interval** - Balance freshness vs load

## Related Features

- [Discovery](20-discovery.md) - Device discovery
- [WebSocket](23-websocket.md) - Real-time metric streaming
- [Database Management](32-database.md) - InfluxDB operations
