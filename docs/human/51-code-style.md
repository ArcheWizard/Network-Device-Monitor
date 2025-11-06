# Code Style Guide

Detailed code style guidelines for the Network Device Monitor project.

## Overview

This project follows Python best practices with specific conventions. Consistency is key for maintainability.

## Python Style

### PEP 8 Compliance

Follow [PEP 8](https://peps.python.org/pep-0008/) with some modifications:

- **Line length:** 88 characters (Black default)
- **Indentation:** 4 spaces (never tabs)
- **Imports:** Organized in groups
- **Naming:** Follow PEP 8 conventions

### Code Formatter: Black

Use [Black](https://black.readthedocs.io/) for automatic formatting:

```bash
# Format entire codebase
black backend/app backend/tests

# Check without formatting
black --check backend/app

# Format specific file
black backend/app/services/discovery.py
```

Configuration in `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
```

### Type Checker: mypy

Use [mypy](https://mypy.readthedocs.io/) for type checking:

```bash
# Type check entire codebase
mypy backend/app

# Strict mode
mypy --strict backend/app
```

Configuration in `backend/mypy.ini`:

```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### Linter: flake8

Use [flake8](https://flake8.pycqa.org/) for linting:

```bash
# Lint codebase
flake8 backend/app backend/tests

# With specific rules
flake8 --max-line-length=88 backend/app
```

Configuration in `.flake8`:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = __pycache__, .git, venv, build
```

## Naming Conventions

### Variables and Functions

```python
# Variables: lowercase with underscores
device_count = 10
max_retry_attempts = 3

# Functions: lowercase with underscores
def discover_devices():
    pass

def calculate_average_latency():
    pass

# Private functions: single leading underscore
def _internal_helper():
    pass

# Constants: uppercase with underscores
MAX_DEVICES = 100
DEFAULT_TIMEOUT = 2.0
API_VERSION = "1.0"
```

### Classes

```python
# Classes: PascalCase
class Device:
    pass

class NetworkDiscoveryService:
    pass

class SQLiteInventoryRepository:
    pass

# Private classes: single leading underscore
class _InternalCache:
    pass
```

### Modules and Packages

```python
# Modules: lowercase with underscores
# discovery.py
# device_monitor.py
# influx_writer.py

# Packages: lowercase without underscores
# app/services/
# app/models/
# app/storage/
```

## Type Hints

### Always Use Type Hints

```python
from typing import Optional, List, Dict, Union
from datetime import datetime

# Function arguments and return type
def fetch_device(device_id: str) -> Optional[Device]:
    """Fetch device by ID."""
    pass

# Multiple return types
def parse_response(data: str) -> Union[Dict, List]:
    """Parse API response."""
    pass

# Complex types
def process_metrics(
    metrics: Dict[str, List[float]],
    threshold: float = 100.0
) -> List[str]:
    """Process metrics and return alerts."""
    pass
```

### Pydantic Models

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Device(BaseModel):
    """Device model with validation."""

    id: str = Field(..., description="Device MAC address")
    ip: str = Field(..., pattern=r"^\d{1,3}(\.\d{1,3}){3}$")
    hostname: Optional[str] = Field(None, max_length=255)
    first_seen: datetime
    last_seen: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "aa:bb:cc:dd:ee:ff",
                "ip": "192.168.1.100",
                "hostname": "device.local",
                "first_seen": "2024-01-01T00:00:00Z",
                "last_seen": "2024-01-01T12:00:00Z"
            }
        }
```

## Documentation

### Docstrings: Google Style

```python
def discover_devices(
    cidr: str,
    interface: str,
    timeout: float = 2.0,
    use_arp: bool = True
) -> List[Device]:
    """
    Discover devices on the network.

    Performs network discovery using ARP scanning and/or ICMP ping sweep.
    Falls back to ICMP if ARP is not available (e.g., on WiFi interfaces).

    Args:
        cidr: Network CIDR notation (e.g., "192.168.1.0/24")
        interface: Network interface name (e.g., "eth0")
        timeout: Timeout in seconds for each probe. Default is 2.0.
        use_arp: Whether to attempt ARP scanning. Default is True.

    Returns:
        List of discovered Device objects with IP, MAC, and metadata.

    Raises:
        ValueError: If CIDR format is invalid
        NetworkError: If interface doesn't exist or lacks permissions

    Example:
        >>> devices = discover_devices("192.168.1.0/24", "eth0")
        >>> len(devices)
        15
        >>> devices[0].ip
        '192.168.1.1'
    """
    pass
```

### Module Docstrings

```python
"""
Network discovery service.

This module provides functions for discovering devices on a local network
using various methods:
- ARP scanning (requires root/CAP_NET_RAW)
- ICMP ping sweep (no special permissions)
- mDNS/Bonjour discovery (optional)

Example:
    from app.services.discovery import discover_devices

    devices = discover_devices("192.168.1.0/24", "eth0")
    for device in devices:
        print(f"{device.ip}: {device.mac}")
"""
```

### Class Docstrings

```python
class SQLiteInventoryRepository:
    """
    SQLite-based device inventory repository.

    Manages persistent storage of discovered network devices using SQLite.
    Provides CRUD operations and querying capabilities.

    Attributes:
        db_path: Path to SQLite database file
        _conn: SQLite connection object (private)

    Example:
        repo = SQLiteInventoryRepository("devices.db")
        device = repo.get_device("192.168.1.1")
        repo.upsert_device(device)
    """

    def __init__(self, db_path: str):
        """
        Initialize repository.

        Args:
            db_path: Path to SQLite database file
        """
        pass
```

## Code Organization

### Import Ordering

```python
# 1. Standard library imports
import os
import sys
from datetime import datetime
from typing import Optional, List

# 2. Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import scapy.all as scapy

# 3. Local application imports
from app.config import settings
from app.models.device import Device
from app.services.discovery import discover_devices
```

### File Structure

```python
"""Module docstring."""

# Imports
import ...

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 2.0

# Type aliases
DeviceDict = Dict[str, Device]

# Exception classes
class DiscoveryError(Exception):
    """Discovery operation failed."""
    pass

# Main classes
class DiscoveryService:
    """Service class."""
    pass

# Utility functions
def _parse_response(data: str) -> Dict:
    """Private utility function."""
    pass

# Public API functions
def discover_network(cidr: str) -> List[Device]:
    """Public API function."""
    pass

# Main execution guard
if __name__ == "__main__":
    # Script entry point
    pass
```

## Best Practices

### Error Handling

```python
# Specific exceptions
try:
    device = repo.get_device(device_id)
except DeviceNotFoundError as e:
    logger.warning(f"Device not found: {device_id}")
    raise HTTPException(status_code=404, detail=str(e))
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")

# Use context managers
with open("devices.json", "r") as f:
    data = json.load(f)

# Async context managers
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed diagnostic information")
logger.info("Normal operation information")
logger.warning("Warning: something unexpected")
logger.error("Error: operation failed")
logger.critical("Critical: system unstable")

# Include context
logger.info(f"Discovered {len(devices)} devices on {interface}")
logger.error(f"Failed to connect to {host}:{port}", exc_info=True)

# Avoid string formatting for disabled levels
logger.debug("Status: %s", expensive_operation())  # Only called if DEBUG enabled
```

### Configuration

```python
# Use Pydantic Settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    network_cidr: str = "192.168.1.0/24"
    interface: str = "eth0"
    snmp_community: str = "public"

    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton pattern
settings = Settings()
```

### Async Code

```python
# Use async/await consistently
async def fetch_devices() -> List[Device]:
    """Fetch devices asynchronously."""
    devices = []
    async for device in discover_async():
        devices.append(device)
    return devices

# Gather concurrent operations
results = await asyncio.gather(
    fetch_device("192.168.1.1"),
    fetch_device("192.168.1.2"),
    fetch_device("192.168.1.3"),
    return_exceptions=True
)

# Use timeouts
try:
    result = await asyncio.wait_for(
        slow_operation(),
        timeout=5.0
    )
except asyncio.TimeoutError:
    logger.warning("Operation timed out")
```

### Testing

```python
import pytest
from unittest.mock import Mock, patch

# Descriptive test names
def test_discover_devices_returns_list_of_devices():
    """Test that discover_devices returns a list of Device objects."""
    pass

# Use fixtures
@pytest.fixture
def mock_device():
    """Mock device for testing."""
    return Device(
        id="aa:bb:cc:dd:ee:ff",
        ip="192.168.1.100",
        mac="aa:bb:cc:dd:ee:ff"
    )

# Parametrize tests
@pytest.mark.parametrize("cidr,expected", [
    ("192.168.1.0/24", 256),
    ("10.0.0.0/16", 65536),
])
def test_calculate_network_size(cidr, expected):
    """Test network size calculation."""
    assert calculate_size(cidr) == expected
```

## Anti-Patterns to Avoid

### Don't

```python
# Magic numbers
timeout = 2
max_retries = 3

# Mutable default arguments
def process_devices(devices=[]):  # DON'T
    pass

# Bare except
try:
    risky_operation()
except:  # DON'T
    pass

# Type comments (use type hints)
device = get_device()  # type: Device  # DON'T
```

### Do

```python
# Named constants
TIMEOUT_SECONDS = 2
MAX_RETRIES = 3

# Immutable defaults
def process_devices(devices: Optional[List[Device]] = None):
    if devices is None:
        devices = []

# Specific exceptions
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Value error: {e}")

# Type hints
device: Device = get_device()
```

## Tools Configuration

### pyproject.toml

```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

## Related Documentation

- [Development Guide](10-development.md) - Development workflow
- [Contributing Guide](50-contributing.md) - Contribution guidelines
- [Testing Guide](12-testing.md) - Testing standards
