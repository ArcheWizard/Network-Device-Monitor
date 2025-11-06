# SNMP Service Interface

## Overview

The SNMP Service provides SNMPv2c query capabilities for device identification and metrics collection.

**Module:** `app.services.snmp`
**Location:** `backend/app/services/snmp.py`

## Common SNMP OIDs

```python
OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"       # sysName
OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"      # sysDescr
OID_SYS_UPTIME = "1.3.6.1.2.1.1.3.0"     # sysUpTime
OID_SYS_CONTACT = "1.3.6.1.2.1.1.4.0"    # sysContact
OID_SYS_LOCATION = "1.3.6.1.2.1.1.6.0"   # sysLocation
OID_SYS_OBJECTID = "1.3.6.1.2.1.1.2.0"   # sysObjectID
```

## Public Functions

### `async def snmp_get(target, oid, community, port, timeout, retries) -> Optional[str]`

Query a single SNMP OID.

**Parameters:**

- `target` (str): IP address of SNMP agent
- `oid` (str): OID to query (dotted decimal notation)
- `community` (str): SNMP community string. Default: "public"
- `port` (int): SNMP port. Default: 161
- `timeout` (float): Query timeout in seconds. Default: 2.0
- `retries` (int): Number of retries on failure. Default: 1

**Returns:** OID value as string, or None if query fails.

**Example:**

```python
from app.services import snmp

# Get system name
sys_name = await snmp.snmp_get(
    target="192.168.1.1",
    oid="1.3.6.1.2.1.1.5.0",
    community="public"
)
print(f"System Name: {sys_name}")

# Get system description
sys_descr = await snmp.snmp_get(
    target="192.168.1.1",
    oid="1.3.6.1.2.1.1.1.0",
    community="private",
    timeout=3.0
)
```

---

### `async def snmp_get_bulk(target, oids, community, port, timeout, retries) -> Dict[str, Optional[str]]`

Query multiple SNMP OIDs in parallel.

**Parameters:**

- `target` (str): IP address of SNMP agent
- `oids` (List[str]): List of OIDs to query
- `community` (str): SNMP community string. Default: "public"
- `port` (int): SNMP port. Default: 161
- `timeout` (float): Query timeout per OID. Default: 2.0
- `retries` (int): Number of retries per query. Default: 1

**Returns:** Dictionary mapping OID → value (or None if query failed).

**Example:**

```python
oids = [
    "1.3.6.1.2.1.1.5.0",  # sysName
    "1.3.6.1.2.1.1.1.0",  # sysDescr
    "1.3.6.1.2.1.1.3.0"   # sysUpTime
]

results = await snmp.snmp_get_bulk(
    target="192.168.1.1",
    oids=oids,
    community="public"
)

for oid, value in results.items():
    print(f"{oid}: {value}")
```

---

### `async def snmp_identify(target, community, timeout) -> Dict[str, Optional[str]]`

Query common SNMP identification OIDs.

**Parameters:**

- `target` (str): IP address of SNMP agent
- `community` (str): SNMP community string. Default: "public"
- `timeout` (float): Query timeout. Default: 2.0

**Returns:** Dictionary with identification data:

- `hostname` (Optional[str]): System name (sysName)
- `description` (Optional[str]): System description (sysDescr)
- `uptime` (Optional[str]): System uptime (sysUpTime)
- `contact` (Optional[str]): System contact (sysContact)
- `location` (Optional[str]): System location (sysLocation)
- `object_id` (Optional[str]): System object ID (sysObjectID)

**Example:**

```python
from app.services import snmp

# Identify device via SNMP
result = await snmp.snmp_identify(
    target="192.168.1.1",
    community="public",
    timeout=2.0
)

print(f"Hostname: {result['hostname']}")
print(f"Description: {result['description']}")
print(f"Location: {result['location']}")
```

**Integration Example:**

```python
from app.services import snmp, identification

async def full_identify(ip: str, mac: str = None):
    # Try SNMP first
    snmp_data = await snmp.snmp_identify(ip)

    # Fallback to OUI/DNS if SNMP fails
    if not snmp_data.get('hostname'):
        ident_data = await identification.identify_device(
            ip=ip,
            mac=mac,
            use_oui=True,
            use_snmp=False,
            use_dns=True
        )
        return {**snmp_data, **ident_data}

    return snmp_data
```

