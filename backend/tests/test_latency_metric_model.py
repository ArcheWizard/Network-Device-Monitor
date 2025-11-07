from datetime import datetime, timezone

import pytest
from app.models.metrics import LatencyMetric, LatencyPoint


def test_latency_metric_model():
    """Test the complete LatencyMetric model."""
    metric = LatencyMetric(
        device_id="aa:bb:cc:dd:ee:ff",
        timestamp=datetime.now(timezone.utc),
        latency_ms=12.5,
        packet_loss=0.25,  # 25% loss
        packets_sent=4,
        packets_received=3,
    )

    assert metric.device_id == "aa:bb:cc:dd:ee:ff"
    assert metric.latency_ms == 12.5
    assert metric.packet_loss == 0.25
    assert metric.packets_sent == 4
    assert metric.packets_received == 3
    assert isinstance(metric.timestamp, datetime)


def test_latency_metric_validation():
    """Test that LatencyMetric requires all fields."""
    # Missing fields should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        LatencyMetric(
            device_id="test",
            timestamp=datetime.now(timezone.utc),
            # Missing other required fields
        )


def test_latency_point_model():
    """Test the simplified LatencyPoint model."""
    point = LatencyPoint(
        ts=1699000000,
        ms=15.3,
        loss=0.1,
    )

    assert point.ts == 1699000000
    assert point.ms == 15.3
    assert point.loss == 0.1


def test_latency_models_coexist():
    """Test that both LatencyMetric and LatencyPoint can be used together."""
    # Create a full metric
    metric = LatencyMetric(
        device_id="device1",
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        latency_ms=10.0,
        packet_loss=0.0,
        packets_sent=4,
        packets_received=4,
    )

    # Create a simplified point (e.g., for API response)
    point = LatencyPoint(
        ts=int(metric.timestamp.timestamp()),
        ms=metric.latency_ms,
        loss=metric.packet_loss,
    )

    # Verify they represent the same data
    assert point.ms == metric.latency_ms
    assert point.loss == metric.packet_loss
