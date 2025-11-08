"""Test validation error handling for registration."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from src.auth_manager import AuthManager


@pytest.mark.asyncio
async def test_register_validation_error_list():
    """Test that list-based validation errors are properly converted to string."""
    auth_manager = AuthManager("http://test:8000")

    with patch.object(auth_manager, "_get_client") as mock_client:
        # Simulate a validation error response from FastAPI
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = "Validation error"
        mock_response.json.return_value = {
            "detail": [
                {
                    "type": "value_error",
                    "loc": ["body", "password"],
                    "msg": "Value error, Password must contain at least one uppercase letter",
                    "input": "weakpassword",
                    "ctx": {"error": {}}
                },
                {
                    "type": "value_error",
                    "loc": ["body", "email"],
                    "msg": "Value error, Invalid email format",
                    "input": "notanemail",
                    "ctx": {"error": {}}
                }
            ]
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unprocessable Entity", request=MagicMock(), response=mock_response
        )

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_http

        success, error_msg = await auth_manager.register(
            "testuser", "test@example.com", "weakpassword"
        )

        assert success is False
        assert isinstance(error_msg, str)
        assert "Password must contain at least one uppercase letter" in error_msg
        assert "Invalid email format" in error_msg


@pytest.mark.asyncio
async def test_register_validation_error_string():
    """Test that string-based error details are handled correctly."""
    auth_manager = AuthManager("http://test:8000")

    with patch.object(auth_manager, "_get_client") as mock_client:
        # Simulate a simple string error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.json.return_value = {
            "detail": "Username already exists"
        }
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_http

        success, error_msg = await auth_manager.register(
            "testuser", "test@example.com", "StrongPass123"
        )

        assert success is False
        assert isinstance(error_msg, str)
        assert error_msg == "Username already exists"
