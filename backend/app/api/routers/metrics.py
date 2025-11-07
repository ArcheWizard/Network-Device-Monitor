from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class MetricsSummary(BaseModel):
    """Aggregate metrics summary for all devices."""

    total_devices: int
    devices_up: int
    devices_down: int
    devices_unknown: int
    avg_latency_ms: Optional[float] = None
    max_latency_ms: Optional[float] = None
    total_packet_loss: Optional[float] = None


@router.get("/metrics/latency")
async def get_latency(
    device_id: str,
    limit: int = 100,
    start: str = "-1h",
    request: Request = None,  # type: ignore
):
    """Get latency metrics for a device from InfluxDB.

    Args:
        device_id: Device identifier
        limit: Maximum number of points to return
        start: Start time (InfluxDB duration format, e.g., "-1h", "-24h")
        request: FastAPI request object

    Returns:
        Dictionary with device_id and list of metric points
    """
    influx_writer = (
        getattr(request.app.state, "influx_writer", None) if request else None
    )

    if not influx_writer:
        return {
            "device_id": device_id,
            "points": [],
            "error": "InfluxDB not configured",
        }

    try:
        points = await influx_writer.query_metrics(
            measurement="latency", device_id=device_id, start=start, limit=limit
        )

        return {"device_id": device_id, "points": points, "count": len(points)}
    except Exception as e:
        import logging

        logging.error("Failed to query metrics for %s: %s", device_id, e)
        return {
            "device_id": device_id,
            "points": [],
            "error": "An internal error has occurred.",
        }


@router.get("/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary(request: Request = None):  # type: ignore
    """Get aggregate metrics for all devices.

    Returns:
        Dictionary with summary statistics including:
        - Device counts by status
        - Average and max latency (if available)
        - Total packet loss (if available)
    """
    repo = getattr(request.app.state, "inventory_repo", None) if request else None

    if not repo:
        return MetricsSummary(
            total_devices=0,
            devices_up=0,
            devices_down=0,
            devices_unknown=0,
            avg_latency_ms=None,
            max_latency_ms=None,
            total_packet_loss=None,
        )

    # Get all devices
    devices = await repo.list_devices()

    # Calculate device statistics
    total = len(devices)
    up = sum(1 for d in devices if d.get("status") == "up")
    down = sum(1 for d in devices if d.get("status") == "down")
    unknown = total - up - down

    # Get recent metrics from InfluxDB if available
    influx_writer = (
        getattr(request.app.state, "influx_writer", None) if request else None
    )
    avg_latency = None
    max_latency = None
    total_loss = None

    if influx_writer:
        try:
            # Query recent metrics for all devices (last hour)
            latencies = []
            losses = []

            for device in devices:
                device_id = device.get("id")
                if not device_id:
                    continue

                try:
                    points = await influx_writer.query_metrics(
                        measurement="latency",
                        device_id=device_id,
                        start="-1h",
                        limit=10,
                    )

                    for point in points:
                        if "ms" in point and point["ms"] is not None:
                            latencies.append(point["ms"])
                        if "loss" in point and point["loss"] is not None:
                            losses.append(point["loss"])
                except Exception:
                    # Skip devices with query errors
                    continue

            # Calculate aggregates
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)

            if losses:
                total_loss = sum(losses) / len(losses)

        except Exception as e:
            import logging

            logging.warning("Failed to calculate metrics summary: %s", e)

    return MetricsSummary(
        total_devices=total,
        devices_up=up,
        devices_down=down,
        devices_unknown=unknown,
        avg_latency_ms=avg_latency,
        max_latency_ms=max_latency,
        total_packet_loss=total_loss,
    )
