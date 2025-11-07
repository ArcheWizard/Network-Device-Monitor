import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_discovery_scan_endpoint(monkeypatch):
    # Monkeypatch the discovery.scan used by the router to avoid real network ops
    import app.api.routers.devices as devices_router

    async def fake_scan(**kwargs):  # Accept keyword arguments
        return [{"ip": "192.0.2.10", "mac": "aa:bb:cc:dd:ee:ff", "source": "arp"}]

    # Mock identification to avoid real lookups
    async def fake_identify(**kwargs):
        return {
            "vendor": "Test Vendor",
            "hostname": "test.local",
            "description": None,
        }

    monkeypatch.setattr(devices_router.discovery, "scan", fake_scan)

    from app.services import identification

    monkeypatch.setattr(identification, "identify_device", fake_identify)

    # Mock the repo or set persist=False to skip persistence
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Test with persist=False to avoid needing a mock repo
        r = await ac.post("/api/devices/discover", json={"persist": False})
        assert r.status_code == 200
        data = r.json()
        assert "devices" in data
        assert data["count"] == 1
        assert data["devices"][0]["ip"] == "192.0.2.10"
        assert data["persisted"] is False
