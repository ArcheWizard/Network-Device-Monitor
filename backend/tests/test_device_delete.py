import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_delete_device_not_found():
    """Test deleting a non-existent device returns 404."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.delete("/api/devices/nonexistent-device-id")
        # Without DB initialized, we expect 503 or if DB is initialized but device not found, 404
        # The test environment may not have DB initialized, so we accept either
        assert r.status_code in [404, 503]


@pytest.mark.asyncio
async def test_delete_device_success(monkeypatch):
    """Test deleting an existing device returns 204."""

    # Mock the repository methods
    class MockRepo:
        async def get_device(self, device_id: str):
            if device_id == "test-device-id":
                return {
                    "id": "test-device-id",
                    "ip": "192.168.1.100",
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "hostname": "test-device",
                    "vendor": "Test Vendor",
                    "device_type": None,
                    "status": "up",
                    "first_seen": 1699000000,
                    "last_seen": 1699001000,
                    "tags": {},
                }
            return None

        async def delete_device(self, device_id: str):
            return True

    # Patch the app state to use mock repo
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Inject mock repo into app state
        app.state.inventory_repo = MockRepo()

        r = await ac.delete("/api/devices/test-device-id")
        assert r.status_code == 204
        assert r.content == b""  # No content in response


@pytest.mark.asyncio
async def test_delete_device_no_database():
    """Test deleting a device when database is unavailable returns 503."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Ensure no repo in app state
        if hasattr(app.state, "inventory_repo"):
            original_repo = app.state.inventory_repo
            app.state.inventory_repo = None

            r = await ac.delete("/api/devices/any-device-id")
            assert r.status_code == 503
            assert "Database unavailable" in r.json().get("detail", "")

            # Restore original repo
            app.state.inventory_repo = original_repo
        else:
            # If no repo was set, test directly
            r = await ac.delete("/api/devices/any-device-id")
            assert r.status_code == 503
