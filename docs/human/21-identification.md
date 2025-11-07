# Device Identification

Device identification enriches discovered devices with detailed information using multiple lookup methods.

## Overview

The identification system uses three complementary methods:

1. **OUI Lookup** - MAC address to vendor mapping (offline, fast)
2. **SNMP Queries** - Device system information (requires SNMP access)
3. **DNS Reverse Lookup** - IP to hostname resolution

## Quick Start

```bash
# Identification runs automatically during discovery with identify=true
curl -X POST http://localhost:8000/api/devices/discover \
  -H "Content-Type: application/json" \
  -d '{"identify": true}'
```

## OUI Vendor Lookup

**What it does:** Maps MAC address prefixes to manufacturer names

**Data source:** IEEE OUI (Organizationally Unique Identifier) database

**Speed:** ~1ms (local CSV file)

**Setup:**
```bash
# Download OUI database
make seed-oui
```

**Example:**
```
MAC: aa:bb:cc:dd:ee:ff
OUI Prefix: AA:BB:CC
Vendor: Apple Inc.
```

## SNMP Identification

**What it does:** Queries device via SNMPv2c for system information

**Requirements:**
- Device must support SNMP
- SNMP community string (default: "public")
- Network access to UDP port 161

**Retrieved data:**
- System name (sysName)
- System description (sysDescr)
- System uptime (sysUpTime)
- System contact (sysContact)
- System location (sysLocation)
- System object ID (sysObjectID)

**Configuration:**
```bash
SNMP_COMMUNITY=public
SNMP_PORT=161
SNMP_TIMEOUT=2.0
```

**Common device responses:**
- **Routers:** Cisco IOS, Juniper JUNOS
- **Switches:** Vendor-specific descriptions
- **Printers:** Model and firmware info
- **Network appliances:** Product name and version

## DNS Reverse Lookup

**What it does:** Resolves IP addresses to hostnames via PTR records

**Requirements:**
- Properly configured DNS server
- PTR records for devices

**Speed:** 50-2000ms (network-dependent)

**Examples:**
```
IP: 192.168.1.1 → hostname: router.local
IP: 192.168.1.100 → hostname: laptop.example.com
IP: 192.168.1.200 → (no PTR record)
```

## Identification Priority

When multiple methods provide data, the system uses this priority:

1. SNMP hostname (most reliable for managed devices)
2. DNS reverse lookup (if SNMP unavailable)
3. mDNS hostname (from discovery phase)

Vendor information comes from OUI lookup if MAC address is available.

## Performance

**Single device identification:**
- OUI lookup: ~1ms
- SNMP query: 100-2000ms
- DNS lookup: 50-2000ms
- **Total: 150-4000ms per device**

**Bulk identification:**
Uses async parallel execution to identify multiple devices simultaneously.

## Troubleshooting

### SNMP Queries Fail

**Cause:** SNMP not enabled or wrong community string

**Solutions:**
1. Verify SNMP is enabled on device
2. Check SNMP community string: `SNMP_COMMUNITY=your-community`
3. Verify network connectivity to port 161/udp
4. Check firewall rules

**Test SNMP manually:**
```bash
snmpwalk -v2c -c public 192.168.1.1 system
```

### No Vendor from MAC Address

**Cause:** OUI database missing or MAC prefix not in database

**Solutions:**
```bash
# Update OUI database
make seed-oui

# Verify database exists
ls -lh backend/data/oui_cache.csv
```

### DNS Lookups Slow

**Cause:** DNS server slow or unresponsive

**Solutions:**
- Reduce timeout: Configure shorter DNS timeout
- Disable DNS lookup if not needed
- Use local DNS cache/resolver

### Identification Disabled

Check configuration in discovery API call:
```json
{
    "identify": true,  # Must be true
    "persist": true
}
```

## Configuration Reference

```bash
# SNMP Settings
SNMP_COMMUNITY=public      # Community string
SNMP_PORT=161              # SNMP port
SNMP_TIMEOUT=2.0           # Query timeout

# OUI Database
# Located at: backend/data/oui_cache.csv
# Update with: make seed-oui
```

## Best Practices

1. **Update OUI database regularly** - Run `make seed-oui` monthly
2. **Use appropriate SNMP community** - Don't use default "public" in production
3. **Set realistic timeouts** - Balance between thoroughness and speed
4. **Secure SNMP access** - Restrict SNMP to management network
5. **Monitor identification success rate** - Track which methods work best

## Security Considerations

- **SNMP community strings** are transmitted in plaintext
- **SNMPv3** with authentication is more secure (future enhancement)
- **Restrict SNMP access** to management network only
- **OUI database** may contain outdated information

## API Integration

Identification happens automatically during discovery with `identify=true`, but can be called separately:

```python
from app.services import identification

result = await identification.identify_device(
    ip="192.168.1.1",
    mac="aa:bb:cc:dd:ee:ff",
    use_oui=True,
    use_snmp=True,
    use_dns=True
)

print(result['vendor'])    # "Cisco Systems"
print(result['hostname'])  # "router"
```

## Related Features

- [Discovery](20-discovery.md) - Network device discovery
- [Monitoring](22-monitoring.md) - Device health monitoring
- [API Reference](40-api-reference.md) - Complete API documentation
