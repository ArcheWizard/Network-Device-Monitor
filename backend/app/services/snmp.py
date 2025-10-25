"""SNMP query utilities for device identification and metrics collection.

Uses pysnmp for SNMPv2c queries (asyncio-based).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Common SNMP OIDs
OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"  # sysName
OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"  # sysDescr
OID_SYS_UPTIME = "1.3.6.1.2.1.1.3.0"  # sysUpTime
OID_SYS_CONTACT = "1.3.6.1.2.1.1.4.0"  # sysContact
OID_SYS_LOCATION = "1.3.6.1.2.1.1.6.0"  # sysLocation
OID_SYS_OBJECTID = "1.3.6.1.2.1.1.2.0"  # sysObjectID

# Import pysnmp (optional dependency)
try:
    from pysnmp.hlapi.asyncio import (
        CommunityData,
        ContextData,
        ObjectIdentity,
        ObjectType,
        SnmpEngine,
        UdpTransportTarget,
    )

    PYSNMP_AVAILABLE = True
except ImportError:
    logger.warning("pysnmp not installed. SNMP functionality will be disabled.")
    # Provide Any-typed fallbacks so static analysis doesn't complain
    from typing import Any as _Any

    CommunityData: _Any = None
    ContextData: _Any = None
    ObjectIdentity: _Any = None
    ObjectType: _Any = None
    SnmpEngine: _Any = None
    UdpTransportTarget: _Any = None
    getCmd: _Any = None

    PYSNMP_AVAILABLE = False


async def snmp_get(
    target: str,
    oid: str,
    community: str = "public",
    port: int = 161,
    timeout: float = 2.0,
    retries: int = 1,
) -> Optional[str]:
    """Query a single SNMP OID.

    Args:
        target: IP address of SNMP agent
        oid: OID to query (dotted decimal notation)
        community: SNMP community string
        port: SNMP port
        timeout: Query timeout in seconds
        retries: Number of retries on failure

    Returns:
        OID value as string, or None if query fails
    """
    if not PYSNMP_AVAILABLE:
        return None

    try:
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((target, port), timeout=int(timeout), retries=retries),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )

        errorIndication, errorStatus, errorIndex, varBinds = await iterator

        if errorIndication:
            logger.debug("SNMP error for %s OID %s: %s", target, oid, errorIndication)
            return None
        elif errorStatus:
            logger.debug(
                "SNMP error for %s OID %s: %s at %s",
                target,
                oid,
                errorStatus.prettyPrint(),
                errorIndex,
            )
            return None
        else:
            for varBind in varBinds:
                return str(varBind[1])  # Return value as string

    except Exception as e:
        logger.debug("SNMP query failed for %s OID %s: %s", target, oid, e)
        return None
    # Ensure Optional[str] is always returned
    return None


async def snmp_get_bulk(
    target: str,
    oids: List[str],
    community: str = "public",
    port: int = 161,
    timeout: float = 2.0,
    retries: int = 1,
) -> Dict[str, Optional[str]]:
    """Query multiple SNMP OIDs in parallel.

    Args:
        target: IP address of SNMP agent
        oids: List of OIDs to query
        community: SNMP community string
        port: SNMP port
        timeout: Query timeout per OID
        retries: Number of retries per query

    Returns:
        Dictionary mapping OID → value (or None if query failed)
    """
    tasks = [snmp_get(target, oid, community, port, timeout, retries) for oid in oids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    output: Dict[str, Optional[str]] = {}
    for oid, val in zip(oids, results):
        if isinstance(val, Exception):
            output[oid] = None
        elif isinstance(val, str):
            output[oid] = val
        else:
            output[oid] = None
    return output


async def snmp_identify(
    target: str,
    community: str = "public",
    timeout: float = 2.0,
) -> Dict[str, Optional[str]]:
    """Query common SNMP identification OIDs.

    Args:
        target: IP address of SNMP agent
        community: SNMP community string
        timeout: Query timeout

    Returns:
        Dictionary with keys: hostname, description, uptime, contact, location, object_id
    """
    oids = {
        "hostname": OID_SYS_NAME,
        "description": OID_SYS_DESCR,
        "uptime": OID_SYS_UPTIME,
        "contact": OID_SYS_CONTACT,
        "location": OID_SYS_LOCATION,
        "object_id": OID_SYS_OBJECTID,
    }

    results = await snmp_get_bulk(
        target, list(oids.values()), community, timeout=timeout
    )

    return {key: results.get(oid) for key, oid in oids.items()}
