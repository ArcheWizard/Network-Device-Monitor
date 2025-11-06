# Database Management

Managing SQLite and InfluxDB databases for the Network Device Monitor.

## Overview

The application uses two databases:

- **SQLite** - Device inventory (persistent state)
- **InfluxDB** - Time-series metrics (performance data)

## SQLite Database

### Location

```bash
backend/data/devices.db
```

### Schema

**devices table:**
```sql
CREATE TABLE devices (
    id TEXT PRIMARY KEY,           -- MAC address
    ip TEXT NOT NULL,              -- IP address
    mac TEXT NOT NULL,             -- MAC address (duplicate of id)
    hostname TEXT,                 -- DNS hostname
    vendor TEXT,                   -- OUI vendor
    device_type TEXT,              -- Device type (future)
    status TEXT DEFAULT 'unknown', -- up/down/unknown
    first_seen INTEGER NOT NULL,   -- Unix timestamp
    last_seen INTEGER NOT NULL,    -- Unix timestamp
    snmp_sys_name TEXT,            -- SNMP sysName
    snmp_sys_descr TEXT            -- SNMP sysDescr
);
```

### Accessing SQLite

**Using SQLite CLI:**
```bash
cd backend
sqlite3 data/devices.db

# List tables
.tables

# Show schema
.schema devices

# Query devices
SELECT * FROM devices;

# Exit
.quit
```

**Using Python:**
```python
import sqlite3

conn = sqlite3.connect('backend/data/devices.db')
cursor = conn.cursor()

# Query all devices
cursor.execute('SELECT * FROM devices')
for row in cursor.fetchall():
    print(row)

conn.close()
```

### Backup SQLite

```bash
# Simple copy
cp backend/data/devices.db backend/data/devices.db.backup

# Using SQLite backup command
sqlite3 backend/data/devices.db ".backup 'backup/devices-$(date +%Y%m%d).db'"

# Automated daily backup
cat > backup_sqlite.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="./backups"
mkdir -p $BACKUP_DIR
sqlite3 backend/data/devices.db ".backup '$BACKUP_DIR/devices-$(date +%Y%m%d-%H%M%S).db'"
find $BACKUP_DIR -name "devices-*.db" -mtime +30 -delete  # Keep 30 days
EOF
chmod +x backup_sqlite.sh
```

### Restore SQLite

```bash
# Stop the application first
# Then restore from backup
cp backup/devices-20240101.db backend/data/devices.db

# Or use SQLite restore
sqlite3 backend/data/devices.db ".restore 'backup/devices-20240101.db'"
```

### Maintenance

**Vacuum (reclaim space):**
```bash
sqlite3 backend/data/devices.db "VACUUM;"
```

**Integrity check:**
```bash
sqlite3 backend/data/devices.db "PRAGMA integrity_check;"
```

**Optimize:**
```bash
sqlite3 backend/data/devices.db "PRAGMA optimize;"
```

## InfluxDB Database

### Configuration

```bash
# Environment variables
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=your-token
INFLUX_ORG=myorg
INFLUX_BUCKET=network_metrics
```

### Schema

**Measurement: latency**

**Tags:**
- `device_id` - Device identifier (MAC address)
- `ip` - Device IP address

**Fields:**
- `ms` (float) - Average latency in milliseconds
- `loss` (float) - Packet loss ratio (0.0 to 1.0)
- `min_ms` (float) - Minimum latency
- `max_ms` (float) - Maximum latency

**Timestamp:** Automatic (measurement time)

### Accessing InfluxDB

**Using InfluxDB UI:**

1. Open http://localhost:8086
2. Login with credentials
3. Navigate to Data Explorer
4. Select bucket: `network_metrics`
5. Query data

**Using Flux:**
```flux
from(bucket: "network_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "latency")
  |> filter(fn: (r) => r["device_id"] == "aa:bb:cc:dd:ee:ff")
```

**Using InfluxDB CLI:**
```bash
influx query '
  from(bucket: "network_metrics")
    |> range(start: -1h)
    |> filter(fn: (r) => r["_measurement"] == "latency")
' --org myorg --token your-token
```

**Using Python:**
```python
from influxdb_client import InfluxDBClient

client = InfluxDBClient(
    url="http://localhost:8086",
    token="your-token",
    org="myorg"
)

query_api = client.query_api()

query = '''
from(bucket: "network_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "latency")
'''

tables = query_api.query(query)
for table in tables:
    for record in table.records:
        print(f"{record.get_time()}: {record.get_value()}")

client.close()
```

### Backup InfluxDB

**Using InfluxDB CLI:**
```bash
# Backup all data
influx backup /path/to/backup \
  --host http://localhost:8086 \
  --token your-token

# Backup specific bucket
influx backup /path/to/backup \
  --host http://localhost:8086 \
  --token your-token \
  --bucket network_metrics
```

