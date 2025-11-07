"""Device monitoring service for health checks and metrics collection.

Implements ping-based monitoring to track latency, packet loss, and device status.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..models.metrics import LatencyMetric

logger = logging.getLogger(__name__)


async def ping_device(ip: str, count: int = 4, timeout: float = 2.0) -> Dict[str, Any]:
    """Ping device and return metrics.

    Args:
        ip: IP address to ping
        count: Number of ping packets to send
        timeout: Timeout in seconds per ping

    Returns:
        Dictionary with keys: ip, status, latency_avg, latency_min, latency_max, packet_loss
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping",
            "-c",
            str(count),
            "-W",
            str(int(timeout)),
            ip,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            logger.debug("Ping failed for %s: return code %d", ip, proc.returncode)
            return {
                "ip": ip,
                "status": "down",
                "latency_avg": None,
                "latency_min": None,
                "latency_max": None,
                "packet_loss": 100.0,
            }

        output = stdout.decode()

        # Parse packet loss: "4 packets transmitted, 4 received, 0% packet loss"
        loss_match = re.search(r"(\d+)% packet loss", output)
        packet_loss = float(loss_match.group(1)) if loss_match else 0.0

        # Parse latency: "rtt min/avg/max/mdev = 0.123/0.456/0.789/0.012 ms"
        latency_match = re.search(
            r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/[\d.]+ ms", output
        )

        if latency_match:
            latency_min = float(latency_match.group(1))
            latency_avg = float(latency_match.group(2))
            latency_max = float(latency_match.group(3))
        else:
            # Fallback: if we can't parse but returncode was 0, assume minimal latency
            latency_min = latency_avg = latency_max = 0.0

        return {
            "ip": ip,
            "status": "up" if packet_loss < 100.0 else "down",
            "latency_avg": latency_avg,
            "latency_min": latency_min,
            "latency_max": latency_max,
            "packet_loss": packet_loss,
        }

    except Exception as e:
        logger.error("Ping error for %s: %s", ip, e)
        return {
            "ip": ip,
            "status": "error",
            "latency_avg": None,
            "latency_min": None,
            "latency_max": None,
            "packet_loss": 100.0,
        }


async def create_latency_metric(
    device_id: str, ip: str, count: int = 4, timeout: float = 2.0
) -> Optional[LatencyMetric]:
    """Create a complete LatencyMetric model from ping results.

    This function wraps ping_device and returns a LatencyMetric model
    that includes all fields as documented in the architecture.

    Args:
        device_id: Device identifier (MAC address or IP)
        ip: IP address to ping
        count: Number of ping packets to send
        timeout: Timeout in seconds per ping

    Returns:
        LatencyMetric model or None if ping failed completely
    """
    ping_result = await ping_device(ip=ip, count=count, timeout=timeout)

    # If device is down or error, we can't create a valid metric
    if ping_result["status"] in ["down", "error"] or ping_result["latency_avg"] is None:
        return None

    # Calculate packets received from packet loss percentage
    packets_sent = count
    packet_loss_ratio = ping_result["packet_loss"] / 100.0
    packets_received = int(packets_sent * (1 - packet_loss_ratio))

    return LatencyMetric(
        device_id=device_id,
        timestamp=datetime.now(timezone.utc),
        latency_ms=ping_result["latency_avg"],
        packet_loss=packet_loss_ratio,  # Convert percentage to ratio (0.0 to 1.0)
        packets_sent=packets_sent,
        packets_received=packets_received,
    )


async def tick_all():
    """Monitor all devices (placeholder for scheduler integration)."""
    # TODO: iterate devices and ping
    pass
