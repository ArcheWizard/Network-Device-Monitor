"""InfluxDB metrics writer/reader for time-series data.

Stores device monitoring metrics (latency, packet loss, bandwidth) with timestamps.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Import InfluxDB client (optional dependency)
try:
    from influxdb_client.client.influxdb_client import InfluxDBClient  # type: ignore
    from influxdb_client.client.write.point import Point  # type: ignore
    from influxdb_client.domain.write_precision import WritePrecision  # type: ignore
    from influxdb_client.client.write_api import SYNCHRONOUS  # type: ignore

    INFLUX_AVAILABLE = True
except ImportError:
    logger.warning("influxdb-client not installed. Metrics storage will be disabled.")
    INFLUX_AVAILABLE = False


class InfluxMetricsWriter:
    """InfluxDB metrics writer for device monitoring data."""

    def __init__(self, url: str, token: str, org: str, bucket: str):
        """Initialize InfluxDB writer.

        Args:
            url: InfluxDB URL (e.g., http://localhost:8086)
            token: Authentication token
            org: Organization name
            bucket: Bucket name for metrics
        """
        if not INFLUX_AVAILABLE:
            raise RuntimeError("influxdb-client not available")

        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.client: Optional[InfluxDBClient] = None

    def connect(self):
        """Establish connection to InfluxDB."""
        if self.client is None:
            self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)  # type: ignore
            logger.info("Connected to InfluxDB at %s", self.url)

    def close(self):
        """Close InfluxDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("Closed InfluxDB connection")

    async def write_metric(
        self,
        measurement: str,
        tags: Dict[str, str],
        fields: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Write a metric point to InfluxDB.

        Args:
            measurement: Measurement name (e.g., "latency", "bandwidth")
            tags: Tag dictionary (e.g., {"device_id": "192.168.1.1"})
            fields: Field dictionary (e.g., {"ms": 12.4, "loss": 0.0})
            timestamp: Optional timestamp (defaults to now)

        Returns:
            True if write successful, False otherwise
        """
        if not INFLUX_AVAILABLE or not self.client:
            logger.debug("InfluxDB not available, skipping metric write")
            return False

        try:
            point = Point(measurement)  # type: ignore

            # Add tags
            for key, value in tags.items():
                point = point.tag(key, value)

            # Add fields
            for key, value in fields.items():
                if value is not None:
                    point = point.field(key, value)

            # Add timestamp
            if timestamp:
                point = point.time(timestamp, WritePrecision.S)  # type: ignore

            # Write to InfluxDB
            write_api = self.client.write_api(write_options=SYNCHRONOUS)  # type: ignore
            write_api.write(bucket=self.bucket, org=self.org, record=point)

            logger.debug("Wrote metric: %s %s %s", measurement, tags, fields)
            return True

        except Exception as e:
            logger.error("Failed to write metric to InfluxDB: %s", e)
            return False

    async def query_metrics(
        self, measurement: str, device_id: str, start: str = "-1h", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query metrics from InfluxDB.

        Args:
            measurement: Measurement name
            device_id: Device identifier
            start: Start time (InfluxDB duration format, e.g., "-1h", "-24h")
            limit: Maximum number of points to return

        Returns:
            List of metric points with timestamp and values
        """
        if not INFLUX_AVAILABLE or not self.client:
            logger.debug("InfluxDB not available, returning empty results")
            return []

        try:
            query = f"""
                from(bucket: "{self.bucket}")
                |> range(start: {start})
                |> filter(fn: (r) => r["_measurement"] == "{measurement}")
                |> filter(fn: (r) => r["device_id"] == "{device_id}")
                |> limit(n: {limit})
                |> sort(columns: ["_time"], desc: true)
            """

            query_api = self.client.query_api()
            tables = query_api.query(query, org=self.org)

            # Parse results
            points = []
            for table in tables:
                for record in table.records:
                    point = {
                        "time": record.get_time().isoformat()
                        if record.get_time()
                        else None,
                        "field": record.get_field(),
                        "value": record.get_value(),
                    }
                    points.append(point)

            return points

        except Exception as e:
            logger.error("Failed to query metrics from InfluxDB: %s", e)
            return []


# Global writer instance
_writer: Optional[InfluxMetricsWriter] = None


def init_influx(
    url: str, token: str, org: str, bucket: str
) -> Optional[InfluxMetricsWriter]:
    """Initialize InfluxDB writer.

    Args:
        url: InfluxDB URL
        token: Authentication token
        org: Organization name
        bucket: Bucket name

    Returns:
        InfluxMetricsWriter instance if successful, None otherwise
    """
    global _writer

    if not INFLUX_AVAILABLE:
        logger.warning("InfluxDB client not available, metrics will not be stored")
        return None

    try:
        _writer = InfluxMetricsWriter(url, token, org, bucket)
        _writer.connect()
        return _writer
    except Exception as e:
        logger.error("Failed to initialize InfluxDB: %s", e)
        return None


def get_writer() -> Optional[InfluxMetricsWriter]:
    """Get global InfluxDB writer instance."""
    return _writer
