"""
Tests for WebSocket streaming functionality.
"""

import pytest
from fastapi.testclient import TestClient
from starlette.routing import WebSocketRoute
from app.main import app
from app.api.routers.ws import ConnectionManager, get_manager


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def connection_manager():
    """Create a fresh ConnectionManager instance for testing."""
    return ConnectionManager()


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.sent_messages = []
        self.closed = False

    async def accept(self):
        """Accept the connection."""
        pass

    async def send_json(self, data: dict):
        """Store sent messages."""
        self.sent_messages.append(data)

    async def receive_text(self):
        """Simulate receiving text (not used in current implementation)."""
        raise Exception("Connection closed")


@pytest.mark.asyncio
async def test_connection_manager_connect_disconnect(connection_manager):
    """Test that ConnectionManager can connect and disconnect websockets."""
    ws = MockWebSocket()

    # Connect
    await connection_manager.connect(ws)
    assert len(connection_manager.active_connections) == 1
    assert ws in connection_manager.active_connections

    # Disconnect
    connection_manager.disconnect(ws)
    assert len(connection_manager.active_connections) == 0
    assert ws not in connection_manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_multiple_connections(connection_manager):
    """Test that ConnectionManager can handle multiple simultaneous connections."""
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    ws3 = MockWebSocket()

    # Connect multiple clients
    await connection_manager.connect(ws1)
    await connection_manager.connect(ws2)
    await connection_manager.connect(ws3)

    assert len(connection_manager.active_connections) == 3

    # Disconnect one
    connection_manager.disconnect(ws2)
    assert len(connection_manager.active_connections) == 2
    assert ws1 in connection_manager.active_connections
    assert ws2 not in connection_manager.active_connections
    assert ws3 in connection_manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_broadcast(connection_manager):
    """Test that broadcast sends message to all connected clients."""
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()
    ws3 = MockWebSocket()

    await connection_manager.connect(ws1)
    await connection_manager.connect(ws2)
    await connection_manager.connect(ws3)

    test_message = {"type": "test", "data": "hello world", "ts": 12345}

    await connection_manager.broadcast(test_message)

    # All clients should receive the message
    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 1
    assert len(ws3.sent_messages) == 1

    assert ws1.sent_messages[0] == test_message
    assert ws2.sent_messages[0] == test_message
    assert ws3.sent_messages[0] == test_message


@pytest.mark.asyncio
async def test_connection_manager_send_to_client(connection_manager):
    """Test that send_to_client sends message to a specific client."""
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await connection_manager.connect(ws1)
    await connection_manager.connect(ws2)

    test_message = {"type": "hello", "message": "Welcome to monitoring"}

    await connection_manager.send_to_client(ws1, test_message)

    # Only ws1 should receive the message
    assert len(ws1.sent_messages) == 1
    assert len(ws2.sent_messages) == 0
    assert ws1.sent_messages[0] == test_message


@pytest.mark.asyncio
async def test_device_discovered_event_format(connection_manager):
    """Test device_discovered event has correct format."""
    ws = MockWebSocket()
    await connection_manager.connect(ws)

    event = {
        "type": "device_discovered",
        "device": {
            "id": "aa:bb:cc:dd:ee:ff",
            "ip": "192.168.1.100",
            "mac": "aa:bb:cc:dd:ee:ff",
            "hostname": "test-device",
            "vendor": "Test Vendor Inc.",
            "source": "arp",
        },
        "ts": 1234567890,
    }

    await connection_manager.broadcast(event)

    assert len(ws.sent_messages) == 1
    received = ws.sent_messages[0]

    assert received["type"] == "device_discovered"
    assert "device" in received
    assert received["device"]["id"] == "aa:bb:cc:dd:ee:ff"
    assert received["device"]["ip"] == "192.168.1.100"
    assert received["device"]["vendor"] == "Test Vendor Inc."
    assert "ts" in received


@pytest.mark.asyncio
async def test_device_up_event_format(connection_manager):
    """Test device_up event has correct format."""
    ws = MockWebSocket()
    await connection_manager.connect(ws)

    event = {
        "type": "device_up",
        "device_id": "aa:bb:cc:dd:ee:ff",
        "ip": "192.168.1.100",
        "hostname": "test-device",
        "vendor": "Test Vendor Inc.",
        "previous_status": "down",
        "ts": 1234567890,
    }

    await connection_manager.broadcast(event)

    assert len(ws.sent_messages) == 1
    received = ws.sent_messages[0]

    assert received["type"] == "device_up"
    assert received["device_id"] == "aa:bb:cc:dd:ee:ff"
    assert received["ip"] == "192.168.1.100"
    assert received["previous_status"] == "down"


@pytest.mark.asyncio
async def test_device_down_event_format(connection_manager):
    """Test device_down event has correct format."""
    ws = MockWebSocket()
    await connection_manager.connect(ws)

    event = {
        "type": "device_down",
        "device_id": "aa:bb:cc:dd:ee:ff",
        "ip": "192.168.1.100",
        "hostname": "test-device",
        "vendor": "Test Vendor Inc.",
        "previous_status": "up",
        "ts": 1234567890,
    }

    await connection_manager.broadcast(event)

    assert len(ws.sent_messages) == 1
    received = ws.sent_messages[0]

    assert received["type"] == "device_down"
    assert received["device_id"] == "aa:bb:cc:dd:ee:ff"
    assert received["previous_status"] == "up"
    assert received["ip"] == "192.168.1.100"
    assert received["hostname"] == "test-device"
    assert received["vendor"] == "Test Vendor Inc."
    assert "ts" in received


@pytest.mark.asyncio
async def test_latency_event_format(connection_manager):
    """Test latency event has correct format."""
    ws = MockWebSocket()
    await connection_manager.connect(ws)

    event = {
        "type": "latency",
        "device_id": "aa:bb:cc:dd:ee:ff",
        "latency_avg": 12.4,
        "packet_loss": 0.0,
        "ts": 123456789,
    }

    await connection_manager.broadcast(event)

    assert len(ws.sent_messages) == 1
    received = ws.sent_messages[0]
    assert received["type"] == "latency"
    assert received["device_id"] == "aa:bb:cc:dd:ee:ff"
    assert received["latency_avg"] == 12.4
    assert received["packet_loss"] == 0.0
    assert "ts" in received


@pytest.mark.asyncio
async def test_broadcast_with_disconnected_client(connection_manager):
    """Test broadcast handles disconnected clients gracefully."""
    ws1 = MockWebSocket()
    ws2 = MockWebSocket()

    await connection_manager.connect(ws1)
    await connection_manager.connect(ws2)

    # Simulate ws2 raising an exception on send_json
    async def fail_send_json(data):
        raise Exception("Client disconnected")

    ws2.send_json = fail_send_json  # type: ignore[assignment]

    test_message = {"type": "test", "data": "x"}
    await connection_manager.broadcast(test_message)

    # ws1 should receive the message, ws2 should be removed
    assert len(ws1.sent_messages) == 1
    assert ws1.sent_messages[0] == test_message
    assert ws2 not in connection_manager.active_connections


@pytest.mark.asyncio
async def test_get_manager_singleton():
    """Test that get_manager returns the same instance."""
    from app.api.routers.ws import manager

    assert get_manager() is manager


def test_websocket_endpoint_exists(test_client):
    """Test that WebSocket endpoint is registered in the app."""
    # Only inspect WebSocketRoute to avoid BaseRoute path typing issues
    paths = [r.path for r in app.routes if isinstance(r, WebSocketRoute)]
    assert "/ws/stream" in paths
