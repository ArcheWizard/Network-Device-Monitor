# Testing Guide

This guide covers running tests, writing tests, and testing best practices for Network Device Monitor.

## Quick Start

```bash
# Run all backend tests
make test

# Run tests with coverage
pytest --cov=app --cov-report=html backend/tests/

# Run frontend tests
make test-frontend
```

## Running Tests

### Backend Tests

**All tests:**
```bash
cd backend
pytest tests/
```

**Verbose output:**
```bash
pytest -v tests/
```

**Specific test file:**
```bash
pytest tests/test_discovery_api.py
```

**Specific test function:**
```bash
pytest tests/test_discovery_api.py::test_scan_basic
```

**With print statements:**
```bash
pytest -s tests/
```

### Frontend Tests

```bash
cd frontend/pyqt
pytest tests/
```

**Note:** Frontend tests require a display environment (X11, Wayland, etc.) or use Xvfb:

```bash
xvfb-run pytest tests/
```

## Test Coverage

### Generate Coverage Report

```bash
cd backend
pytest --cov=app --cov-report=html tests/
```

View the report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Terminal Report

```bash
pytest --cov=app --cov-report=term-missing tests/
```

Shows which lines are not covered by tests.

## Test Organization

### Backend Test Structure

```
backend/tests/
├── conftest.py                 # Shared fixtures
├── test_api_smoke.py           # Basic API smoke tests
├── test_discovery_api.py       # Discovery API tests
├── test_discovery_persistence.py  # Discovery + database tests
├── test_identification.py      # Identification service tests
├── test_monitoring.py          # Monitoring service tests
├── test_oui_lookup.py          # OUI database tests
├── test_sqlite_repo.py         # SQLite repository tests
└── test_websocket.py           # WebSocket tests
```

### Frontend Test Structure

```
frontend/pyqt/tests/
├── __init__.py
├── test_api_client.py          # API client tests
├── test_main_window.py         # Main window UI tests
└── test_workers.py             # Background worker tests
```

## Writing Tests

### Basic Test Template

```python
import pytest

@pytest.mark.asyncio
async def test_my_function():
    """Test description."""
    from app.services import my_service

    result = await my_service.my_function()
    assert result is not None
    assert len(result) > 0
```

### API Test Template

```python
@pytest.mark.asyncio
async def test_api_endpoint():
    """Test API endpoint."""
    from httpx import AsyncClient
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/devices")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
```

### Fixture Usage

```python
@pytest.fixture
async def test_device():
    """Create test device."""
    return {
        "id": "test-device",
        "ip": "192.168.1.100",
        "mac": "aa:bb:cc:dd:ee:ff"
    }

@pytest.mark.asyncio
async def test_with_fixture(test_device):
    """Use fixture in test."""
    assert test_device["ip"] == "192.168.1.100"
```

## Test Types

### Unit Tests

Test individual functions/methods in isolation:

```python
@pytest.mark.asyncio
async def test_ping_device():
    """Unit test for ping function."""
    from app.services import monitoring

    result = await monitoring.ping_device("127.0.0.1", count=1)
    assert result["ip"] == "127.0.0.1"
    assert "status" in result
```

### Integration Tests

Test multiple components working together:

```python
@pytest.mark.asyncio
async def test_discovery_with_persistence():
    """Integration test for discovery + database."""
    from app.services import discovery
    from app.storage.sqlite import init_sqlite

    # Setup
    repo = await init_sqlite(":memory:")

    # Discover devices
    devices = await discovery.scan()

    # Persist to database
    for device in devices:
        await repo.upsert_device(device)

    # Verify
    stored = await repo.list_devices()
    assert len(stored) == len(devices)
```

### End-to-End Tests

Test complete workflows:

```python
@pytest.mark.asyncio
async def test_full_discovery_workflow():
    """E2E test for complete discovery workflow."""
    # 1. Trigger discovery via API
    # 2. Verify devices stored in database
    # 3. Verify metrics written to InfluxDB
    # 4. Verify WebSocket notifications sent
    pass
```

## Test Markers

Use markers to categorize tests:

```python
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_network_scan():
    """Slow integration test."""
    pass
```

Run specific markers:
```bash
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Run only integration tests
pytest -m unit  # Run only unit tests
```

## Mocking

### Mock External Services

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mocked_snmp():
    """Test with mocked SNMP."""
    mock_response = {"hostname": "router", "description": "Test"}

    with patch('app.services.snmp.snmp_identify', new=AsyncMock(return_value=mock_response)):
        from app.services import identification

        result = await identification.identify_device("192.168.1.1")
        assert result['hostname'] == "router"
```

### Mock Database

```python
@pytest.fixture
async def mock_repo():
    """Mock repository."""
    from unittest.mock import AsyncMock

    repo = AsyncMock()
    repo.list_devices.return_value = [
        {"id": "device-1", "ip": "192.168.1.1"}
    ]
    return repo
```

## Continuous Testing

### Watch Mode (pytest-watch)

```bash
pip install pytest-watch
ptw backend/tests/
```

Auto-runs tests when files change.

### Pre-commit Testing

```bash
pip install pre-commit
pre-commit install
```

Runs tests before each commit (configure in `.pre-commit-config.yaml`).

## Debugging Tests

### Run with PDB

```bash
pytest --pdb tests/
```

Drops into debugger on failures.

### Print Output

```bash
pytest -s tests/
```

Shows print statements during tests.

### Verbose Logging

```bash
pytest --log-cli-level=DEBUG tests/
```

## CI/CD Testing

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Release tags

See `.github/workflows/ci.yml` for configuration.

## Performance Testing

```python
import time

@pytest.mark.asyncio
async def test_discovery_performance():
    """Test discovery completes within time limit."""
    from app.services import discovery

    start = time.time()
    result = await discovery.scan()
    elapsed = time.time() - start

    assert elapsed < 30.0  # Must complete in under 30 seconds
```

## Best Practices

1. **Write tests first** (TDD approach)
2. **Keep tests independent** - no shared state between tests
3. **Use descriptive names** - `test_discovery_returns_devices_with_mac_addresses`
4. **Test edge cases** - empty inputs, errors, timeouts
5. **Mock external dependencies** - network, databases, APIs
6. **Clean up resources** - use fixtures with teardown
7. **Fast tests** - optimize for speed, mark slow tests
8. **Maintain test data** - use factories/fixtures for test data

## Common Issues

### Tests Hang

- Check for missing `@pytest.mark.asyncio` decorator
- Ensure async functions use `await`
- Check for deadlocks in concurrent code

### Import Errors

```bash
# Add backend to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/backend"
pytest tests/
```

### Network Tests Fail

- Tests may require network access
- Some discovery tests need root/CAP_NET_RAW on Linux
- Mock network calls for unit tests

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
