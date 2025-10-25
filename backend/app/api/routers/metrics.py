from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/metrics/latency")
async def get_latency(
    device_id: str, limit: int = 100, start: str = "-1h", request: Request = None # type: ignore
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
        return {"device_id": device_id, "points": [], "error": str(e)}
