# Database

## SQLite (inventory)

Schema used by the inventory repository (`app/storage/sqlite.py`):

```sql
CREATE TABLE IF NOT EXISTS devices (
  id TEXT PRIMARY KEY,
  ip TEXT,
  mac TEXT,
  hostname TEXT,
  vendor TEXT,
  device_type TEXT,
  status TEXT,
  first_seen INTEGER,
  last_seen INTEGER,
  tags TEXT
);
```

Notes:

- `status` is one of: `up`, `down`, `unknown`.
- `tags` is a JSON-encoded object stored as TEXT.
- `first_seen`/`last_seen` are Unix timestamps (seconds).

## InfluxDB (metrics)

- Measurement: latency
  - tags: device_id
  - fields: ms (float), loss (float)
- Measurement: bandwidth
  - tags: device_id, ifIndex
  - fields: in_bps (float), out_bps (float)
  - Note: compute from SNMP counters with deltas and interval

Retention: 30d default, downsample later.
