from __future__ import annotations

import asyncio
import ipaddress
import logging
import subprocess
from typing import Optional, Set

from ..config import settings
from ..utils.network import interface_cidrs

logger = logging.getLogger(__name__)


def _arp_scan_sync(
    cidr: str, interface: str | None = None, timeout: float = 3.0
) -> list[dict]:
    """Synchronous ARP scan with fallback to system tools for WiFi."""
    # Try scapy first
    try:
        from scapy.all import srp
        from scapy.layers.l2 import ARP, Ether
    except Exception as e:
        logger.warning("ARP scan skipped: scapy import failed: %s", e)
        return _arp_scan_fallback(cidr, interface)

    try:
        arp = ARP(pdst=cidr)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp
        result = srp(packet, timeout=max(1, int(timeout)), iface=interface, verbose=0)[
            0
        ]

        devices: list[dict] = []
        for _sent, received in result:
            ip = getattr(received, "psrc", None)
            mac = getattr(received, "hwsrc", None)
            if ip:
                entry: dict = {"ip": str(ip), "source": "arp"}
                if mac:
                    entry["mac"] = str(mac)
                devices.append(entry)

        # If scapy returned nothing, try fallback (WiFi compatibility)
        if not devices:
            logger.info("Scapy ARP scan returned 0 devices, trying fallback")
            return _arp_scan_fallback(cidr, interface)

        return devices
    except Exception as e:
        logger.error("ARP scan error on %s (iface=%s): %s", cidr, interface, e)
        # Always try fallback when scapy fails (WiFi or permission issues)
        logger.info("Attempting fallback ARP scan due to error")
        return _arp_scan_fallback(cidr, interface)


