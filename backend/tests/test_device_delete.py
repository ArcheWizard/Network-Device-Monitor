import pytest
import pytest_asyncio
from app.main import app
from app.storage.sqlite import init_sqlite
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture(scope="function")
async def test_app_with_auth():
    """Initialize app with in-memory database and authentication enabled."""
    device_repo, user_repo = await init_sqlite(":memory:")
    app.state.inventory_repo = device_repo
    app.state.user_repo = user_repo

    # Enable authentication for tests
    from app.config import settings

    original_auth = settings.REQUIRE_AUTH
    settings.REQUIRE_AUTH = True

    yield app

    # Reset after tests
    settings.REQUIRE_AUTH = original_auth


@pytest_asyncio.fixture
async def operator_token(test_app_with_auth):
    """Create an operator user and return their token."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app_with_auth), base_url="http://test"
    ) as client:
        # Register operator
        operator_data = {
            "username": "operator",
            "email": "operator@example.com",
            "password": "OperatorPass123",
            "role": "operator",
        }
        await client.post("/api/auth/register", json=operator_data)

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": operator_data["username"],
                "password": operator_data["password"],
            },
        )
        return login_response.json()["token"]["access_token"]


@pytest_asyncio.fixture
async def viewer_token(test_app_with_auth):
    """Create a viewer user and return their token."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app_with_auth), base_url="http://test"
    ) as client:
        # Register viewer
        viewer_data = {
            "username": "viewer",
            "email": "viewer@example.com",
            "password": "ViewerPass123",
            "role": "viewer",
        }
        await client.post("/api/auth/register", json=viewer_data)

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": viewer_data["username"],
                "password": viewer_data["password"],
            },
        )
        return login_response.json()["token"]["access_token"]


@pytest.mark.asyncio
async def test_delete_device_no_auth(test_app_with_auth):
    """Test deleting a device without authentication returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app_with_auth), base_url="http://test"
    ) as ac:
        r = await ac.delete("/api/devices/any-device-id")
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_delete_device_insufficient_permissions(test_app_with_auth, viewer_token):
    """Test deleting a device as viewer returns 403."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app_with_auth), base_url="http://test"
    ) as ac:
        r = await ac.delete(
            "/api/devices/any-device-id",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert r.status_code == 403
        assert "permissions" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_device_not_found(test_app_with_auth, operator_token):
    """Test deleting a non-existent device returns 404."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app_with_auth), base_url="http://test"
    ) as ac:
        r = await ac.delete(
            "/api/devices/nonexistent-device-id",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_device_success(test_app_with_auth, operator_token):
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

    # Inject mock repo into app state
    test_app_with_auth.state.inventory_repo = MockRepo()

    async with AsyncClient(
        transport=ASGITransport(app=test_app_with_auth), base_url="http://test"
    ) as ac:
        r = await ac.delete(
            "/api/devices/test-device-id",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert r.status_code == 204
        assert r.content == b""  # No content in response


@pytest.mark.asyncio
async def test_delete_device_no_database(test_app_with_auth, operator_token):
    """Test deleting a device when database is unavailable returns 503."""
    # Temporarily remove the repo
    original_repo = test_app_with_auth.state.inventory_repo
    test_app_with_auth.state.inventory_repo = None

    async with AsyncClient(
        transport=ASGITransport(app=test_app_with_auth), base_url="http://test"
    ) as ac:
        r = await ac.delete(
            "/api/devices/any-device-id",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert r.status_code == 503
        assert "Database unavailable" in r.json().get("detail", "")

    # Restore original repo
    test_app_with_auth.state.inventory_repo = original_repo
