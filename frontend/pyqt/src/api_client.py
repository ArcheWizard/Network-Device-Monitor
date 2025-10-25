"""Async API client for the FastAPI backend with WebSocket streaming."""

from __future__ import annotations

from typing import Any, AsyncGenerator, Optional
import asyncio
import json
import logging
from urllib.parse import urlparse, urlunparse

import httpx
import websockets

logger = logging.getLogger(__name__)


def _http_to_ws(url: str) -> str:
    """Convert http(s) base URL to ws(s) for websockets."""
    parsed = urlparse(url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    return urlunparse((scheme, parsed.netloc, "/ws/stream", "", "", ""))


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _client_get(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        return self._client

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

    async def trigger_scan(
        self,
        cidr: Optional[str] = None,
        interface: Optional[str] = None,
        arp_timeout: Optional[float] = None,
        ping_timeout: Optional[float] = None,
        persist: Optional[bool] = True,
        identify: Optional[bool] = True,
    ) -> dict[str, Any]:
        """POST /api/discovery/scan with optional parameters."""
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
        r = await client.post("/api/discovery/scan", json=payload or None)
        r.raise_for_status()
        return r.json()

    async def stream_events(
        self, reconnect_backoff: float = 2.0, max_backoff: float = 30.0
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Connect to WebSocket and yield events as dicts with auto-reconnect.

        Yields:
            Parsed JSON messages from the server.
        """
        ws_url = _http_to_ws(self.base_url)
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


async def fetch_devices(base_url: str = "http://127.0.0.1:8000") -> list[dict[str, Any]]:
    """Convenience function for one-off device fetches."""
    client = APIClient(base_url)
    try:
        return await client.fetch_devices()
    finally:
        await client.aclose()
