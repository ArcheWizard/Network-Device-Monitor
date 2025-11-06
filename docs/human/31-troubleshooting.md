# Troubleshooting Guide

Common issues and solutions for the Network Device Monitor.

## General Issues

### Backend Won't Start

**Symptom:** Application exits immediately or shows import errors

**Solutions:**

1. Check Python version:
```bash
python --version  # Must be 3.11+
```

2. Verify dependencies:
```bash
cd backend
pip install -r requirements/base.txt
```

3. Check environment variables:
```bash
# Ensure .env file exists
ls -la .env

# Verify required variables
grep -E "NETWORK_CIDR|INTERFACE" .env
```

4. Review logs:
```bash
# Check for errors
python -m app.main
```

### Database Connection Errors

**Symptom:** `OperationalError: unable to open database file`

**Solutions:**

1. Check write permissions:
```bash
ls -ld backend/data/
# Should show write permissions for user
```

2. Create data directory:
```bash
mkdir -p backend/data
```

3. Verify SQLite:
```bash
python -c "import sqlite3; print(sqlite3.version)"
```

### InfluxDB Connection Failed

**Symptom:** `ConnectionError: InfluxDB connection failed`

**Solutions:**

1. Verify InfluxDB is running:
```bash
curl http://localhost:8086/health
```

2. Check credentials:
```bash
# Verify token is valid
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8086/api/v2/buckets
```

3. Check environment variables:
```bash
echo $INFLUX_URL
echo $INFLUX_TOKEN
echo $INFLUX_ORG
echo $INFLUX_BUCKET
```

4. Test from Python:
```python
from influxdb_client import InfluxDBClient

client = InfluxDBClient(
    url="http://localhost:8086",
    token="your-token",
    org="myorg"
)

print(client.health())
```

## Discovery Issues

### No Devices Discovered

**Symptom:** Discovery scan returns empty list

**Solutions:**

1. **Check network interface:**
```bash
# List interfaces
ip addr show

# Verify interface in .env matches
grep INTERFACE .env
```

2. **Verify network configuration:**
```bash
# Check CIDR
grep NETWORK_CIDR .env

# Ensure CIDR covers your network
# Example: 192.168.1.0/24 for 192.168.1.1-254
```

3. **Check permissions (for ARP scan):**
```bash
# ARP requires root or CAP_NET_RAW
sudo python -m app.main

# Or set capabilities
sudo setcap cap_net_raw+ep $(which python3)
```

4. **Try different discovery methods:**
```bash
# Test ICMP ping sweep (no special permissions)
curl -X POST http://localhost:8000/api/devices/discover
```

### ARP Scan Fails on WiFi

**Symptom:** `WARNING: arp_scan may not work on WiFi`

**Solutions:**

- WiFi adapters often don't support ARP scanning
- Use ICMP ping sweep instead (automatic fallback)
- Or use Ethernet connection for monitoring

### Discovery Takes Too Long

**Symptom:** Discovery scan times out or is very slow

**Solutions:**

1. **Reduce network size:**
```bash
# Use smaller CIDR
NETWORK_CIDR=192.168.1.0/26  # Only scans 64 addresses
```

2. **Adjust timeout:**
```python
# In backend/app/services/discovery.py
# Reduce ping timeout (line ~60)
timeout = 1  # seconds
```

3. **Check network latency:**
```bash
ping -c 5 192.168.1.1
# High latency will slow discovery
```

## Identification Issues

### Vendor Shows "Unknown"

**Symptom:** Device discovered but vendor is Unknown

**Solutions:**

1. **Update OUI database:**
```bash
cd backend
bash ../scripts/seed_oui.sh
```

2. **Check MAC address format:**
```bash
# MAC should be lowercase with colons
# Good: aa:bb:cc:dd:ee:ff
# Bad: AA-BB-CC-DD-EE-FF
```

3. **Verify OUI cache:**
```bash
ls -lh backend/data/oui_cache.csv
# Should be ~3MB with ~35000 entries
```

### SNMP Identification Fails

**Symptom:** No sysName or sysDescr from SNMP

**Solutions:**

1. **Check SNMP is enabled on device:**
```bash
# Test with snmpwalk
snmpwalk -v2c -c public 192.168.1.1 system
```

2. **Verify SNMP community string:**
```bash
# Check .env
grep SNMP_COMMUNITY .env

# Try different community
SNMP_COMMUNITY=private
```

3. **Check SNMP timeout:**
```python
# In backend/app/services/snmp.py
# Increase timeout if needed (line ~30)
timeout=2.0
```

### DNS Reverse Lookup Fails

**Symptom:** Hostname is null or not resolved

**Solutions:**

