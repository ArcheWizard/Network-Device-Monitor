# Discovery Feature

Network discovery is the core feature that identifies devices on your network using multiple scanning methods.

## Overview

The discovery system uses three complementary methods to find network devices:

1. **ARP Scanning** - Discovers devices on the local network segment (Layer 2)
2. **ICMP Ping Sweep** - Finds devices across IP ranges (Layer 3)
3. **mDNS/Zeroconf** - Discovers devices advertising services

## Quick Start

### Trigger Manual Scan

Via API:
```bash
curl -X POST http://localhost:8000/api/discovery/scan \
  -H "Content-Type: application/json" \
  -d '{}'
```

Via Python:
```python
import asyncio
import httpx

async def scan():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/discovery/scan",
            json={"persist": True, "identify": True}
        )
        result = response.json()
        print(f"Found {result['count']} devices")

asyncio.run(scan())
```

### View Discovered Devices

```bash
curl http://localhost:8000/api/devices
```

## Discovery Methods

### ARP Scanning

**Best for:** Local network (same subnet)
**Advantages:**
- Fast (3-5 seconds for /24 network)
- Provides MAC addresses
- Works with devices that don't respond to ping

**How it works:**
1. Sends ARP requests to all IPs in target network
2. Collects ARP responses with IP and MAC addresses
3. Falls back to system tools (arp-scan, ip neigh) if Scapy unavailable

**Configuration:**
```bash
NETWORK_CIDR=192.168.1.0/24  # Target network
INTERFACE=eth0                # Network interface (auto-detect if unset)
```

### ICMP Ping Sweep

**Best for:** Larger networks, remote subnets
**Advantages:**
- No special permissions required (uses system `ping`)
- Works across routers
- Fast parallel execution

**How it works:**
1. Generates list of all IPs in CIDR range
2. Pings each IP in parallel (configurable concurrency)
3. Returns list of responding IPs

**Configuration:**
```python
# In discovery scan request
{
    "cidr": "10.0.0.0/16",
    "ping_timeout": 1.0,  # Timeout per ping
    "concurrency": 256     # Max concurrent pings
}
```

### mDNS Discovery

**Best for:** IoT devices, printers, smart home devices
**Advantages:**
- Discovers device hostnames and services
- No scanning needed - devices announce themselves
- Works with Bonjour/Avahi devices

**How it works:**
1. Listens for mDNS service announcements
2. Collects service names and hostnames
3. Merges with ARP/ICMP results

## Discovery Parameters

### Basic Scan

```json
{
    "cidr": "192.168.1.0/24",
    "interface": "eth0",
    "persist": true,
    "identify": true
}
```

### Advanced Scan

```json
{
    "cidr": "10.0.0.0/16",
    "interface": "eth0",
    "arp_timeout": 5.0,
    "ping_timeout": 2.0,
    "persist": true,
    "identify": true
}
```

**Parameters:**
- `cidr` - Target network in CIDR notation (defaults to NETWORK_CIDR)
- `interface` - Network interface name (defaults to INTERFACE or auto-detect)
- `arp_timeout` - ARP scan timeout in seconds (default: 3.0)
- `ping_timeout` - Ping sweep timeout per host in seconds (default: 1.0)
- `persist` - Save discovered devices to database (default: true)
- `identify` - Run identification (OUI, SNMP, DNS) on devices (default: true)

## Scheduled Discovery

Discovery can run automatically on a schedule (configured in `backend/app/scheduler/jobs.py`):

```python
# Example: Run discovery every hour
scheduler.add_job(
    discovery_job,
    'interval',
    hours=1,
    args=[app]
)
```

## Discovery Results

Discovered devices include:

```json
{
    "count": 5,
    "devices": [
        {
            "ip": "192.168.1.1",
            "mac": "aa:bb:cc:dd:ee:ff",
            "hostname": "router.local",
            "vendor": "Cisco Systems",
            "source": "arp"
        },
        {
            "ip": "192.168.1.100",
            "mac": "11:22:33:44:55:66",
            "hostname": "laptop",
            "vendor": "Apple Inc",
            "source": "arp"
        }
    ],
    "persisted": true,
    "identified": true
}
```

**Fields:**
- `ip` - IPv4 address
- `mac` - MAC address (if available)
- `hostname` - Device hostname (from mDNS or DNS)
- `vendor` - Device vendor from OUI lookup
- `source` - Discovery method ("arp", "icmp", "mdns")

## Persistence

When `persist=true`, discovered devices are saved to the SQLite database with:

- Stable ID (MAC address if available, else IP)
- First seen timestamp
- Last seen timestamp
- Discovery source tag

Subsequent scans update existing devices rather than creating duplicates.

## Identification Integration

When `identify=true`, each discovered device is enriched with:

- **Vendor** - From MAC address OUI lookup
- **Hostname** - From SNMP or DNS reverse lookup
- **Description** - From SNMP sysDescr
- **Additional SNMP data** - Contact, location, uptime

See [Identification](21-identification.md) for details.

## Performance

**Typical scan times for /24 network (254 hosts):**
- ARP scan: 3-5 seconds
- Ping sweep (128 concurrency): 5-10 seconds
- mDNS: 2-3 seconds
- **Total: ~10-15 seconds**

**Large networks:**
- /16 network: Use higher ping concurrency or cap max_hosts
- Multiple subnets: Run discovery jobs in parallel

## Troubleshooting

### ARP Scan Returns No Devices

**Cause:** Insufficient permissions or WiFi interface

**Solutions:**
```bash
# Grant capabilities (Linux)
sudo setcap cap_net_raw,cap_net_admin=eip $(readlink -f .venv/bin/python)

# Install arp-scan fallback
sudo apt install arp-scan

# Use fallback tools
# System will automatically use `arp-scan` or `ip neigh` if Scapy fails
```

### Discovery is Slow

**Cause:** Network size or timeout settings

**Solutions:**
- Reduce `ping_timeout` to 0.5-1.0 seconds
- Increase `ping_concurrency` to 256-512
- Split large networks into smaller subnets

### WiFi Interface Not Discovered

**Cause:** Scapy has issues with some WiFi adapters

**Solution:** The system automatically falls back to `arp-scan` or `ip neigh` which work with WiFi

### No Devices Found on Remote Subnet

**Cause:** ARP doesn't work across routers

**Solution:** Use ping_sweep for Layer 3 discovery:
```json
{
    "cidr": "10.0.0.0/24",
    "arp_timeout": 0,  # Skip ARP
    "ping_timeout": 2.0
}
```

## Security Considerations

- ARP scanning requires elevated privileges (CAP_NET_RAW on Linux)
- Discovery generates network traffic - be mindful in production environments
- Consider scheduling discovery during off-peak hours
- Firewall rules may block ICMP ping - coordinate with network team

## Best Practices

1. **Start with small networks** - Test on /24 before scanning larger ranges
2. **Use appropriate timeouts** - Balance speed vs accuracy
3. **Enable identification** - Enriches device data
4. **Enable persistence** - Builds device history over time
5. **Schedule regular scans** - Keeps inventory up-to-date
6. **Monitor scan duration** - Optimize settings based on network size

## API Reference

See [API Reference](40-api-reference.md) for complete API documentation.

## Related Features

- [Identification](21-identification.md) - Device identification via OUI, SNMP, DNS
- [Monitoring](22-monitoring.md) - Health monitoring and metrics
- [WebSocket](23-websocket.md) - Real-time discovery notifications
