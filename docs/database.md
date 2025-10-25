# Database

## SQLite (inventory)

Tables:

- devices(id TEXT PK, ip TEXT, mac TEXT, hostname TEXT, vendor TEXT, device_type TEXT, first_seen INTEGER, last_seen INTEGER, tags TEXT JSON)

## InfluxDB (metrics)

- Measurement: latency
  - tags: device_id
  - fields: ms (float), loss (float)
- Measurement: bandwidth
  - tags: device_id, ifIndex
  - fields: in_bps (float), out_bps (float)
  - Note: compute from SNMP counters with deltas and interval

Retention: 30d default, downsample later.
