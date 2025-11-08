"""Tests for authentication manager."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.auth_manager import AuthManager


@pytest.fixture
def auth_manager():
    """Create auth manager for testing."""
    return AuthManager("http://test:8000")


@pytest.mark.asyncio
async def test_login_success(auth_manager):
    """Test successful login."""
    with patch.object(auth_manager, "_get_client") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test-token",
            "token_type": "bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_http.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_http

        with patch.object(auth_manager, "fetch_current_user", return_value=True):
            result = await auth_manager.login("testuser", "testpass")

        assert result is True
        assert auth_manager._token == "test-token"


@pytest.mark.asyncio
async def test_login_failure(auth_manager):
    """Test failed login."""
    with patch.object(auth_manager, "_get_client") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_http

        result = await auth_manager.login("baduser", "badpass")

        assert result is False
        assert auth_manager._token is None


@pytest.mark.asyncio
async def test_register_success(auth_manager):
    """Test successful registration."""
    with patch.object(auth_manager, "_get_client") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "user-1", "username": "newuser"}
        mock_response.raise_for_status = MagicMock()

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_http

        success, error = await auth_manager.register(
            "newuser", "test@example.com", "TestPass123!"
        )

        assert success is True
        assert error is None


@pytest.mark.asyncio
async def test_register_failure(auth_manager):
    """Test failed registration."""
    with patch.object(auth_manager, "_get_client") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Username already exists"
        mock_response.json.return_value = {"detail": "Username already exists"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_http

        success, error = await auth_manager.register(
            "existinguser", "test@example.com", "TestPass123!"
        )

        assert success is False
        assert "Username already exists" in error


def test_is_authenticated_with_token(auth_manager):
    """Test authentication check with valid token."""
    from datetime import datetime, timedelta

    auth_manager._token = "valid-token"
    auth_manager._token_expiry = datetime.utcnow() + timedelta(hours=1)

    assert auth_manager.is_authenticated is True


def test_is_authenticated_expired_token(auth_manager):
    """Test authentication check with expired token."""
    from datetime import datetime, timedelta

    auth_manager._token = "expired-token"
    auth_manager._token_expiry = datetime.utcnow() - timedelta(hours=1)

    assert auth_manager.is_authenticated is False
    assert auth_manager._token is None


def test_is_admin(auth_manager):
    """Test admin role check."""
    auth_manager._token = "token"
    auth_manager._user = {"username": "admin", "role": "admin"}

    assert auth_manager.is_admin() is True


def test_is_operator(auth_manager):
    """Test operator role check."""
    auth_manager._token = "token"
    auth_manager._user = {"username": "operator", "role": "operator"}

    assert auth_manager.is_operator() is True
    assert auth_manager.is_admin() is False


def test_is_viewer(auth_manager):
    """Test viewer role check."""
    auth_manager._token = "token"
    auth_manager._user = {"username": "viewer", "role": "viewer"}

    assert auth_manager.is_viewer() is True
    assert auth_manager.is_operator() is False
    assert auth_manager.is_admin() is False


def test_logout(auth_manager):
    """Test logout clears authentication state."""
    auth_manager._token = "test-token"
    auth_manager._user = {"username": "test"}

    auth_manager.logout()

    assert auth_manager._token is None
    assert auth_manager._user is None
    assert auth_manager.is_authenticated is False


@pytest.mark.asyncio
async def test_check_auth_required_enabled(auth_manager):
    """Test checking if auth is required (enabled)."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await auth_manager.check_auth_required()

        assert result is True


@pytest.mark.asyncio
async def test_check_auth_required_disabled(auth_manager):
    """Test checking if auth is required (disabled)."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await auth_manager.check_auth_required()

        assert result is False
