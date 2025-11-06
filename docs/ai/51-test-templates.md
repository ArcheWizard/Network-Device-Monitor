# Test Templates

## Overview

Test templates for Network Device Monitor using pytest and pytest-asyncio.

## Unit Test Template

`backend/tests/test_my_service.py`:

```python
"""Unit tests for my_service module."""

import pytest
from app.services import my_service


class TestMainFunction:
    """Tests for main_function."""

    @pytest.mark.asyncio
    async def test_basic_functionality(self):
        """Test basic function operation."""
        result = await my_service.main_function("test")
        assert isinstance(result, list)
        assert len(result) >= 0

    @pytest.mark.asyncio
    async def test_with_params(self):
        """Test function with custom parameters."""
        result = await my_service.main_function("test", param2=20)
        assert result is not None

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            await my_service.main_function("")


class TestHelperFunction:
    """Tests for helper_function."""

    @pytest.mark.asyncio
    async def test_success_case(self):
        """Test successful processing."""
        result = await my_service.helper_function({"key": "value"})
        assert result is not None

    @pytest.mark.asyncio
    async def test_failure_case(self):
        """Test graceful failure."""
        result = await my_service.helper_function({})
        assert result is None
```

## API Router Test Template

`backend/tests/test_my_router.py`:

```python
"""API tests for my_router endpoints."""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestGetEndpoint:
    """Tests for GET endpoint."""

    @pytest.mark.asyncio
    async def test_get_items_success(self, client):
        """Test getting items."""
        response = await client.get("/api/my-endpoint")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_with_pagination(self, client):
        """Test pagination parameters."""
        response = await client.get("/api/my-endpoint?limit=10&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10

    @pytest.mark.asyncio
    async def test_invalid_pagination(self, client):
        """Test invalid pagination parameters."""
        response = await client.get("/api/my-endpoint?limit=-1")
        assert response.status_code == 422  # Validation error


class TestPostEndpoint:
    """Tests for POST endpoint."""

    @pytest.mark.asyncio
    async def test_create_item_success(self, client):
        """Test creating item."""
        payload = {"param1": "value", "param2": 10}
        response = await client.post("/api/my-endpoint", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_create_item_validation_error(self, client):
        """Test validation error."""
        payload = {"param1": ""}  # Invalid
        response = await client.post("/api/my-endpoint", json=payload)
        assert response.status_code == 400
```

## Integration Test Template

`backend/tests/test_integration_my_feature.py`:

```python
"""Integration tests for my feature."""

import pytest
from httpx import AsyncClient
from app.main import app
from app.storage.sqlite import init_sqlite


@pytest.fixture
async def test_db():
    """Create test database."""
    repo = await init_sqlite(":memory:")
    yield repo
    # Cleanup if needed


@pytest.fixture
async def client_with_db(test_db):
    """Create test client with database."""
    app.state.inventory_repo = test_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_full_workflow(client_with_db):
    """Test complete feature workflow."""
    # Step 1: Create item
    create_response = await client_with_db.post(
        "/api/my-endpoint",
        json={"param1": "test"}
    )
    assert create_response.status_code == 200

    # Step 2: Retrieve item
    get_response = await client_with_db.get("/api/my-endpoint")
    assert get_response.status_code == 200
    items = get_response.json()
    assert len(items) > 0
```

## Fixture Templates

`backend/tests/conftest.py` (add to existing):

```python
"""Shared test fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_device():
    """Create mock device for testing."""
    return {
        "id": "test-device",
        "ip": "192.168.1.100",
        "mac": "aa:bb:cc:dd:ee:ff",
        "hostname": "test.local",
        "vendor": "Test Vendor",
        "status": "up"
    }


@pytest.fixture
async def mock_devices():
    """Create list of mock devices."""
    return [
        {"id": "device-1", "ip": "192.168.1.1", "mac": "aa:bb:cc:dd:ee:01"},
        {"id": "device-2", "ip": "192.168.1.2", "mac": "aa:bb:cc:dd:ee:02"},
        {"id": "device-3", "ip": "192.168.1.3", "mac": "aa:bb:cc:dd:ee:03"},
    ]
```

