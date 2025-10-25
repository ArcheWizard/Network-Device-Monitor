from __future__ import annotations

from typing import List, Tuple

import psutil

try:
    from netaddr import IPAddress, IPNetwork
except Exception:  # pragma: no cover - optional import until deps installed
    IPAddress = None  # type: ignore
    IPNetwork = None  # type: ignore


def auto_detect_interfaces() -> List[str]:
    """Return a list of non-loopback interface names with IPv4 addresses."""
    names: List[str] = []
    for name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if (
                getattr(addr, "family", None) == 2
                and addr.address
                and not addr.address.startswith("127.")
            ):
                names.append(name)
                break
    return names


def interface_cidrs() -> List[Tuple[str, str]]:
    """Return (interface, cidr) for detected IPv4 addresses.

    Falls back gracefully if netaddr is not available.
    """
    pairs: List[Tuple[str, str]] = []
    for name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if (
                getattr(addr, "family", None) == 2
                and addr.address
                and not addr.address.startswith("127.")
            ):
                if IPAddress and IPNetwork and getattr(addr, "netmask", None):
                    try:
                        IPAddress(addr.address)
                        network = IPNetwork(f"{addr.address}/{addr.netmask}")
                        cidr = str(network.cidr)
                    except Exception:
                        cidr = f"{addr.address}/24"
                else:
                    cidr = f"{addr.address}/24"
                pairs.append((name, cidr))
    return pairs
