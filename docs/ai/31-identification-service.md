# Identification Service Interface

## Overview

The Identification Service enriches discovered devices with additional information using OUI lookup, SNMP queries, and DNS reverse lookups.

**Module:** `app.services.identification`
**Location:** `backend/app/services/identification.py`

## Public Functions

### `async def identify_device(ip, mac, use_oui, use_snmp, use_dns, snmp_community, snmp_timeout) -> Dict[str, Optional[str]]`

Comprehensive device identification using multiple methods.

**Parameters:**
- `ip` (str): IP address of the device
- `mac` (Optional[str]): MAC address (required for OUI lookup)
- `use_oui` (bool): Enable OUI vendor lookup. Default: True
- `use_snmp` (bool): Enable SNMP identification. Default: True
- `use_dns` (bool): Enable DNS reverse lookup. Default: True
- `snmp_community` (str): SNMP community string. Default: "public"
- `snmp_timeout` (float): SNMP query timeout in seconds. Default: 2.0

**Returns:** Dictionary with identification data:
- `vendor` (Optional[str]): Device vendor from OUI database
- `hostname` (Optional[str]): Device hostname from SNMP or DNS
- `description` (Optional[str]): System description from SNMP
- `uptime` (Optional[str]): System uptime from SNMP
- `contact` (Optional[str]): System contact from SNMP
- `location` (Optional[str]): System location from SNMP
- `object_id` (Optional[str]): System object ID from SNMP

**Example:**
```python
from app.services import identification

# Full identification
result = await identification.identify_device(
    ip="192.168.1.1",
    mac="aa:bb:cc:dd:ee:ff",
    use_oui=True,
    use_snmp=True,
    use_dns=True
)

print(f"Vendor: {result['vendor']}")
print(f"Hostname: {result['hostname']}")
print(f"Description: {result['description']}")

# OUI-only (fast, offline)
result = await identification.identify_device(
    ip="192.168.1.100",
    mac="11:22:33:44:55:66",
    use_oui=True,
    use_snmp=False,
    use_dns=False
)
print(f"Vendor: {result['vendor']}")
```

---

### `async def dns_reverse_lookup(ip, timeout) -> Optional[str]`

Perform DNS reverse lookup (PTR record query).

**Parameters:**
- `ip` (str): IP address to lookup
- `timeout` (float): Query timeout in seconds. Default: 2.0

**Returns:** Hostname string if found, None otherwise.

**Notes:**
- Uses Python's `socket.gethostbyaddr()` in thread pool (blocking I/O)
- Returns full FQDN (e.g., "device.example.com")
- Handles timeouts and DNS errors gracefully

**Example:**
```python
hostname = await identification.dns_reverse_lookup(
    ip="192.168.1.1",
    timeout=2.0
)
if hostname:
    print(f"Hostname: {hostname}")
else:
    print("No PTR record found")
```

---

### `async def vendor_from_mac(mac) -> str | None`

Look up vendor from MAC address using IEEE OUI database.

**Parameters:**
- `mac` (str): MAC address (format: "aa:bb:cc:dd:ee:ff" or "AA-BB-CC-DD-EE-FF")

**Returns:** Vendor name string if found, None otherwise.

**Notes:**
- Wraps synchronous `lookup_vendor()` function from `app.utils.oui`
- OUI database cached in `backend/data/oui_cache.csv`
- Fast local lookup (no network requests)

**Example:**
```python
vendor = await identification.vendor_from_mac("aa:bb:cc:dd:ee:ff")
print(f"Vendor: {vendor}")  # e.g., "Cisco Systems, Inc."
```

---

## Integration with Discovery

