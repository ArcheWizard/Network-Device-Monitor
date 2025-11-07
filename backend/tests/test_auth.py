"""Tests for authentication and authorization.

This module tests user registration, login, token validation,
and role-based access control.
"""

import pytest
import pytest_asyncio
from app.main import app
from app.storage.sqlite import init_sqlite
from app.utils.auth import create_access_token, hash_password
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture(scope="function")
async def test_app():
    """Initialize app with in-memory database for testing."""
    device_repo, user_repo = await init_sqlite(":memory:")
    app.state.inventory_repo = device_repo
    app.state.user_repo = user_repo

    # Enable authentication for tests
    from app.config import settings

    settings.REQUIRE_AUTH = True

    yield app

    # Reset after tests
    settings.REQUIRE_AUTH = False


@pytest.fixture
def test_user_data():
    """Test user data fixture."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123",
        "full_name": "Test User",
        "role": "viewer",
    }


@pytest.fixture
def admin_user_data():
    """Admin user data fixture."""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "AdminPass123",
        "full_name": "Admin User",
        "role": "admin",
    }


@pytest.mark.asyncio
async def test_register_user_success(test_app, test_user_data):
    """Test successful user registration."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()

        assert "user" in data
        assert data["user"]["username"] == test_user_data["username"]
        assert data["user"]["email"] == test_user_data["email"]
        assert data["user"]["role"] == test_user_data["role"]
        assert data["user"]["is_active"] is True
        assert "hashed_password" not in data["user"]
        assert "message" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(test_app, test_user_data):
    """Test registration with duplicate username."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register first user
        await client.post("/api/auth/register", json=test_user_data)

        # Try to register with same username
        response = await client.post("/api/auth/register", json=test_user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_email(test_app, test_user_data):
    """Test registration with duplicate email."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register first user
        await client.post("/api/auth/register", json=test_user_data)

        # Try to register with different username but same email
        test_user_data["username"] = "anotheruser"
        response = await client.post("/api/auth/register", json=test_user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_weak_password(test_app):
    """Test registration with weak password."""
    weak_user_data = {
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "weak",  # Too short, no uppercase, no digit
        "role": "viewer",
    }

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=weak_user_data)
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_invalid_username(test_app):
    """Test registration with invalid username."""
    invalid_user_data = {
        "username": "ab",  # Too short
        "email": "test@example.com",
        "password": "TestPass123",
        "role": "viewer",
    }

    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/register", json=invalid_user_data)
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(test_app, test_user_data):
    """Test successful login."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register user
        await client.post("/api/auth/register", json=test_user_data)

        # Login
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
        }
        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        assert "user" in data
        assert "token" in data
        assert data["user"]["username"] == test_user_data["username"]
        assert data["token"]["access_token"]
        assert data["token"]["token_type"] == "bearer"
        assert data["token"]["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_wrong_password(test_app, test_user_data):
    """Test login with wrong password."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register user
        await client.post("/api/auth/register", json=test_user_data)

        # Login with wrong password
        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword123",
        }
        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(test_app):
    """Test login with non-existent username."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        login_data = {
            "username": "nonexistent",
            "password": "TestPass123",
        }
        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_current_user(test_app, test_user_data):
    """Test getting current user info with valid token."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register and login
        await client.post("/api/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["token"]["access_token"]

        # Get current user
        response = await client.get(
            "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(test_app):
    """Test getting current user with invalid token."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_no_token(test_app):
    """Test getting current user without token."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        response = await client.get("/api/auth/me")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_as_admin(test_app, admin_user_data, test_user_data):
    """Test listing users as admin."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register admin and regular user
        await client.post("/api/auth/register", json=admin_user_data)
        await client.post("/api/auth/register", json=test_user_data)

        # Login as admin
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": admin_user_data["username"],
                "password": admin_user_data["password"],
            },
        )
        token = login_response.json()["token"]["access_token"]

        # List users
        response = await client.get(
            "/api/auth/users", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 2
        usernames = [u["username"] for u in users]
        assert admin_user_data["username"] in usernames
        assert test_user_data["username"] in usernames


@pytest.mark.asyncio
async def test_list_users_as_viewer(test_app, test_user_data):
    """Test listing users as non-admin (should fail)."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register and login as viewer
        await client.post("/api/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["token"]["access_token"]

        # Try to list users
        response = await client.get(
            "/api/auth/users", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "permissions" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_user_as_admin(test_app, admin_user_data, test_user_data):
    """Test updating user as admin."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register users
        await client.post("/api/auth/register", json=admin_user_data)
        user_response = await client.post("/api/auth/register", json=test_user_data)
        user_id = user_response.json()["user"]["id"]

        # Login as admin
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": admin_user_data["username"],
                "password": admin_user_data["password"],
            },
        )
        token = login_response.json()["token"]["access_token"]

        # Update user
        update_data = {
            "role": "operator",
            "full_name": "Updated Name",
        }
        response = await client.patch(
            f"/api/auth/users/{user_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["role"] == "operator"
        assert updated_user["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user_as_admin(test_app, admin_user_data, test_user_data):
    """Test deleting user as admin."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register users
        await client.post("/api/auth/register", json=admin_user_data)
        user_response = await client.post("/api/auth/register", json=test_user_data)
        user_id = user_response.json()["user"]["id"]

        # Login as admin
        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": admin_user_data["username"],
                "password": admin_user_data["password"],
            },
        )
        token = login_response.json()["token"]["access_token"]

        # Delete user
        response = await client.delete(
            f"/api/auth/users/{user_id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

        # Verify user is deleted
        get_response = await client.get(
            f"/api/auth/users/{user_id}", headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_self_as_admin(test_app, admin_user_data):
    """Test admin cannot delete their own account."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app), base_url="http://test"
    ) as client:
        # Register and login as admin
        admin_response = await client.post("/api/auth/register", json=admin_user_data)
        admin_id = admin_response.json()["user"]["id"]

        login_response = await client.post(
            "/api/auth/login",
            json={
                "username": admin_user_data["username"],
                "password": admin_user_data["password"],
            },
        )
        token = login_response.json()["token"]["access_token"]

        # Try to delete self
        response = await client.delete(
            f"/api/auth/users/{admin_id}", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403
        assert "cannot delete" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_token_expiration():
    """Test token contains expiration time."""
    from datetime import timedelta

    token = create_access_token(
        data={"sub": "testuser", "role": "viewer"}, expires_delta=timedelta(minutes=30)
    )

    assert token
    assert isinstance(token, str)


def test_password_hashing():
    """Test password hashing and verification."""
    from app.utils.auth import verify_password

    password = "TestPass123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
