"""Async API client for the FastAPI backend with WebSocket streaming."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Optional
from urllib.parse import urlparse, urlunparse

import httpx
import websockets

logger = logging.getLogger(__name__)


def _http_to_ws(url: str, token: Optional[str] = None) -> str:
    """Convert http(s) base URL to ws(s) for websockets.

    Args:
        url: Base HTTP(S) URL
        token: Optional JWT token to append as query parameter

    Returns:
        WebSocket URL with optional token parameter
    """
    parsed = urlparse(url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    ws_url = urlunparse((scheme, parsed.netloc, "/ws/stream", "", "", ""))

    # Add token as query parameter if provided
    if token:
        ws_url += f"?token={token}"

    return ws_url


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self._client: Optional[httpx.AsyncClient] = None

    async def _client_get(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=10.0,
                headers=headers
            )
        return self._client

    def set_auth_token(self, token: Optional[str]) -> None:
        """Update authentication token and recreate client if needed."""
        self.auth_token = token
        if self._client is not None:
            # Close existing client and recreate with new token
            asyncio.create_task(self.aclose())
            self._client = None

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def fetch_devices(self) -> list[dict[str, Any]]:
        """GET /api/devices"""
        client = await self._client_get()
        r = await client.get("/api/devices")
        r.raise_for_status()
        data = r.json()
        assert isinstance(data, list)
        return data  # type: ignore[return-value]

    async def fetch_live_devices(self) -> list[dict[str, Any]]:
        """GET /api/devices/live - only non-archived devices"""
        client = await self._client_get()
        r = await client.get("/api/devices/live")
        r.raise_for_status()
        data = r.json()
        assert isinstance(data, list)
        return data  # type: ignore[return-value]

    async def fetch_archived_devices(self) -> list[dict[str, Any]]:
        """GET /api/devices/archived - only archived devices"""
        client = await self._client_get()
        r = await client.get("/api/devices/archived")
        r.raise_for_status()
        data = r.json()
        assert isinstance(data, list)
        return data  # type: ignore[return-value]

    async def delete_device(self, device_id: str) -> None:
        """DELETE /api/devices/{device_id}

        Args:
            device_id: Device identifier (MAC or IP)

        Raises:
            httpx.HTTPStatusError: If delete fails (404, 403, 503, etc.)
        """
        client = await self._client_get()
        r = await client.delete(f"/api/devices/{device_id}")
        r.raise_for_status()

    async def archive_device(self, device_id: str) -> None:
        """POST /api/devices/{device_id}/archive

        Args:
            device_id: Device identifier (MAC or IP)

        Raises:
            httpx.HTTPStatusError: If archive fails (404, 403, 503, etc.)
        """
        client = await self._client_get()
        r = await client.post(f"/api/devices/{device_id}/archive")
        r.raise_for_status()

    async def restore_device(self, device_id: str) -> None:
        """POST /api/devices/{device_id}/restore

        Args:
            device_id: Device identifier (MAC or IP)

        Raises:
            httpx.HTTPStatusError: If restore fails (404, 403, 503, etc.)
        """
        client = await self._client_get()
        r = await client.post(f"/api/devices/{device_id}/restore")
        r.raise_for_status()

    async def trigger_scan(
        self,
        cidr: Optional[str] = None,
        interface: Optional[str] = None,
        arp_timeout: Optional[float] = None,
        ping_timeout: Optional[float] = None,
        persist: Optional[bool] = True,
        identify: Optional[bool] = True,
    ) -> dict[str, Any]:
        """POST /api/devices/scan with optional parameters."""
        client = await self._client_get()
        payload: dict[str, Any] = {}
        if cidr is not None:
            payload["cidr"] = cidr
        if interface is not None:
            payload["interface"] = interface
        if arp_timeout is not None:
            payload["arp_timeout"] = arp_timeout
        if ping_timeout is not None:
            payload["ping_timeout"] = ping_timeout
        if persist is not None:
            payload["persist"] = persist
        if identify is not None:
            payload["identify"] = identify
        r = await client.post("/api/devices/discover", json=payload or None)
        r.raise_for_status()
        return r.json()

    async def stream_events(
        self, reconnect_backoff: float = 2.0, max_backoff: float = 30.0
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Connect to WebSocket and yield events as dicts with auto-reconnect.

        Yields:
            Parsed JSON messages from the server.
        """
        ws_url = _http_to_ws(self.base_url, self.auth_token)
        backoff = reconnect_backoff
        while True:
            try:
                logger.info("Connecting to WS %s", ws_url)
                async with websockets.connect(ws_url) as ws:  # type: ignore[arg-type]
                    backoff = reconnect_backoff  # reset after successful connect
                    while True:
                        raw = await ws.recv()
                        try:
                            msg = json.loads(raw)
                            if isinstance(msg, dict):
                                yield msg
                            else:
                                logger.debug("Ignoring non-dict WS msg: %s", msg)
                        except json.JSONDecodeError:
                            logger.exception("Failed to parse WS message: %s", raw)
            except asyncio.CancelledError:
                logger.info("WebSocket stream cancelled")
                break
            except Exception as e:
                logger.warning("WebSocket error: %s; reconnecting in %.1fs", e, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, max_backoff)


async def fetch_devices(
    base_url: str = "http://127.0.0.1:8000",
) -> list[dict[str, Any]]:
    """Convenience function for one-off device fetches."""
    client = APIClient(base_url)
    try:
        return await client.fetch_devices()
    finally:
        await client.aclose()
