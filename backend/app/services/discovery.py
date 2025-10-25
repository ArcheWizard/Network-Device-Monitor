from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
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
        from scapy.all import ARP, Ether, srp  # type: ignore
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
                devices.append(
                    {"ip": str(ip), "mac": str(mac) if mac else None, "source": "arp"}
                )

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
    """Fallback ARP scan using system arp-scan or nmap for WiFi compatibility."""
    devices: list[dict] = []

    # Try arp-scan first (most reliable)
    try:
        # Auto-detect interface if not specified
        if not interface:
            pairs = interface_cidrs()
            if pairs:
                interface = pairs[0][0]  # Use first detected interface
                logger.debug("Auto-detected interface for arp-scan: %s", interface)

        cmd = ["arp-scan", "--localnet", "--interface", interface or "auto"]
        logger.debug("Running arp-scan: %s", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            for line in result.stdout.splitlines():
                # Parse: 192.168.1.1	aa:bb:cc:dd:ee:ff	Vendor Name
                parts = line.split("\t")
                if len(parts) >= 2:
                    ip, mac = parts[0].strip(), parts[1].strip()
                    if ip and ":" in mac:
                        devices.append({"ip": ip, "mac": mac, "source": "arp-scan"})

            if devices:
                logger.info("Fallback arp-scan found %d devices", len(devices))
                return devices
        else:
            logger.debug(
                "arp-scan failed with return code %d: %s",
                result.returncode,
                result.stderr,
            )
    except FileNotFoundError:
        logger.debug("arp-scan not installed, trying ARP cache")
    except subprocess.TimeoutExpired:
        logger.debug("arp-scan timed out")
    except Exception as e:
        logger.debug("arp-scan error: %s", e)

    # Try reading system ARP cache as last resort
    try:
        logger.debug("Reading system ARP cache")
        result = subprocess.run(
            ["ip", "neigh"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                # Parse: 192.168.1.1 dev wlp8s0 lladdr aa:bb:cc:dd:ee:ff REACHABLE
                parts = line.split()
                if len(parts) >= 5 and parts[3] == "lladdr":
                    ip, mac = parts[0], parts[4]
                    if ":" in mac:
                        devices.append({"ip": ip, "mac": mac, "source": "arp-cache"})

            if devices:
                logger.info("Fallback ARP cache found %d devices", len(devices))
            else:
                logger.warning(
                    "ARP cache is empty - try pinging devices first to populate it"
                )
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

    # Limit concurrency to avoid spawning too many processes
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
        # Some distros use busybox ping with -w timeout; but -W 1 -c 1 is common on Linux
        try:
            async with sem:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
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
            from zeroconf import Zeroconf, ServiceBrowser
        except Exception as e:
            logger.warning("mDNS discovery skipped: zeroconf import failed: %s", e)
            return []

        class _TypeListener:
            def __init__(self):
                self.types: Set[str] = set()

            def add_service(self, zc, type_, name):  # type: ignore[no-redef]
                self.types.add(name)

            def update_service(self, zc, type_, name):
                return

            def remove_service(self, zc, type_, name):
                return

        class _InstanceListener:
            def __init__(self, zc: "Zeroconf", stype: str, out: list[dict]):
                self.zc = zc
                self.stype = stype
                self.out = out

            def add_service(self, zc, type_, name):  # type: ignore[no-redef]
                try:
                    info = self.zc.get_service_info(
                        self.stype, name, timeout=int(max(1.0, t) * 1000)
                    )
                    if not info:
                        return
                    addrs: list[str] = []
                    for a in getattr(info, "addresses", []) or []:
                        try:
                            addrs.append(socket.inet_ntoa(a))
                        except Exception:
                            try:
                                addrs.append(socket.inet_ntop(socket.AF_INET6, a))
                            except Exception:
                                pass
                    for ip in addrs:
                        self.out.append(
                            {
                                "ip": ip,
                                "mac": None,
                                "hostname": getattr(info, "server", None),
                                "service": self.stype,
                                "source": "mdns",
                            }
                        )
                except Exception as e:
                    logger.debug("mDNS resolve error for %s: %s", name, e)

            def update_service(self, zc, type_, name):
                return

            def remove_service(self, zc, type_, name):
                return

        zc = Zeroconf()
        try:
            found: list[dict] = []
            type_listener = _TypeListener()
            ServiceBrowser(zc, "_services._dns-sd._udp.local.", type_listener)  # type: ignore[arg-type]

            import time as _time

            deadline = _time.time() + t / 2
            while _time.time() < deadline:
                _time.sleep(0.1)

            service_types = list(type_listener.types)
            if not service_types:
                service_types = [
                    "_http._tcp.local.",
                    "_workstation._tcp.local.",
                    "_ssh._tcp.local.",
                ]

            browsers: list[ServiceBrowser] = []
            listeners: list[_InstanceListener] = []
            for st in service_types[:10]:
                lst = _InstanceListener(zc, st, found)
                listeners.append(lst)
                browsers.append(ServiceBrowser(zc, st, lst))  # type: ignore[arg-type]

            deadline = _time.time() + max(0.2, t / 2)
            while _time.time() < deadline:
                _time.sleep(0.1)

            return found
        finally:
            try:
                zc.close()
            except Exception:
                pass

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
    _cidr_val = getattr(settings, "NETWORK_CIDR", "") if cidr is None else cidr
    cidr = _cidr_val.strip() if isinstance(_cidr_val, str) and _cidr_val else None
    _iface_val = (
        getattr(settings, "INTERFACE", None) if interface is None else interface
    )
    iface: Optional[str] = (
        _iface_val.strip() if isinstance(_iface_val, str) and _iface_val else None
    )

    if not cidr:
        # Auto-detect first non-loopback IPv4 interface network
        pairs = interface_cidrs()
        if pairs:
            # If user supplied INTERFACE, try to find matching CIDR
            if iface:
                for name, c in pairs:
                    if name == iface:
                        cidr = c
                        break
            # Fallback to first detected
            if not cidr:
                cidr = pairs[0][1]
    # Final fallback if still not set
    if not cidr:
        cidr = "192.168.1.0/24"

    # Run ARP scan
    logger.info("Starting ARP scan: cidr=%s iface=%s", cidr, iface)
    devices = await arp_scan(cidr, interface=iface, timeout=arp_timeout)
    seen_ips: Set[str] = {d["ip"] for d in devices if "ip" in d}

    # ICMP ping sweep to catch hosts that didn't answer ARP (e.g., some stacks)
    try:
        alive_ips = await ping_sweep(cidr, timeout=ping_timeout)
    except Exception:
        alive_ips = []

    for ip in alive_ips:
        if ip not in seen_ips:
            devices.append({"ip": ip, "mac": None, "source": "icmp"})
            seen_ips.add(ip)

    # mDNS discovery
    try:
        mdns = await mdns_discover(timeout=2.5)
        for entry in mdns:
            ip = entry.get("ip")
            if ip and ip not in seen_ips:
                devices.append(entry)
                seen_ips.add(ip)
    except Exception as e:
        logger.debug("mDNS discover failed: %s", e)

    return devices
