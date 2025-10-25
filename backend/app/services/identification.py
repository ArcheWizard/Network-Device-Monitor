"""Device identification service using OUI lookup and SNMP queries."""

from __future__ import annotations

import logging
import socket
from typing import Dict, Optional

from app.utils.oui import lookup_vendor
from app.services.snmp import snmp_identify as snmp_query

logger = logging.getLogger(__name__)


async def identify_device(
    ip: str,
    mac: Optional[str] = None,
    use_oui: bool = True,
    use_snmp: bool = True,
    use_dns: bool = True,  # New parameter
    snmp_community: str = "public",
    snmp_timeout: float = 2.0,
) -> Dict[str, Optional[str]]:
    """Identify device using OUI lookup and SNMP queries.

    Args:
        ip: IP address of device
        mac: MAC address (optional, required for OUI lookup)
        use_oui: Enable OUI vendor lookup
        use_snmp: Enable SNMP identification
        use_dns: Enable DNS reverse lookup for hostname
        snmp_community: SNMP community string
        snmp_timeout: SNMP query timeout

    Returns:
        Dictionary with keys: vendor, hostname, description, uptime, contact, location, object_id
    """
    result: Dict[str, Optional[str]] = {
        "vendor": None,
        "hostname": None,
        "description": None,
        "uptime": None,
        "contact": None,
        "location": None,
        "object_id": None,
    }

    # OUI lookup
    if use_oui and mac:
        try:
            vendor = lookup_vendor(mac)
            if vendor:
                result["vendor"] = vendor
                logger.debug("OUI lookup for %s: %s", mac, vendor)
        except Exception as e:
            logger.warning("OUI lookup failed for %s: %s", mac, e)

    # SNMP identification
    if use_snmp:
        try:
            snmp_data = await snmp_query(
                ip, community=snmp_community, timeout=snmp_timeout
            )
            result.update(snmp_data)
            if snmp_data.get("hostname"):
                logger.debug(
                    "SNMP identification for %s: hostname=%s", ip, snmp_data["hostname"]
                )
        except Exception as e:
            logger.warning("SNMP identification failed for %s: %s", ip, e)

    # DNS reverse lookup (fallback if SNMP didn't provide hostname)
    if use_dns and not result["hostname"]:
        try:
            hostname = await dns_reverse_lookup(ip, timeout=2.0)
            if hostname:
                result["hostname"] = hostname
                logger.debug("DNS reverse lookup for %s: %s", ip, hostname)
        except Exception as e:
            logger.debug("DNS reverse lookup failed for %s: %s", ip, e)

    return result


async def dns_reverse_lookup(ip: str, timeout: float = 2.0) -> Optional[str]:
    """Perform DNS reverse lookup to get hostname from IP.

    Args:
        ip: IP address to lookup
        timeout: DNS query timeout in seconds

    Returns:
        Hostname if found, None otherwise
    """
    import asyncio

    try:
        # Run blocking DNS lookup in thread pool
        loop = asyncio.get_running_loop()
        hostname, _, _ = await asyncio.wait_for(
            loop.run_in_executor(None, socket.gethostbyaddr, ip), timeout=timeout
        )

        # Strip domain suffix if present (e.g., "device.local" -> "device")
        if hostname:
            # Keep full hostname for now, can add config to strip later
            return hostname

        return None
    except (socket.herror, socket.gaierror, asyncio.TimeoutError):
        # DNS lookup failed or timed out
        return None
    except Exception as e:
        logger.debug("DNS reverse lookup error for %s: %s", ip, e)
        return None


async def vendor_from_mac(mac: str) -> str | None:
    """Look up vendor from MAC address using OUI database.

    Args:
        mac: MAC address

    Returns:
        Vendor name if found, None otherwise
    """
    return lookup_vendor(mac)
