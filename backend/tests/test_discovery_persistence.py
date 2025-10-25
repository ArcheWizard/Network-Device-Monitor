from httpx import AsyncClient, ASGITransport
from app.main import app
from app.storage.sqlite import init_sqlite
import pytest


@pytest.mark.asyncio
async def test_discovery_scan_persists_to_repo(monkeypatch):
    """Test that discovery scan persists results to SQLite when persist=True."""
    import app.api.routers.devices as devices_router

    async def fake_scan(**kwargs):
        return [
            {"ip": "192.0.2.10", "mac": "aa:bb:cc:dd:ee:ff", "source": "arp"},
            {
                "ip": "192.0.2.11",
                "mac": "11:22:33:44:55:66",
                "hostname": "test.local",
                "source": "mdns",
            },
        ]

    # Mock identification to avoid OUI warnings
    async def fake_identify(**kwargs):
        return {
            "vendor": None,
            "hostname": kwargs.get("mac", "").replace(":", ""),
            "description": None,
            "uptime": None,
            "contact": None,
            "location": None,
            "object_id": None,
        }

    monkeypatch.setattr(devices_router.discovery, "scan", fake_scan)

    # Initialize SQLite repo for the app
    repo = await init_sqlite(":memory:")
    app.state.inventory_repo = repo

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Mock identification at the service level
        from app.services import identification

        monkeypatch.setattr(identification, "identify_device", fake_identify)

        # Scan with persist=True (default)
        r = await ac.post("/api/discovery/scan", json={"persist": True})
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 2
        assert data["persisted"] is True

        # Check devices are in repo
        r2 = await ac.get("/api/devices")
        assert r2.status_code == 200
        devices = r2.json()
        assert len(devices) >= 2
        device_ids = {d["id"] for d in devices}
        assert "aa:bb:cc:dd:ee:ff" in device_ids
        assert "11:22:33:44:55:66" in device_ids

        # Get by ID
        r3 = await ac.get("/api/devices/aa:bb:cc:dd:ee:ff")
        assert r3.status_code == 200
        dev = r3.json()
        assert dev["ip"] == "192.0.2.10"
        assert dev["mac"] == "aa:bb:cc:dd:ee:ff"
        devices = r2.json()
        assert len(devices) >= 2
        device_ids = {d["id"] for d in devices}
        assert "aa:bb:cc:dd:ee:ff" in device_ids
        assert "11:22:33:44:55:66" in device_ids

        # Get by ID
        r3 = await ac.get("/api/devices/aa:bb:cc:dd:ee:ff")
        assert r3.status_code == 200
        dev = r3.json()
        assert dev["ip"] == "192.0.2.10"
        assert dev["mac"] == "aa:bb:cc:dd:ee:ff"
