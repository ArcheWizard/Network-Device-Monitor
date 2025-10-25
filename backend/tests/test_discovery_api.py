from httpx import AsyncClient, ASGITransport
from app.main import app
import pytest


@pytest.mark.asyncio
async def test_discovery_scan_endpoint(monkeypatch):
    # Monkeypatch the discovery.scan used by the router to avoid real network ops
    import app.api.routers.devices as devices_router

    async def fake_scan(**kwargs):  # Accept keyword arguments
        return [{"ip": "192.0.2.10", "mac": "aa:bb:cc:dd:ee:ff", "source": "arp"}]

    monkeypatch.setattr(devices_router.discovery, "scan", fake_scan)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.post("/api/discovery/scan")
        assert r.status_code == 200
        data = r.json()
        assert "devices" in data
        assert data["count"] == 1
        assert data["devices"][0]["ip"] == "192.0.2.10"