1. **Check DNS server:**
```bash
# Test reverse lookup
nslookup 192.168.1.1

# Or with dig
dig -x 192.168.1.1
```

2. **Verify network DNS:**
```bash
# Check /etc/resolv.conf
cat /etc/resolv.conf
```

3. **Use router's DNS:**
```bash
# Set DNS server explicitly
# In backend/app/services/identification.py
# Use router IP as DNS server
```

## Monitoring Issues

### No Metrics in InfluxDB

**Symptom:** Devices discovered but no metrics stored

**Solutions:**

1. **Check monitoring is running:**
```bash
# Look for "Monitoring job started" in logs
```

2. **Verify bucket exists:**
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8086/api/v2/buckets
```

3. **Check write permissions:**
```bash
# Token must have write access to bucket
# Verify in InfluxDB UI: Settings > Tokens
```

4. **Test write manually:**
```python
from app.storage.influx import InfluxMetricsWriter
from app.config import settings

writer = InfluxMetricsWriter(settings)
writer.write_metric("latency", {"device_id": "test"}, {"ms": 10.0})
```

### High Latency Values

**Symptom:** Reported latency much higher than expected

**Solutions:**

1. **Check network path:**
```bash
traceroute 192.168.1.1
```

2. **Verify device is responding:**
```bash
ping -c 10 192.168.1.1
```

3. **Check system load:**
```bash
top
# High CPU/memory usage can affect ping timing
```

### Device Status Stuck on "down"

**Symptom:** Device is online but shows as down

**Solutions:**

1. **Check firewall rules:**
```bash
# Device may be blocking ICMP
# Check device firewall settings
```

2. **Verify device IP:**
```bash
# IP may have changed (DHCP)
# Re-run discovery
```

3. **Manual ping test:**
```bash
ping -c 5 192.168.1.1
```

## WebSocket Issues

### WebSocket Connection Refused

**Symptom:** `WebSocket connection failed` in browser console

**Solutions:**

1. **Check backend is running:**
```bash
curl http://localhost:8000/health
```

2. **Verify WebSocket endpoint:**
```javascript
// Use correct protocol (ws:// not http://)
const ws = new WebSocket('ws://localhost:8000/ws/stream');
```

3. **Check CORS settings:**
```bash
# If accessing from different origin
# May need to configure CORS in backend
```

### No Messages Received

**Symptom:** WebSocket connects but no messages arrive

**Solutions:**

1. **Check discovery/monitoring are running:**
```bash
# Events only sent when things happen
# Try running discovery to generate events
curl -X POST http://localhost:8000/api/devices/discover
```

2. **Verify message handler:**
```javascript
ws.onmessage = (event) => {
    console.log('Received:', event.data);  // Should see messages
};
```

## Performance Issues

### High CPU Usage

**Symptom:** Backend consuming excessive CPU

**Solutions:**

1. **Check monitoring interval:**
```python
# In backend/app/scheduler/jobs.py
# Increase interval if too frequent
```

2. **Reduce device count:**
```bash
# Monitor fewer devices
# Or increase monitoring interval
```

3. **Profile the application:**
```bash
python -m cProfile -o profile.stats backend/app/main.py
```

### High Memory Usage

**Symptom:** Backend memory usage growing over time

**Solutions:**

1. **Check for memory leaks:**
```bash
# Monitor memory over time
watch -n 60 'ps aux | grep python'
```

2. **Limit InfluxDB client pool:**
```python
# In backend/app/storage/influx.py
# Adjust client settings
```

## Docker Issues

### Container Networking

**Symptom:** Container can't reach network devices

**Solutions:**

1. **Use host network mode:**
```yaml
services:
  backend:
    network_mode: host
```

2. **Check container capabilities:**
```yaml
services:
  backend:
    cap_add:
      - NET_RAW
      - NET_ADMIN
```

### Volume Permissions

**Symptom:** `Permission denied` when writing to volumes

**Solutions:**

```bash
# Fix volume ownership
sudo chown -R 1000:1000 ./backend/data

# Or in docker-compose.yml
services:
  backend:
    user: "1000:1000"
```

## Getting Help

If issues persist:

1. **Enable debug logging:**
```bash
LOG_LEVEL=DEBUG python -m app.main
```

2. **Check issue tracker:**
- GitHub Issues: https://github.com/yourusername/network-device-monitor/issues

3. **Provide diagnostic info:**
- Python version
- OS and distribution
- Full error messages and stack traces
- Environment configuration (redact secrets)

## Related Documentation

- [Configuration](03-configuration.md) - Environment setup
- [Deployment](30-deployment.md) - Production deployment
- [Database Management](32-database.md) - Database operations
