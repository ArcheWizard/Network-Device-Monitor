from datetime import datetime

from pydantic import BaseModel


class LatencyMetric(BaseModel):
    """Complete latency metric model matching architecture documentation.

    This model includes all fields as specified in docs/human/11-architecture.md
    and is used for internal processing and storage.
    """

    device_id: str
    timestamp: datetime
    latency_ms: float
    packet_loss: float  # 0.0 to 1.0 ratio
    packets_sent: int
    packets_received: int


class LatencyPoint(BaseModel):
    """Simplified latency point for API responses.

    This is a lighter version used for API responses and time-series data
    where the device_id and packet counts are handled separately.
    """

    ts: int  # Unix timestamp
    ms: float  # Latency in milliseconds
    loss: float  # Packet loss ratio (0.0 to 1.0)
