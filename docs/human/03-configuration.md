# Configuration Guide

Comprehensive configuration reference for Network Device Monitor.

## Table of Contents

- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Network Settings](#network-settings)
- [SNMP Configuration](#snmp-configuration)
- [Storage Configuration](#storage-configuration)
- [Monitoring Settings](#monitoring-settings)
- [Alert Configuration](#alert-configuration)
- [Performance Tuning](#performance-tuning)
- [Security Settings](#security-settings)

## Configuration Files

### Primary Configuration

Configuration is loaded in this order (later overrides earlier):

1. **Default values** in `backend/app/config.py`
2. **Environment variables** from `.env` file
3. **Environment variables** from shell

### Location

```
backend/
  .env              # Primary configuration file (git-ignored)
  .env.example      # Template with defaults
  app/
    config.py       # Configuration loader
```

### Example .env File

```env
# Network Discovery
NETWORK_CIDR=192.168.1.0/24
INTERFACE=eth0

# SNMP Settings
SNMP_COMMUNITY=public
SNMP_PORT=161
SNMP_TIMEOUT=1.0

# InfluxDB (optional)
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=your-token-here
INFLUX_ORG=your-org
INFLUX_BUCKET=network_metrics

# Monitoring
MONITOR_INTERVAL=30
PING_COUNT=4

# Alerts
ALERT_LATENCY_MS=200
ALERT_PACKET_LOSS=0.5

# Application
PORT=8000
LOG_LEVEL=INFO
```

## Environment Variables

### Network Settings

#### `NETWORK_CIDR`

Target network for device discovery.

- **Type**: String (CIDR notation)
- **Default**: `"192.168.1.0/24"`
- **Examples**:
  - `"10.0.0.0/8"` - Large network
  - `"192.168.1.0/24"` - Standard home network
  - `"172.16.0.0/16"` - Medium enterprise network

```bash
NETWORK_CIDR=192.168.1.0/24
```

#### `INTERFACE`

Network interface to use for discovery.

- **Type**: String or null
- **Default**: `null` (auto-detect)
- **Examples**: `eth0`, `wlan0`, `en0`

```bash
# Auto-detect (recommended)
INTERFACE=

# Specify interface
INTERFACE=eth0

# List available interfaces
ip addr show  # Linux
ifconfig      # macOS
```

### SNMP Configuration

#### `SNMP_COMMUNITY`

SNMP v2c community string for device identification.

- **Type**: String
- **Default**: `"public"`
- **Security**: Use read-only community strings

```bash
SNMP_COMMUNITY=public
```

#### `SNMP_PORT`

UDP port for SNMP queries.

- **Type**: Integer
- **Default**: `161`
- **Range**: 1-65535

```bash
SNMP_PORT=161
```

#### `SNMP_TIMEOUT`

Timeout for SNMP queries in seconds.

- **Type**: Float
- **Default**: `1.0`
- **Range**: 0.1-30.0

```bash
# Fast network
SNMP_TIMEOUT=0.5

# Slow/unreliable network
SNMP_TIMEOUT=3.0
```

### Storage Configuration

#### SQLite (Built-in)

SQLite is used by default, no configuration needed.

- **Path**: `backend/data/devices.db`
- **Auto-created**: Yes
- **Migrations**: Automatic

#### InfluxDB (Optional)

Time-series database for historical metrics.

##### `INFLUX_URL`

InfluxDB server URL.

- **Type**: String (URL) or null
- **Default**: `null` (disabled)

```bash
INFLUX_URL=http://localhost:8086
```

##### `INFLUX_TOKEN`

Authentication token for InfluxDB.

- **Type**: String or null
- **Default**: `null`
- **Generate**: In InfluxDB UI under "API Tokens"

```bash
INFLUX_TOKEN=your-generated-token-here
```

##### `INFLUX_ORG`

InfluxDB organization name.

- **Type**: String or null
- **Default**: `null`

```bash
INFLUX_ORG=my-organization
```

##### `INFLUX_BUCKET`

Bucket name for storing metrics.

- **Type**: String or null
- **Default**: `null`

```bash
INFLUX_BUCKET=network_metrics
```

**Note**: If any InfluxDB setting is missing, metrics will only be stored in SQLite.

### Monitoring Settings

#### `MONITOR_INTERVAL`

Seconds between monitoring checks.

- **Type**: Integer
- **Default**: `30`
- **Range**: 5-3600

```bash
# High-frequency monitoring (more load)
MONITOR_INTERVAL=10

# Standard monitoring
MONITOR_INTERVAL=30

# Low-frequency monitoring (less load)
MONITOR_INTERVAL=300
```

#### `PING_COUNT`

Number of ICMP echo requests per check.

- **Type**: Integer
- **Default**: `4`
- **Range**: 1-10

```bash
# Quick checks
PING_COUNT=2

# Accurate measurements
PING_COUNT=10
```

### Alert Configuration

#### `ALERT_LATENCY_MS`

Latency threshold in milliseconds.

- **Type**: Float
- **Default**: `200.0`
- **Unit**: Milliseconds

```bash
# Sensitive threshold
ALERT_LATENCY_MS=100

# Standard threshold
ALERT_LATENCY_MS=200

# Relaxed threshold
ALERT_LATENCY_MS=500
```

#### `ALERT_PACKET_LOSS`

Packet loss threshold (ratio).

- **Type**: Float
- **Default**: `0.5` (50%)
- **Range**: 0.0-1.0

```bash
# Trigger on any packet loss
ALERT_PACKET_LOSS=0.0

# Trigger on 25% loss
ALERT_PACKET_LOSS=0.25

# Trigger on 50% loss
ALERT_PACKET_LOSS=0.5
```

### Application Settings

#### `PORT`

HTTP server port.

- **Type**: Integer
- **Default**: `8000`
- **Range**: 1024-65535 (avoid privileged ports)

```bash
PORT=8000
```

#### `LOG_LEVEL`

Logging verbosity.

- **Type**: String
- **Default**: `"INFO"`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

```bash
# Development - verbose
LOG_LEVEL=DEBUG

# Production - standard
LOG_LEVEL=INFO

# Production - minimal
LOG_LEVEL=WARNING
```

## Performance Tuning

### Discovery Performance

```bash
# Fast discovery (small networks)
NETWORK_CIDR=192.168.1.0/24
SNMP_TIMEOUT=0.5

# Slow/large networks
NETWORK_CIDR=10.0.0.0/16
SNMP_TIMEOUT=2.0
# Consider chunking discovery manually
```

### Monitoring Performance

```bash
# High-frequency monitoring
MONITOR_INTERVAL=15
PING_COUNT=2

# Battery-friendly monitoring
MONITOR_INTERVAL=120
PING_COUNT=3
```

### Database Performance

**SQLite** (automatic optimization):
- Indexes created automatically
- WAL mode enabled for concurrency
- Auto-vacuum configured

**InfluxDB** (external tuning):
- Configure retention policies in InfluxDB
- Use downsampling for long-term storage
- Adjust write batch size if needed

## Security Settings

### Network Security

```bash
# Use specific interface to limit exposure
INTERFACE=eth0

# Restrict discovery to known subnet
NETWORK_CIDR=192.168.1.0/28  # Only 14 IPs
```

### SNMP Security

```bash
# Use read-only community
SNMP_COMMUNITY=public-readonly

# For SNMP v3 (future enhancement):
# SNMP_VERSION=3
# SNMP_USER=monitor
# SNMP_AUTH_PROTOCOL=SHA
# SNMP_PRIV_PROTOCOL=AES
```

### API Security

```bash
# Bind to localhost only (add to config.py)
# host="127.0.0.1"

# Enable CORS restrictions (configured in main.py)
# CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Credentials Management

**Never commit credentials to git**:

```bash
# Add to .gitignore
echo "backend/.env" >> .gitignore

# Use environment-specific files
.env.development
.env.production
```

**Use secrets management in production**:

```bash
# Load from secrets manager
INFLUX_TOKEN=$(aws secretsmanager get-secret-value --secret-id influx-token)
```

## Configuration Examples

### Home Network

```env
NETWORK_CIDR=192.168.1.0/24
INTERFACE=
SNMP_COMMUNITY=public
MONITOR_INTERVAL=60
PING_COUNT=3
ALERT_LATENCY_MS=300
LOG_LEVEL=INFO
```

### Enterprise Network

```env
NETWORK_CIDR=10.100.0.0/16
INTERFACE=eth0
SNMP_COMMUNITY=enterprise-readonly
SNMP_TIMEOUT=2.0
INFLUX_URL=http://influxdb.internal:8086
INFLUX_TOKEN=${INFLUX_TOKEN}  # From environment
INFLUX_ORG=network-ops
INFLUX_BUCKET=device_monitoring
MONITOR_INTERVAL=30
ALERT_LATENCY_MS=100
ALERT_PACKET_LOSS=0.1
LOG_LEVEL=WARNING
```

### Development Environment

```env
NETWORK_CIDR=192.168.1.0/26
INTERFACE=
SNMP_COMMUNITY=public
MONITOR_INTERVAL=15
PING_COUNT=2
LOG_LEVEL=DEBUG
```

## Validation

Check current configuration:

```python
# In Python shell
from app.config import settings
print(settings.model_dump_json(indent=2))
```

Or via API:

```bash
# Note: Only available in development mode
curl http://localhost:8000/api/debug/config
```

## Next Steps

- [Development Guide](10-development.md) - Set up development environment
- [API Reference](40-api-reference.md) - REST API endpoints
- [Security Guide](42-security.md) - Security best practices
- [Troubleshooting](31-troubleshooting.md) - Common configuration issues