def _arp_scan_fallback(cidr: str, interface: str | None = None) -> list[dict]:
    """Fallback ARP scan using system arp-scan or ip neigh for WiFi compatibility."""
    devices: list[dict] = []

    # Try arp-scan first (most reliable)
    try:
        # Auto-detect interface if not specified
        if not interface:
            pairs = interface_cidrs()
            if pairs:
                interface = pairs[0][0]

        cmd = ["arp-scan", "--localnet"]
        if interface:
            cmd += ["--interface", interface]
        logger.debug("Running arp-scan: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        if result.returncode == 0:
            for line in result.stdout.splitlines():
                parts = line.strip().split()
                # Typical: "<ip>\t<mac>\t<vendor...>"
                if len(parts) >= 2 and "." in parts[0] and ":" in parts[1]:
                    ip = parts[0]
                    mac = parts[1]
                    devices.append({"ip": ip, "mac": mac, "source": "arp-scan"})
        else:
            logger.debug("arp-scan returned non-zero: %s", result.returncode)
    except FileNotFoundError:
        logger.debug("arp-scan not installed, trying ARP cache")
    except subprocess.TimeoutExpired:
        logger.debug("arp-scan timed out")
    except Exception as e:
        logger.debug("arp-scan error: %s", e)

    # Try reading system ARP cache as last resort
    try:
        logger.debug("Reading system ARP cache via 'ip neigh'")
        result = subprocess.run(
            ["ip", "neigh"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                # Example: "192.168.1.1 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE"
                line = line.strip()
                if not line or "lladdr" not in line:
                    continue
                parts = line.split()
                ip = parts[0]
                mac = None
                for i, tok in enumerate(parts):
                    if tok == "lladdr" and i + 1 < len(parts):
                        mac = parts[i + 1]
                        break
                entry: dict = {"ip": ip, "source": "ip-neigh"}
                if mac:
                    entry["mac"] = mac
                # Avoid duplicates by IP
                if not any(d.get("ip") == ip for d in devices):
                    devices.append(entry)
    except Exception as e:
        logger.debug("Failed to read ARP cache: %s", e)

    return devices


async def arp_scan(
    cidr: str, interface: str | None = None, timeout: float = 3.0
) -> list[dict]:
    # Run scapy (sync) in a thread so we don't block the event loop
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _arp_scan_sync, cidr, interface, timeout)


async def ping_sweep(
    cidr: str, timeout: float = 1.0, concurrency: int = 128, max_hosts: int = 4096
) -> list[str]:
    """Async ping sweep using system 'ping' for portability without raw sockets."""
    # Build list of host IPs for the network
    try:
        network = ipaddress.ip_network(cidr, strict=False)
    except Exception:
        return []
    sem = asyncio.Semaphore(max(1, int(concurrency)))

    async def ping_one(ip: str) -> bool:
        cmd = [
            "ping",
            "-c",
            "1",
            "-W",
            str(int(timeout)),
            ip,
        ]
        try:
            async with sem:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.communicate()
                return proc.returncode == 0
        except Exception:
            return False

    hosts = [str(ip) for ip in network.hosts()]
    # For very large networks, cap the number of hosts to probe to keep it safe
    if len(hosts) > max_hosts:
        logger.warning(
            "Ping sweep host count %d exceeds cap %d; truncating", len(hosts), max_hosts
        )
        hosts = hosts[:max_hosts]

    results = await asyncio.gather(
        *[ping_one(ip) for ip in hosts], return_exceptions=False
    )
    alive: list[str] = [ip for ip, ok in zip(hosts, results) if ok]
    return alive


async def mdns_discover(timeout: float = 3.0) -> list[dict]:
    """Discover mDNS services and return list of {ip, hostname, service}."""
    loop = asyncio.get_running_loop()

    def _mdns_sync(t: float) -> list[dict]:
        try:
            from zeroconf import ServiceBrowser, Zeroconf  # type: ignore
        except Exception as e:
            logger.debug("zeroconf not available: %s", e)
            return []

        results: list[dict] = []

        class _Listener:
            def __init__(self):
                self.items: list[dict] = []

            def remove_service(self, zc, type_, name):  # noqa: D401
                return

            def add_service(self, zc, type_, name):
                # We do not resolve here to keep it simple/fast
                self.items.append({"service": type_, "hostname": name})

            def update_service(self, zc, type_, name):
                return

        zc = Zeroconf()
        listener = _Listener()
        try:
            # Common service types might be discovered by browsing the special meta-service
            ServiceBrowser(zc, "_services._dns-sd._udp.local.", listener)
            # Simple sleep to accumulate results
            import time as _time

            _time.sleep(max(1, int(t)))
        finally:
            zc.close()

        # We don't attempt to resolve IPs here; keep structure consistent
        results.extend(listener.items)
        return results

    return await loop.run_in_executor(None, _mdns_sync, timeout)


async def scan(
    cidr: Optional[str] = None,
    interface: Optional[str] = None,
    arp_timeout: float = 3.0,
    ping_timeout: float = 1.0,
) -> list[dict]:
    """Run discovery for a target CIDR and return merged list of devices.

    Priority of sources: ARP (with MAC) then ICMP ping (IP only). mDNS optional later.
    """
    # Determine effective CIDR/interface with fallbacks
    raw_cidr = cidr if cidr is not None else getattr(settings, "NETWORK_CIDR", "")
    raw_iface = (
        interface if interface is not None else getattr(settings, "INTERFACE", None)
    )

    eff_cidr: Optional[str] = (
        raw_cidr.strip() if isinstance(raw_cidr, str) and raw_cidr else None
    )
    eff_iface: Optional[str] = (
        raw_iface.strip() if isinstance(raw_iface, str) and raw_iface else None
    )

    if not eff_cidr:
        # Auto-detect first non-loopback IPv4 interface network
        pairs = interface_cidrs()
        if pairs:
            eff_cidr = pairs[0][1]

    # Final fallback if still not set
    if not eff_cidr:
        eff_cidr = "192.168.1.0/24"

    # Run ARP scan
    logger.info("Starting ARP scan: cidr=%s iface=%s", eff_cidr, eff_iface)
    devices = await arp_scan(eff_cidr, interface=eff_iface, timeout=arp_timeout)
    seen_ips: Set[str] = {d["ip"] for d in devices if "ip" in d}

    # ICMP ping sweep to catch hosts that didn't answer ARP (e.g., some stacks)
    try:
        alive_ips = await ping_sweep(eff_cidr, timeout=ping_timeout)
    except Exception:
        alive_ips = []

    for ip in alive_ips:
        if ip not in seen_ips:
            devices.append({"ip": ip, "source": "icmp"})

    # Try to resolve MACs for ICMP-only hosts via ARP cache (so OUI can work)
    # (Best-effort; rely on _arp_scan_fallback to have primed cache)
    try:
        cache = _arp_scan_fallback(eff_cidr, eff_iface)
        mac_by_ip = {d["ip"]: d.get("mac") for d in cache if "ip" in d}
        for d in devices:
            ip = d.get("ip")
            if ip and not d.get("mac"):
                mac = mac_by_ip.get(ip)
                if mac:
                    d["mac"] = mac
    except Exception as e:
        logger.debug("Failed to enrich MACs from ARP cache: %s", e)

    # mDNS discovery (best-effort merge by hostname)
    try:
        mdns = await mdns_discover(timeout=2.5)
        for entry in mdns:
            host = entry.get("hostname")
            if not host:
                continue
            # Attach hostname for first device without one
            for d in devices:
                if not d.get("hostname"):
                    d["hostname"] = host
                    break
    except Exception as e:
        logger.debug("mDNS discover failed: %s", e)

    return devices
