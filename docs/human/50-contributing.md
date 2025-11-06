# Contributing Guide

Guidelines for contributing to the Network Device Monitor project.

## Welcome

Thank you for considering contributing to the Network Device Monitor! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Docker (for testing deployments)
- Basic knowledge of networking concepts

### Development Setup

1. **Fork and clone:**

```bash
git clone https://github.com/YOUR_USERNAME/network-device-monitor.git
cd network-device-monitor
```

2. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

3. **Install dependencies:**

```bash
cd backend
pip install -r requirements/dev.txt
```

4. **Set up InfluxDB (Docker):**

```bash
docker-compose -f docker/docker-compose.yml up -d influxdb
```

5. **Configure environment:**

```bash
cp .env.example .env
nano .env  # Edit configuration
```

6. **Run tests:**

```bash
pytest
```

## How to Contribute

### Reporting Bugs

**Before submitting:**

- Check existing issues for duplicates
- Test with the latest version
- Collect diagnostic information

**Bug report should include:**

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Relevant logs and error messages

**Example bug report:**

```markdown
## Description
Discovery scan fails on WiFi interfaces

## Steps to Reproduce
1. Configure `INTERFACE=wlan0`
2. Run discovery: `curl -X POST http://localhost:8000/api/devices/discover`
3. Check logs

## Expected Behavior
Devices should be discovered using ICMP fallback

## Actual Behavior
Discovery returns empty list

## Environment
- OS: Ubuntu 22.04
- Python: 3.11.2
- Interface: wlan0 (WiFi)

## Logs
```

WARNING: arp_scan may not work on WiFi

```
```

### Suggesting Features

**Feature request should include:**

- Clear description of the feature
- Use case and motivation
- Proposed implementation (if any)
- Potential challenges or concerns

**Example feature request:**

```markdown
## Feature: SNMPv3 Support

### Description
Add support for SNMPv3 with authentication and encryption

### Motivation
SNMPv2c community strings are insecure. SNMPv3 provides authentication and encryption.

### Proposed Implementation
- Add SNMPv3 configuration options
- Update SNMP client to support USM authentication
- Add UI fields for SNMPv3 credentials

### Challenges
- Backward compatibility with SNMPv2c
- Credential management complexity
```

### Pull Requests

**Before starting work:**

1. Check if an issue exists, or create one
2. Comment on the issue to claim it
3. Discuss approach with maintainers

**PR process:**

1. **Create a branch:**

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

2. **Make changes:**

- Write code following style guidelines
- Add tests for new functionality
- Update documentation

3. **Test your changes:**

```bash
# Run tests
pytest

# Check types
mypy app/

# Lint code
flake8 app/ tests/

# Format code
black app/ tests/
```

4. **Commit with clear messages:**

```bash
git commit -m "feat: add SNMPv3 authentication support"
git commit -m "fix: discovery fails on WiFi interfaces"
git commit -m "docs: update installation instructions"
```

5. **Push and create PR:**

```bash
git push origin feature/your-feature-name
```

6. **PR description should include:**

- Link to related issue
- Summary of changes
- Testing performed
- Screenshots (if UI changes)

**PR template:**

```markdown
## Description
Brief description of changes

Fixes #123

## Changes
- Added SNMPv3 authentication
- Updated configuration schema
- Added tests for SNMPv3

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing performed
- [ ] Documentation updated

## Screenshots
(if applicable)
```

## Development Guidelines

### Code Style

**Follow PEP 8:**

- Use 4 spaces for indentation
- Maximum line length: 88 characters (black default)
- Use meaningful variable names
- Add docstrings to functions and classes

**Example:**

```python
def discover_devices(
    cidr: str,
    interface: str,
    timeout: float = 2.0
) -> list[Device]:
    """
    Discover devices on the network.

    Args:
        cidr: Network CIDR notation (e.g., "192.168.1.0/24")
        interface: Network interface name (e.g., "eth0")
        timeout: Timeout in seconds for each probe

    Returns:
        List of discovered devices

    Raises:
        ValueError: If CIDR format is invalid
        NetworkError: If interface doesn't exist
    """
    # Implementation
    pass
```

### Type Hints

Always use type hints:

```python
from typing import Optional, List, Dict
from datetime import datetime

def process_device(
    device_id: str,
    ip: str,
    discovered_at: datetime,
    metadata: Optional[Dict[str, str]] = None
) -> Device:
    """Process and validate discovered device."""
    # Implementation
    pass
```

### Testing

**Write tests for:**

- New features
- Bug fixes
- Edge cases

**Test structure:**

```python
import pytest
from app.services.discovery import discover_devices

def test_discover_devices_success():
    """Test successful device discovery."""
    devices = discover_devices("192.168.1.0/24", "eth0")
    assert len(devices) > 0
    assert all(d.ip.startswith("192.168.1.") for d in devices)

def test_discover_devices_invalid_cidr():
    """Test discovery with invalid CIDR."""
    with pytest.raises(ValueError):
        discover_devices("invalid", "eth0")

@pytest.mark.integration
def test_discover_devices_integration():
    """Integration test requiring real network."""
    # Skipped in CI if network not available
    devices = discover_devices("192.168.1.0/24", "eth0")
    assert isinstance(devices, list)
```

### Documentation

**Update documentation when:**

- Adding new features
- Changing APIs
- Updating configuration
- Fixing bugs that affect usage

**Documentation locations:**

- `docs/human/` - User-facing documentation
- `docs/ai/` - Machine-readable schemas
- `README.md` - Project overview
- Code docstrings - Inline documentation

### Commit Messages

**Format:**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```bash
feat(discovery): add mDNS device discovery

Add support for mDNS/Bonjour device discovery using zeroconf library.
Automatically enabled when available.

Closes #45

---

fix(monitoring): handle ICMP timeout correctly

Previously, ping timeouts were not caught, causing monitoring to fail.
Now properly catches timeout and marks device as down.

Fixes #67

---

docs(api): update WebSocket message format

Update documentation to reflect new message structure with timestamps.
```

## Areas to Contribute

### High Priority

- [ ] API authentication and authorization
- [ ] SNMPv3 support
- [ ] Horizontal scaling support
- [ ] Performance optimizations
- [ ] Mobile-friendly web UI

### Medium Priority

- [ ] Additional discovery methods (LLDP, CDP)
- [ ] Device configuration backup
- [ ] Alerting and notifications
- [ ] Export/import functionality
- [ ] Network topology visualization

### Good First Issues

- [ ] Improve error messages
- [ ] Add more unit tests
- [ ] Documentation improvements
- [ ] Code cleanup and refactoring
- [ ] Update OUI database automatically

## Review Process

1. **Automated checks:**
   - Tests must pass
   - Code style checks must pass
   - Type checking must pass

2. **Code review:**
   - At least one approval required
   - Address reviewer feedback
   - Update as needed

3. **Merge:**
   - Squash and merge (default)
   - Delete branch after merge

## Getting Help

**Questions about:**

- **Development:** Open a discussion on GitHub
- **Bug reports:** Open an issue
- **Feature requests:** Open an issue with "enhancement" label
- **Security issues:** Email maintainers privately

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Credited in release notes
- Thanked in the community!

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Thank You

Your contributions make this project better for everyone. We appreciate your time and effort!

## Related Documentation

- [Development Guide](10-development.md) - Development workflow
- [Code Style Guide](51-code-style.md) - Detailed style guidelines
- [Testing Guide](12-testing.md) - Testing best practices
- [Architecture](11-architecture.md) - System architecture
