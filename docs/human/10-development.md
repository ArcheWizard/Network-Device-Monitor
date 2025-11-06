# Development Guide

Guide for setting up a development environment and contributing to the project.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Debugging](#debugging)
- [Hot Reload](#hot-reload)

## Prerequisites

### Required Tools

- **Python 3.11+**
- **Git**
- **Make** (for automation tasks)
- **Docker** (optional, for integration testing)

### Recommended Tools

- **mise**: Python version management
- **VSCode**: IDE with Python extension
- **Postman/HTTPie**: API testing
- **InfluxDB**: Local time-series database

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd Network-Device-Monitor
```

### 2. Install Python Dependencies

#### Using mise (Recommended)

```bash
# Install mise
curl https://mise.run | sh

# Install Python automatically from mise.toml
mise install

# Verify installation
python --version  # Should be 3.11+
```

#### Manual Setup

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Development Dependencies

```bash
cd backend
pip install -r requirements/dev.txt
```

This installs:

- **Production dependencies** (`base.txt`)
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Linting**: ruff, mypy
- **Type checking**: mypy types
- **Development tools**: ipython, pre-commit

### 4. Configure Environment

```bash
# Copy example configuration
cp backend/.env.example backend/.env

# Edit with your settings
nano backend/.env
```

Development `.env`:

```env
NETWORK_CIDR=192.168.1.0/24
INTERFACE=
SNMP_COMMUNITY=public
LOG_LEVEL=DEBUG
```

### 5. Install Pre-commit Hooks

```bash
# From repository root
pre-commit install

# Test hooks
pre-commit run --all-files
```

Pre-commit runs:

- `ruff check` - Linting
- `ruff format` - Code formatting
- `mypy` - Type checking

### 6. Setup OUI Database (Optional)

```bash
# Download OUI data for MAC vendor lookup
bash scripts/seed_oui.sh
```

## Project Structure

```
Network-Device-Monitor/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # REST API routes
│   │   │   └── routers/  # Endpoint definitions
│   │   ├── models/       # Pydantic models
│   │   ├── scheduler/    # Background jobs
│   │   ├── services/     # Business logic
│   │   ├── storage/      # Data persistence
│   │   └── utils/        # Helper functions
│   ├── tests/            # Unit & integration tests
│   └── requirements/     # Dependency specifications
├── frontend/
│   └── pyqt/             # PyQt6 desktop app
├── docker/               # Container definitions
├── docs/                 # Documentation
│   ├── human/            # Human-readable docs
│   └── ai/               # AI-consumable specs
└── scripts/              # Utility scripts
```

### Key Files

- `backend/app/main.py`: Application entry point
- `backend/app/config.py`: Configuration management
- `backend/app/api/routers/`: API endpoint definitions
- `backend/app/services/`: Core business logic
- `backend/tests/`: Test suite

## Development Workflow

### Starting the Backend

```bash
# From backend directory
cd backend

# Method 1: Direct execution
python -m app.main

# Method 2: Using Make
make run

# Method 3: With hot reload (uvicorn)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend starts at `http://localhost:8000`

### API Documentation

Once running, access interactive API docs:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Starting the Frontend

```bash
cd frontend/pyqt
python src/app.py
```

## Testing

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_discovery_api.py

# Run specific test
pytest tests/test_discovery_api.py::test_discover_devices

# Run with output
pytest -v -s

# Run integration tests only
pytest -m integration

# Run unit tests only
pytest -m "not integration"
```

### Test Organization

```
tests/
├── test_api_smoke.py          # Basic API health checks
├── test_discovery_api.py      # Discovery endpoint tests
├── test_discovery_persistence.py  # Database integration
├── test_identification.py     # SNMP & OUI tests
├── test_monitoring.py         # Monitoring logic tests
├── test_sqlite_repo.py        # Repository tests
└── test_websocket.py          # WebSocket tests
```

### Writing Tests

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Test client for API calls."""
    return TestClient(app)

def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_async_function():
    """Test async code."""
    result = await some_async_function()
    assert result is not None
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html
```

Target: **>80% coverage** for critical paths

## Code Quality

### Linting with Ruff

```bash
cd backend

# Check for issues
make lint
# or
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking with MyPy

```bash
cd backend

# Run type checker
make typecheck
# or
mypy app/

# Check specific file
mypy app/services/discovery.py
```

### Pre-commit Checks

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Skip hooks for commit (not recommended)
git commit --no-verify
```

### Code Style Guidelines

- **Line length**: 100 characters
- **Imports**: Sorted with isort
- **Docstrings**: Google style
- **Type hints**: Required for public APIs
- **Async**: Use async/await for I/O operations

Example:

```python
async def discover_devices(network: str) -> list[Device]:
    """
    Discover devices on the network.

    Args:
        network: CIDR notation network address (e.g., "192.168.1.0/24")

    Returns:
        List of discovered devices

    Raises:
        ValueError: If network CIDR is invalid
    """
    # Implementation
    pass
```

## Debugging

### VSCode Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend",
      "type": "python",
      "request": "launch",
      "module": "app.main",
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    },
    {
      "name": "Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v", "-s"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Debug Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use throughout code
logger.debug("Detailed diagnostic information")
logger.info("General informational messages")
logger.warning("Warning messages")
logger.error("Error messages")
logger.exception("Error with stack trace")
```

### Interactive Debugging

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in (Python 3.7+)
breakpoint()
```

### Remote Debugging

For debugging in containers:

```python
import debugpy

debugpy.listen(("0.0.0.0", 5678))
debugpy.wait_for_client()  # Blocks until debugger attaches
```

## Hot Reload

### Backend Hot Reload

```bash
# Use uvicorn with --reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Changes to `.py` files trigger automatic restart.

**Note**: Background jobs (APScheduler) restart on reload, which may cause duplicate discovery tasks. For development, consider disabling scheduler temporarily.

### Frontend Hot Reload

PyQt6 doesn't support hot reload. Use rapid restart:

```bash
# Quick restart script
while true; do
  python src/app.py
  echo "Restarting in 2 seconds... (Ctrl+C to stop)"
  sleep 2
done
```

## Makefile Targets

Common development tasks:

```bash
# Backend tasks
cd backend

make run          # Start backend
make test         # Run tests
make lint         # Run linter
make format       # Format code
make typecheck    # Run type checker
make coverage     # Generate coverage report
make clean        # Clean cache files

# Root tasks
cd ..
make help         # Show all targets
```

## Development Tips

### 1. Use Virtual Environment

Always activate venv before working:

```bash
source venv/bin/activate
```

### 2. Keep Dependencies Updated

```bash
pip install --upgrade -r requirements/dev.txt
```

### 3. Commit Often

Make small, focused commits:

```bash
git add -p  # Stage changes interactively
git commit -m "feat: add device discovery caching"
```

### 4. Write Tests First (TDD)

1. Write failing test
2. Implement minimum code to pass
3. Refactor
4. Repeat

### 5. Check Before Pushing

```bash
# Run full validation
make lint && make typecheck && make test

# Or use pre-commit
pre-commit run --all-files
```

## Common Tasks

### Adding a New API Endpoint

1. Define route in `backend/app/api/routers/`
2. Implement business logic in `backend/app/services/`
3. Add tests in `backend/tests/`
4. Update documentation

### Adding a New Model

1. Create Pydantic model in `backend/app/models/`
2. Add database migration if needed
3. Update repository in `backend/app/storage/`
4. Add validation tests

### Adding a New Service

1. Create service file in `backend/app/services/`
2. Define interface with type hints
3. Implement business logic
4. Add unit tests with mocks
5. Add integration tests

## Troubleshooting

### Tests Fail with Import Errors

```bash
# Install in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/backend"
```

### Type Checker Complaints

```bash
# Install stub packages
pip install types-requests types-python-dateutil

# Check mypy.ini configuration
cat backend/mypy.ini
```

### Pre-commit Hooks Fail

```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall
pre-commit install --install-hooks
```

## Next Steps

- [Architecture](11-architecture.md) - System design overview
- [Testing Guide](12-testing.md) - Comprehensive testing documentation
- [Code Style](51-code-style.md) - Detailed coding standards
- [Contributing](50-contributing.md) - Contribution guidelines
