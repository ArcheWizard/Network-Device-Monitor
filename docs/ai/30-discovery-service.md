# Discovery Service Interface

## Overview

The Discovery Service provides network scanning capabilities using multiple methods (ARP, ICMP ping, mDNS/Zeroconf) to discover devices on a local network.

**Module:** `app.services.discovery`
**Location:** `backend/app/services/discovery.py`

## Public Functions

### `async def scan(cidr, interface, arp_timeout, ping_timeout) -> list[dict]`

Main discovery function that orchestrates multiple scanning methods.

**Parameters:**
- `cidr` (Optional[str]): Target network CIDR (e.g., "192.168.1.0/24"). Defaults to `settings.NETWORK_CIDR` or auto-detected.
- `interface` (Optional[str]): Network interface name (e.g., "eth0", "wlan0"). Auto-detected if None.
- `arp_timeout` (float): ARP scan timeout in seconds. Default: 3.0
- `ping_timeout` (float): Ping sweep timeout per host in seconds. Default: 1.0

**Returns:** List of discovered devices as dictionaries with keys:
- `ip` (str): IPv4 address
- `mac` (Optional[str]): MAC address (if available)
- `hostname` (Optional[str]): Hostname (if discovered via mDNS)
- `source` (str): Discovery method ("arp", "icmp", "mdns")

**Example:**
```python
from app.services import discovery

# Scan with defaults
devices = await discovery.scan()

# Scan specific network
devices = await discovery.scan(
    cidr="10.0.0.0/24",
    interface="eth0",
    arp_timeout=5.0,
    ping_timeout=2.0
)

# Process results
for device in devices:
    print(f"Found {device['ip']} ({device.get('mac', 'no MAC')})")
```

---

### `async def arp_scan(cidr, interface, timeout) -> list[dict]`

Perform ARP scan to discover devices on the local network.

**Parameters:**
- `cidr` (str): Target network CIDR
- `interface` (Optional[str]): Network interface name
- `timeout` (float): Scan timeout in seconds. Default: 3.0

**Returns:** List of devices with `ip`, `mac`, and `source="arp"` fields.

**Notes:**
- Uses Scapy for packet crafting (requires CAP_NET_RAW on Linux)
- Falls back to system tools (`arp-scan`, `ip neigh`) if Scapy unavailable or on WiFi
- Best for discovering devices on same Layer 2 network

**Example:**
```python
devices = await discovery.arp_scan(
    cidr="192.168.1.0/24",
    interface="eth0",
    timeout=3.0
)
```

---

### `async def ping_sweep(cidr, timeout, concurrency, max_hosts) -> list[str]`

Perform ICMP ping sweep to find active hosts.

**Parameters:**
- `cidr` (str): Target network CIDR
- `timeout` (float): Timeout per ping in seconds. Default: 1.0
- `concurrency` (int): Maximum concurrent pings. Default: 128
- `max_hosts` (int): Maximum hosts to scan (safety cap). Default: 4096

**Returns:** List of IP addresses that responded to ping.

**Notes:**
- Uses system `ping` command (no raw socket permissions needed)
- Async implementation with semaphore for concurrency control
- Useful for discovering devices that don't respond to ARP

**Example:**
```python
alive_ips = await discovery.ping_sweep(
    cidr="192.168.1.0/24",
    timeout=1.0,
    concurrency=256
)
print(f"Found {len(alive_ips)} active hosts")
```

---

### `async def mdns_discover(timeout) -> list[dict]`

Discover mDNS/Zeroconf services on the network.

**Parameters:**
- `timeout` (float): Discovery timeout in seconds. Default: 3.0

**Returns:** List of discovered services with `service` and `hostname` fields.

**Notes:**
- Requires `zeroconf` library
- Discovers devices advertising services via mDNS (e.g., printers, IoT devices)
- Non-blocking async wrapper around synchronous zeroconf library

**Example:**
```python
services = await discovery.mdns_discover(timeout=5.0)
for svc in services:
    print(f"Service: {svc['service']} - {svc['hostname']}")
```

---

## Internal Functions

### `def _arp_scan_sync(cidr, interface, timeout) -> list[dict]`

Synchronous ARP scan implementation using Scapy.

### `def _arp_scan_fallback(cidr, interface) -> list[dict]`

Fallback ARP scan using system tools (`arp-scan` or `ip neigh`). Used when:
- Scapy is unavailable
- Scapy fails (e.g., WiFi interface restrictions)
- Raw socket permissions are insufficient

---

## Integration Example

```python
from fastapi import Request
from app.services import discovery, identification
import time

async def full_discovery(request: Request):
    # Run discovery
    devices = await discovery.scan(
        cidr="192.168.1.0/24",
        arp_timeout=3.0,
        ping_timeout=1.0
    )

    # Identify each device
    for device in devices:
        if device.get('ip'):
            ident = await identification.identify_device(
                ip=device['ip'],
                mac=device.get('mac'),
                use_oui=True,
                use_snmp=True,
                use_dns=True
            )
            device.update(ident)

    # Persist to repository
    repo = request.app.state.inventory_repo
    now = int(time.time())
    for device in devices:
        device_id = device.get('mac') or device.get('ip')
        await repo.upsert_device({
            'id': device_id,
            'ip': device.get('ip'),
            'mac': device.get('mac'),
            'hostname': device.get('hostname'),
            'vendor': device.get('vendor'),
            'first_seen': now,
            'last_seen': now,
            'tags': {'source': device.get('source', 'unknown')}
        })

    return devices
```

---

## Error Handling

All discovery functions handle errors gracefully and return partial results:

```python
try:
    devices = await discovery.scan()
except Exception as e:
    # Scan failed completely - network interface issue?
    logger.error(f"Discovery scan failed: {e}")
    devices = []

# Even if some methods fail, others may succeed
# Example: ARP fails but ping sweep works
```

---

## Performance Considerations

- **ARP scan:** Fast (~3-5 seconds for /24 network)
- **Ping sweep:** Scales with network size and concurrency settings
  - /24 network with 128 concurrency: ~5-10 seconds
  - /16 network: Use `max_hosts` cap or increase timeout
- **mDNS:** Fixed timeout (2-5 seconds), low overhead
- **Total scan time:** Typically 10-15 seconds for small networks

---

## Testing

```python
# Run discovery service tests
pytest backend/tests/test_discovery_api.py
pytest backend/tests/test_discovery_persistence.py
```

---

## Dependencies

- `scapy` - ARP packet crafting (optional, falls back to system tools)
- `zeroconf` - mDNS discovery (optional)
- System utilities: `arp-scan`, `ip`, `ping`

---

## Configuration

Discovery behavior is controlled via environment variables:

```bash
NETWORK_CIDR=192.168.1.0/24    # Default scan target
INTERFACE=eth0                  # Preferred interface (auto-detect if unset)
```

See `backend/app/config.py` for full settings.
