import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_list_devices_with_status_filter():
    """Test filtering devices by status."""

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
            ]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Inject mock repo
        app.state.inventory_repo = MockRepo()

        # Test filtering by "up" status
        r = await ac.get("/api/devices?status=up")
        assert r.status_code == 200
        devices = r.json()
        assert len(devices) == 2
        assert all(d["status"] == "up" for d in devices)

        # Test filtering by "down" status
        r = await ac.get("/api/devices?status=down")
        assert r.status_code == 200
        devices = r.json()
        assert len(devices) == 1
        assert devices[0]["status"] == "down"

        # Test "all" status (should return all devices)
        r = await ac.get("/api/devices?status=all")
        assert r.status_code == 200
        devices = r.json()
        assert len(devices) == 3


@pytest.mark.asyncio
async def test_list_devices_with_pagination():
    """Test pagination with limit and offset."""

    # Mock repository with test data
    class MockRepo:
        async def list_devices(self):
            return [
                {
                    "id": f"device{i}",
                    "ip": f"192.168.1.{10+i}",
                    "mac": f"aa:bb:cc:dd:ee:{i:02d}",
                    "hostname": f"device{i}",
                    "vendor": f"Vendor{i}",
                    "device_type": None,
                    "status": "up",
                    "first_seen": 1699000000,
                    "last_seen": 1699001000,
                    "tags": {},
                }
                for i in range(15)
            ]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Inject mock repo
        app.state.inventory_repo = MockRepo()

        # Test limit
        r = await ac.get("/api/devices?limit=5")
        assert r.status_code == 200
        devices = r.json()
        assert len(devices) == 5
        assert devices[0]["id"] == "device0"

        # Test offset
        r = await ac.get("/api/devices?offset=10&limit=5")
        assert r.status_code == 200
        devices = r.json()
        assert len(devices) == 5
        assert devices[0]["id"] == "device10"

        # Test offset + limit beyond available data
        r = await ac.get("/api/devices?offset=10&limit=10")
        assert r.status_code == 200
        devices = r.json()
        assert len(devices) == 5  # Only 5 devices left after offset 10


@pytest.mark.asyncio
async def test_list_devices_combined_filters():
    """Test combining status filter with pagination."""

    # Mock repository with test data
    class MockRepo:
        async def list_devices(self):
            return [
                {
                    "id": f"device{i}",
                    "ip": f"192.168.1.{10+i}",
                    "mac": f"aa:bb:cc:dd:ee:{i:02d}",
                    "hostname": f"device{i}",
                    "vendor": f"Vendor{i}",
                    "device_type": None,
                    "status": "up" if i % 2 == 0 else "down",
                    "first_seen": 1699000000,
                    "last_seen": 1699001000,
                    "tags": {},
                }
                for i in range(10)
            ]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Inject mock repo
        app.state.inventory_repo = MockRepo()

        # Test status filter + pagination
        r = await ac.get("/api/devices?status=up&limit=2&offset=0")
        assert r.status_code == 200
        devices = r.json()
        assert len(devices) == 2
        assert all(d["status"] == "up" for d in devices)
        assert devices[0]["id"] == "device0"
        assert devices[1]["id"] == "device2"