---

## Error Handling

SNMP queries handle errors gracefully and return None:

```python
# Device not SNMP-enabled
result = await snmp.snmp_get(target="192.168.1.100", oid="1.3.6.1.2.1.1.5.0")
# Returns: None (no exception raised)

# Invalid OID
result = await snmp.snmp_get(target="192.168.1.1", oid="invalid")
# Returns: None

# Timeout
result = await snmp.snmp_get(target="192.168.1.1", oid="1.3.6.1.2.1.1.5.0", timeout=0.1)
# Returns: None
```

---

## SNMP Walk (Future Feature)

SNMP walk functionality for bulk data retrieval:

```python
# Planned API (not yet implemented)
async def snmp_walk(target, oid_base, community="public"):
    """Walk SNMP tree starting from oid_base."""
    # Will use pysnmp's nextCmd or bulkCmd
    pass
```

---

## Common Use Cases

### Router Identification

```python
result = await snmp.snmp_identify("192.168.1.1", community="public")
# Typical output for Cisco router:
# {
#     'hostname': 'router',
#     'description': 'Cisco IOS Software, C2960 Software...',
#     'uptime': '12345600',
#     'contact': 'admin@example.com',
#     'location': 'Server Room',
#     'object_id': '1.3.6.1.4.1.9.1.696'
# }
```

### Switch Management

```python
# Get interface statistics (requires additional OIDs)
if_descr = await snmp.snmp_get("192.168.1.2", "1.3.6.1.2.1.2.2.1.2.1")
if_speed = await snmp.snmp_get("192.168.1.2", "1.3.6.1.2.1.2.2.1.5.1")
```

### Printer Discovery

```python
# Printers typically respond to SNMP
result = await snmp.snmp_identify("192.168.1.50")
if result.get('description') and 'printer' in result['description'].lower():
    print("Found printer!")
```

---

## Performance Considerations

- **Single OID query:** 100-2000ms (device-dependent)
- **Bulk query (6 OIDs):** 100-2000ms (parallel execution)
- **Timeout:** Set appropriate timeout based on network conditions
- **Retries:** Use retries=1 for unreliable networks

**Optimization Tips:**

```python
# Batch SNMP queries for multiple devices
import asyncio

devices = ["192.168.1.1", "192.168.1.2", "192.168.1.3"]
tasks = [snmp.snmp_identify(ip) for ip in devices]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

---

## Security Considerations

- **Community strings:** Default "public" is read-only; use "private" carefully
- **SNMP versions:** Currently supports SNMPv2c only (plaintext)
- **Network exposure:** SNMP should be restricted to management network
- **Sensitive data:** System contact/location may contain sensitive info

**Best Practices:**

```bash
# Use non-default community string in production
SNMP_COMMUNITY=my-secret-community

# Firewall SNMP port 161 UDP to management hosts only
# iptables -A INPUT -p udp --dport 161 -s 192.168.1.0/24 -j ACCEPT
# iptables -A INPUT -p udp --dport 161 -j DROP
```

---

## Testing

```python
# Run SNMP service tests (requires SNMP-enabled device on network)
pytest backend/tests/test_identification.py -k snmp
```

**Test Setup:**

For testing, you can use snmpsim or a real SNMP agent:

```bash
# Install snmpsim for testing
pip install snmpsim

# Run simulator
snmpsimd.py --agent-udpv4-endpoint=127.0.0.1:1161

# Test against simulator
result = await snmp.snmp_get("127.0.0.1", "1.3.6.1.2.1.1.1.0", port=1161)
```

---

## Dependencies

- `pysnmp` - SNMP protocol library
- Graceful degradation if pysnmp unavailable (returns None)

**Installation:**

```bash
pip install pysnmp
```

---

## Configuration

SNMP behavior is controlled via environment variables:

```bash
SNMP_COMMUNITY=public      # Community string
SNMP_PORT=161              # SNMP port
SNMP_TIMEOUT=1.0           # Query timeout in seconds
```

See `backend/app/config.py` for full settings.

---

## Future Enhancements

- SNMPv3 support (authentication and encryption)
- SNMP traps (asynchronous notifications)
- MIB browsing and OID resolution
- Interface statistics collection
- Bandwidth monitoring via SNMP counters