**Automated backup script:**
```bash
#!/bin/bash
BACKUP_DIR="./backups/influxdb"
mkdir -p $BACKUP_DIR

influx backup "$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S)" \
  --host http://localhost:8086 \
  --token your-token \
  --bucket network_metrics

# Keep only last 7 backups
ls -t $BACKUP_DIR | tail -n +8 | xargs -I {} rm -rf "$BACKUP_DIR/{}"
```

### Restore InfluxDB

```bash
# Stop writing to InfluxDB first
# Then restore from backup
influx restore /path/to/backup \
  --host http://localhost:8086 \
  --token your-token \
  --bucket network_metrics
```

### Retention Policies

Configure data retention in InfluxDB:

**Using InfluxDB UI:**
1. Go to Settings > Buckets
2. Select `network_metrics`
3. Set retention period (e.g., 30 days, 90 days, infinite)

**Using InfluxDB CLI:**
```bash
# Set 30-day retention
influx bucket update \
  --name network_metrics \
  --retention 720h \
  --org myorg \
  --token your-token

# Infinite retention
influx bucket update \
  --name network_metrics \
  --retention 0 \
  --org myorg \
  --token your-token
```

### Downsampling

Reduce data resolution for older data to save space:

**Create task:**
```flux
option task = {name: "downsample-latency", every: 1h}

from(bucket: "network_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "latency")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
  |> to(bucket: "network_metrics_downsampled")
```

### Maintenance

**Check disk usage:**
```bash
influx server-config --host http://localhost:8086 --token your-token
```

**Delete old data:**
```bash
influx delete \
  --bucket network_metrics \
  --start 2024-01-01T00:00:00Z \
  --stop 2024-02-01T00:00:00Z \
  --predicate '_measurement="latency"' \
  --org myorg \
  --token your-token
```

**Compact data:**
```bash
# Automatic in InfluxDB 2.x
# No manual compaction needed
```

## Data Migration

### Export SQLite to CSV

```bash
sqlite3 backend/data/devices.db <<EOF
.headers on
.mode csv
.output devices.csv
SELECT * FROM devices;
.quit
EOF
```

### Import CSV to SQLite

```python
import sqlite3
import csv

conn = sqlite3.connect('backend/data/devices.db')
cursor = conn.cursor()

with open('devices.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cursor.execute('''
            INSERT OR REPLACE INTO devices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['id'], row['ip'], row['mac'], row['hostname'],
            row['vendor'], row['device_type'], row['status'],
            row['first_seen'], row['last_seen'],
            row['snmp_sys_name'], row['snmp_sys_descr']
        ))

conn.commit()
conn.close()
```

### Export InfluxDB to CSV

```bash
influx query '
from(bucket: "network_metrics")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "latency")
' --org myorg --token your-token --raw > metrics.csv
```

### Import CSV to InfluxDB

```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import csv
from datetime import datetime

client = InfluxDBClient(
    url="http://localhost:8086",
    token="your-token",
    org="myorg"
)

write_api = client.write_api(write_options=SYNCHRONOUS)

with open('metrics.csv', 'r') as f:
    reader = csv.DictReader(f)
    points = []
    for row in reader:
        point = Point("latency") \
            .tag("device_id", row['device_id']) \
            .field("ms", float(row['ms'])) \
            .field("loss", float(row['loss'])) \
            .time(datetime.fromisoformat(row['timestamp']))
        points.append(point)

        if len(points) >= 1000:  # Batch writes
            write_api.write(bucket="network_metrics", record=points)
            points = []

    if points:
        write_api.write(bucket="network_metrics", record=points)

client.close()
```

## Monitoring Database Health

### SQLite Health Check

```bash
# Check file size
du -h backend/data/devices.db

# Check integrity
sqlite3 backend/data/devices.db "PRAGMA integrity_check;"

# Check device count
sqlite3 backend/data/devices.db "SELECT COUNT(*) FROM devices;"
```

### InfluxDB Health Check

```bash
# Check health endpoint
curl http://localhost:8086/health

# Check metrics
curl http://localhost:8086/metrics

# Check bucket stats
influx bucket list --org myorg --token your-token
```

## Best Practices

1. **Regular backups** - Automate daily backups
2. **Monitor disk usage** - Set up alerts for low disk space
3. **Set retention policies** - Don't keep data forever
4. **Test restores** - Verify backups work
5. **Downsampling** - Reduce resolution of old data
6. **Index optimization** - Vacuum SQLite regularly
7. **Security** - Restrict database file permissions

## Related Documentation

- [Configuration](03-configuration.md) - Database configuration
- [Deployment](30-deployment.md) - Production setup
- [Troubleshooting](31-troubleshooting.md) - Database issues