## Mock Templates

```python
"""Mock templates for testing."""

from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_snmp_response():
    """Mock SNMP response."""
    return {
        "hostname": "router",
        "description": "Cisco IOS",
        "uptime": "12345600",
        "contact": "admin@example.com",
        "location": "Server Room",
        "object_id": "1.3.6.1.4.1.9"
    }


@pytest.mark.asyncio
async def test_with_mocked_snmp(mock_snmp_response):
    """Test with mocked SNMP."""
    with patch('app.services.snmp.snmp_identify', new=AsyncMock(return_value=mock_snmp_response)):
        from app.services import identification

        result = await identification.identify_device("192.168.1.1")
        assert result['hostname'] == "router"
```

## Parametrized Test Template

```python
"""Parametrized tests for multiple test cases."""

import pytest


@pytest.mark.parametrize("input_val,expected", [
    ("192.168.1.1", True),
    ("192.168.1.256", False),
    ("invalid", False),
    ("10.0.0.1", True),
])
def test_ip_validation(input_val, expected):
    """Test IP validation with various inputs."""
    from app.utils.network import is_valid_ip
    assert is_valid_ip(input_val) == expected


@pytest.mark.parametrize("mac,vendor", [
    ("00:00:0C:xx:xx:xx", "Cisco Systems"),
    ("00:50:56:xx:xx:xx", "VMware"),
    ("invalid", None),
])
@pytest.mark.asyncio
async def test_vendor_lookup(mac, vendor):
    """Test vendor lookup with various MACs."""
    from app.utils.oui import lookup_vendor
    result = lookup_vendor(mac)
    if vendor:
        assert vendor in result
    else:
        assert result is None
```

## Performance Test Template

```python
"""Performance tests."""

import pytest
import time


@pytest.mark.asyncio
async def test_discovery_performance():
    """Test discovery performance."""
    from app.services import discovery

    start_time = time.time()
    result = await discovery.scan(cidr="192.168.1.0/24")
    elapsed = time.time() - start_time

    assert elapsed < 30.0  # Should complete in under 30 seconds
    assert len(result) >= 0


@pytest.mark.asyncio
async def test_bulk_monitoring_performance():
    """Test monitoring multiple devices."""
    from app.services import monitoring
    import asyncio

    ips = [f"192.168.1.{i}" for i in range(1, 11)]

    start_time = time.time()
    tasks = [monitoring.ping_device(ip) for ip in ips]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed = time.time() - start_time

    assert len(results) == 10
    assert elapsed < 15.0  # Should complete in under 15 seconds
```

## WebSocket Test Template

```python
"""WebSocket tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_websocket_connection():
    """Test WebSocket connection."""
    client = TestClient(app)

    with client.websocket_connect("/ws/stream") as websocket:
        # Receive hello message
        data = websocket.receive_json()
        assert data["type"] == "hello"
        assert "ts" in data


def test_websocket_messages():
    """Test receiving WebSocket messages."""
    client = TestClient(app)

    with client.websocket_connect("/ws/stream") as websocket:
        # Wait for messages (with timeout)
        import time
        start = time.time()
        messages = []

        while time.time() - start < 5:
            try:
                data = websocket.receive_json(timeout=1)
                messages.append(data)
                if len(messages) >= 3:
                    break
            except:
                break

        # Verify message types
        assert any(msg["type"] == "hello" for msg in messages)
```

## Coverage Commands

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html backend/tests/

# Run specific test file
pytest backend/tests/test_my_service.py -v

# Run with coverage and show missing lines
pytest --cov=app --cov-report=term-missing backend/tests/

# Run only fast tests (exclude slow integration tests)
pytest -m "not slow" backend/tests/

# Run specific test class
pytest backend/tests/test_my_service.py::TestMainFunction -v

# Run with verbose output and print statements
pytest -v -s backend/tests/
```

## Test Markers

Add to `pytest.ini`:

```ini
[tool:pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    api: marks tests as API tests
    websocket: marks tests as WebSocket tests
```

Usage in tests:

```python
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_discovery_scan():
    """Slow integration test for full discovery."""
    pass
```
