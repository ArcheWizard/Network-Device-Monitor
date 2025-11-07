import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_metrics_summary_no_database():
    """Test metrics summary when database is unavailable."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Ensure no repo in app state
        original_repo = getattr(app.state, "inventory_repo", None)
        app.state.inventory_repo = None

        r = await ac.get("/api/metrics/summary")
        assert r.status_code == 200
        data = r.json()

        assert data["total_devices"] == 0
        assert data["devices_up"] == 0
        assert data["devices_down"] == 0
        assert data["devices_unknown"] == 0
        assert data["avg_latency_ms"] is None
        assert data["max_latency_ms"] is None
        assert data["total_packet_loss"] is None

        # Restore original repo
        app.state.inventory_repo = original_repo


@pytest.mark.asyncio
async def test_metrics_summary_with_devices():
    """Test metrics summary with devices."""

    # Mock repository with test data
    class MockRepo:
        async def list_devices(self):
            return [
                {
                    "id": "device1",
                    "ip": "192.168.1.10",
                    "mac": "aa:bb:cc:dd:ee:01",
                    "hostname": "device1",
                    "vendor": "Vendor1",
                    "device_type": None,
                    "status": "up",
                    "first_seen": 1699000000,
                    "last_seen": 1699001000,
                    "tags": {},
                },
                {
                    "id": "device2",
                    "ip": "192.168.1.11",
                    "mac": "aa:bb:cc:dd:ee:02",
                    "hostname": "device2",
                    "vendor": "Vendor2",
                    "device_type": None,
                    "status": "down",
                    "first_seen": 1699000000,
                    "last_seen": 1699001000,
                    "tags": {},
                },
                {
                    "id": "device3",
                    "ip": "192.168.1.12",
                    "mac": "aa:bb:cc:dd:ee:03",
                    "hostname": "device3",
                    "vendor": "Vendor3",
                    "device_type": None,
                    "status": "up",
                    "first_seen": 1699000000,
                    "last_seen": 1699001000,
                    "tags": {},
                },
                {
                    "id": "device4",
                    "ip": "192.168.1.13",
                    "mac": "aa:bb:cc:dd:ee:04",
                    "hostname": "device4",
                    "vendor": "Vendor4",
                    "device_type": None,
                    "status": None,  # Unknown status
                    "first_seen": 1699000000,
                    "last_seen": 1699001000,
                    "tags": {},
                },
            ]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Inject mock repo
        app.state.inventory_repo = MockRepo()

        r = await ac.get("/api/metrics/summary")
        assert r.status_code == 200
        data = r.json()

        assert data["total_devices"] == 4
        assert data["devices_up"] == 2
        assert data["devices_down"] == 1
        assert data["devices_unknown"] == 1
        # Without InfluxDB, these should be None
        assert data["avg_latency_ms"] is None
        assert data["max_latency_ms"] is None
        assert data["total_packet_loss"] is None


@pytest.mark.asyncio
async def test_metrics_summary_with_influx_data():
    """Test metrics summary with InfluxDB data."""

    # Mock repository
    class MockRepo:
        async def list_devices(self):
            return [
                {
                    "id": "device1",
                    "ip": "192.168.1.10",
                    "mac": "aa:bb:cc:dd:ee:01",
                    "hostname": "device1",
                    "vendor": "Vendor1",
                    "device_type": None,
                    "status": "up",
                    "first_seen": 1699000000,
                    "last_seen": 1699001000,
                    "tags": {},
                },
                {
                    "id": "device2",
                    "ip": "192.168.1.11",
                    "mac": "aa:bb:cc:dd:ee:02",
                    "hostname": "device2",
                    "vendor": "Vendor2",
                    "device_type": None,
                    "status": "up",
                    "first_seen": 1699000000,
                    "last_seen": 1699001000,
                    "tags": {},
                },
            ]

    # Mock InfluxDB writer
    class MockInfluxWriter:
        async def query_metrics(self, measurement, device_id, start, limit):
            # Return mock metrics
            if device_id == "device1":
                return [
                    {"ts": 1699000000, "ms": 10.5, "loss": 0.0},
                    {"ts": 1699000060, "ms": 12.3, "loss": 0.0},
                ]
            elif device_id == "device2":
                return [
                    {"ts": 1699000000, "ms": 25.0, "loss": 0.1},
                    {"ts": 1699000060, "ms": 30.0, "loss": 0.05},
                ]
            return []

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Inject mock repo and influx writer
        app.state.inventory_repo = MockRepo()
        app.state.influx_writer = MockInfluxWriter()

        r = await ac.get("/api/metrics/summary")
        assert r.status_code == 200
        data = r.json()

        assert data["total_devices"] == 2
        assert data["devices_up"] == 2
        assert data["devices_down"] == 0
        assert data["devices_unknown"] == 0

        # With InfluxDB data
        assert data["avg_latency_ms"] is not None
        assert data["max_latency_ms"] is not None
        assert data["total_packet_loss"] is not None

        # Check calculated values (approximate)
        # avg = (10.5 + 12.3 + 25.0 + 30.0) / 4 = 19.45
        assert 19.0 < data["avg_latency_ms"] < 20.0
        # max = 30.0
        assert data["max_latency_ms"] == 30.0
        # avg loss = (0.0 + 0.0 + 0.1 + 0.05) / 4 = 0.0375
        assert 0.03 < data["total_packet_loss"] < 0.04
