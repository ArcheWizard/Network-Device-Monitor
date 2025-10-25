"""Tests for API client with mocked httpx and websockets."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from src.api_client import APIClient, _http_to_ws, fetch_devices


class TestHttpToWs:
    """Tests for URL conversion helper."""

    def test_http_to_ws(self):
        assert _http_to_ws("http://localhost:8000") == "ws://localhost:8000/ws/stream"

    def test_https_to_wss(self):
        assert (
            _http_to_ws("https://example.com:8443")
            == "wss://example.com:8443/ws/stream"
        )

    def test_strips_trailing_slash(self):
        assert _http_to_ws("http://localhost:8000/") == "ws://localhost:8000/ws/stream"


class TestAPIClient:
    """Tests for APIClient class."""

    @pytest.mark.asyncio
    async def test_fetch_devices_success(self):
        """Test successful device list fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "id": "aa:bb:cc:dd:ee:ff",
                "ip": "192.168.1.10",
                "mac": "aa:bb:cc:dd:ee:ff",
            }
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = APIClient("http://test:8000")
            devices = await client.fetch_devices()

            assert len(devices) == 1
            assert devices[0]["id"] == "aa:bb:cc:dd:ee:ff"
            mock_client.get.assert_called_once_with("/api/devices")

    @pytest.mark.asyncio
    async def test_trigger_scan_with_params(self):
        """Test triggering scan with custom parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"count": 5, "devices": []}
        mock_response.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = APIClient("http://test:8000")
            result = await client.trigger_scan(
                cidr="192.168.1.0/24", persist=True, identify=True
            )

            assert result["count"] == 5
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "/api/discovery/scan"
            assert call_args[1]["json"]["cidr"] == "192.168.1.0/24"

    @pytest.mark.asyncio
    async def test_client_aclose(self):
        """Test client cleanup."""
        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            client = APIClient("http://test:8000")
            _ = await client._client_get()  # initialize client
            await client.aclose()

            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_events_yields_messages(self):
        """Test WebSocket stream yields parsed JSON messages."""

        async def mock_recv_gen():
            yield json.dumps({"type": "hello", "message": "Connected"})
            yield json.dumps({"type": "device_up", "device_id": "test"})

        mock_ws = AsyncMock()
        recv_iter = mock_recv_gen()

        async def mock_recv():
            return await recv_iter.__anext__()

        mock_ws.recv = mock_recv
        mock_ws.__aenter__ = AsyncMock(return_value=mock_ws)
        mock_ws.__aexit__ = AsyncMock()

        with patch("src.api_client.websockets.connect", return_value=mock_ws):
            client = APIClient("http://test:8000")
            events = []
            async for event in client.stream_events():
                events.append(event)
                if len(events) >= 2:
                    break

            assert len(events) == 2
            assert events[0]["type"] == "hello"
            assert events[1]["type"] == "device_up"

    @pytest.mark.asyncio
    async def test_convenience_fetch_devices(self):
        """Test convenience fetch_devices function."""
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()

        with patch("src.api_client.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            devices = await fetch_devices("http://test:8000")

            assert devices == []
            mock_client.aclose.assert_called_once()