```python
from app.services import discovery, identification

# Discover devices
devices = await discovery.scan(cidr="192.168.1.0/24")

# Identify each device
for device in devices:
    ip = device.get('ip')
    mac = device.get('mac')

    if ip:
        ident_data = await identification.identify_device(
            ip=ip,
            mac=mac,
            use_oui=True,
            use_snmp=True,
            use_dns=True
        )

        # Merge identification data
        device['vendor'] = ident_data.get('vendor')
        device['hostname'] = ident_data.get('hostname') or device.get('hostname')
        device['description'] = ident_data.get('description')
        device['contact'] = ident_data.get('contact')
        device['location'] = ident_data.get('location')

# Now devices have enriched information
for device in devices:
    print(f"{device['ip']} - {device.get('vendor', 'Unknown')} - {device.get('hostname', 'N/A')}")
```

---

## SNMP Integration

The identification service uses the SNMP service (`app.services.snmp`) internally:

```python
from app.services import snmp

# Query common system information
snmp_data = await snmp.snmp_identify(
    target="192.168.1.1",
    community="public",
    timeout=2.0
)

# Returns: {
#   'hostname': 'router',
#   'description': 'Cisco IOS ...',
#   'uptime': '12345600',
#   'contact': 'admin@example.com',
#   'location': 'Server Room',
#   'object_id': '1.3.6.1.4.1.9'
# }
```

---

## OUI Database

The OUI (Organizationally Unique Identifier) database maps MAC address prefixes to vendors.

**Location:** `backend/data/oui_cache.csv`
**Source:** IEEE OUI database
**Update:** Run `make seed-oui` or `bash scripts/seed_oui.sh`

**Format:**
```csv
mac_prefix,vendor_name
00:00:0C,Cisco Systems, Inc.
00:00:5E,ICANN, IANA Department
...
```

**Usage:**
```python
from app.utils.oui import lookup_vendor

vendor = lookup_vendor("aa:bb:cc:dd:ee:ff")
# Looks up "AA:BB:CC" prefix in OUI database
```

---

## Error Handling

Identification methods fail gracefully and return None for unavailable data:

```python
result = await identification.identify_device(
    ip="192.168.1.100",
    mac="invalid-mac",
    use_oui=True,
    use_snmp=True,
    use_dns=True
)

# Even if all methods fail:
# result = {
#     'vendor': None,
#     'hostname': None,
#     'description': None,
#     'uptime': None,
#     'contact': None,
#     'location': None,
#     'object_id': None
# }
```

Individual identification methods log warnings but don't raise exceptions:

```python
# SNMP fails (device not SNMP-enabled) -> returns None values
# DNS fails (no PTR record) -> returns None
# OUI fails (MAC not in database) -> returns None
# Overall function always returns a dict (never raises)
```

---

## Performance Considerations

- **OUI lookup:** ~1ms (local CSV file)
- **DNS reverse lookup:** 50-2000ms (network-dependent, subject to timeout)
- **SNMP query:** 100-2000ms (device-dependent, subject to timeout)
- **Total:** Typically 1-5 seconds per device

For bulk identification:

```python
import asyncio

# Identify multiple devices in parallel
devices = [...]  # List of discovered devices
tasks = [
    identification.identify_device(
        ip=device['ip'],
        mac=device.get('mac'),
        use_oui=True,
        use_snmp=True,
        use_dns=True
    )
    for device in devices if device.get('ip')
]

results = await asyncio.gather(*tasks, return_exceptions=True)

for device, result in zip(devices, results):
    if isinstance(result, dict):
        device.update(result)
```

---

## Configuration

Identification behavior is controlled via environment variables:

```bash
SNMP_COMMUNITY=public    # SNMP community string
SNMP_PORT=161            # SNMP port
SNMP_TIMEOUT=1.0         # SNMP query timeout
```

See `backend/app/config.py` for full settings.

---

## Testing

```python
# Run identification service tests
pytest backend/tests/test_identification.py
pytest backend/tests/test_oui_lookup.py
```

---

## Dependencies

- `pysnmp` - SNMP queries (optional, graceful degradation if unavailable)
- Standard library: `socket` for DNS lookups
- Custom: `app.utils.oui` for OUI database access
