# Changelog

All notable changes to the Network Device Monitor project.

## [Unreleased]

### Planned

- API authentication and authorization
- SNMPv3 support
- Email notifications
- React web UI
- Configuration backup

## [0.1.0] - 2024-01-15

### Added

- Initial MVP release
- Network device discovery via ARP, ICMP ping, and mDNS
- Device identification via OUI lookup, SNMP, and DNS
- Basic health monitoring with ping
- Time-series metrics storage in InfluxDB 2.x
- REST API with FastAPI
- WebSocket for real-time updates
- PyQt6 desktop frontend application
- SQLite database for device inventory
- Docker Compose deployment
- Comprehensive documentation (human and AI)

### Discovery Features

- ARP scanning for local network devices (requires privileges)
- ICMP ping sweep (fallback for WiFi interfaces)
- mDNS/Bonjour discovery for .local devices
- Automatic detection and handling of WiFi interfaces
- Configurable network CIDR and interface

### Identification Features

- OUI database lookup for vendor identification
- SNMP v2c queries for device information (sysName, sysDescr)
- DNS reverse lookup for hostnames
- Vendor caching for performance

### Monitoring Features

- Ping-based health monitoring
- Latency measurement in milliseconds
- Packet loss detection
- Device status tracking (up/down/unknown)
- Configurable alert thresholds
- Automatic monitoring schedule (60-second interval)

### API Endpoints

- `GET /health` - Health check
- `GET /api/devices` - List all devices
- `GET /api/devices/{device_id}` - Get device details
- `POST /api/devices/discover` - Trigger discovery
- `GET /api/metrics/latency` - Query latency metrics
- `WS /ws/stream` - WebSocket for real-time events

### WebSocket Events

- `hello` - Connection established
- `device_discovered` - New device found
- `device_up` - Device came online
- `device_down` - Device went offline
- `latency` - Latency measurement

### Frontend Features

- Desktop application with PyQt6
- Device list view with status
- Real-time updates via WebSocket
- Topology visualization (basic)
- Device detail view

### Database

- SQLite for persistent device storage
- InfluxDB 2.x for time-series metrics
- Automatic schema creation
- Data persistence across restarts

### Deployment

- Docker Compose configuration
- Configurable via environment variables
- Network interface and CIDR configuration
- SNMP community string configuration
- InfluxDB connection settings
- Alert threshold configuration

### Documentation

- Quick start guide
- Installation instructions
- Configuration guide
- Development guide
- Architecture documentation
- API reference
- Testing guide
- Feature guides (discovery, identification, monitoring, websocket)
- Deployment guide
- Troubleshooting guide
- Database management guide
- CLI commands reference
- Security best practices
- Contributing guide
- Code style guide
- Project roadmap
- FAQ
- Glossary
- AI-readable documentation (schemas, templates, examples)

### Testing

- Unit tests for core functionality
- Integration tests for API
- Test coverage reporting
- pytest configuration
- Mock fixtures for testing

### Developer Tools

- Makefile for common tasks
- Type checking with mypy
- Code formatting with black
- Linting with flake8
- Development requirements
- Debug logging support

### Known Limitations

- Single network (CIDR) support only
- No authentication/authorization
- SNMPv2c only (no v3)
- No alerting/notifications
- No web UI (desktop only)
- Limited horizontal scaling
- Basic topology visualization

### Known Issues

- ARP scanning may not work on WiFi interfaces
- mDNS discovery depends on network support
- High latency on congested networks
- Memory usage grows with device count

## [0.0.1] - 2023-12-01 (Internal)

### Added

- Initial project structure
- Basic FastAPI setup
- SQLite integration
- Simple device discovery prototype

---

## Version History

### Version Numbering

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR** - Incompatible API changes
- **MINOR** - Backwards-compatible new features
- **PATCH** - Backwards-compatible bug fixes

### Release Types

- **Stable releases** - Production-ready (e.g., 0.1.0)
- **Pre-releases** - Testing versions (e.g., 0.2.0-beta.1)
- **Development** - Unreleased features (main branch)

### Support Policy

- **Latest stable** - Full support with updates
- **Previous minor** - Security fixes for 3 months
- **Older versions** - No support

### Upgrade Notes

#### Upgrading to 0.1.0

First release - no upgrade path needed.

## Contributing

Found a bug or want to suggest a change to the changelog?

- Report issues on GitHub
- Submit corrections via pull request
- Follow [Keep a Changelog](https://keepachangelog.com/) format

## Categories

Changes are grouped by:

- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security fixes

## Links

- [Source Code](https://github.com/yourusername/network-device-monitor)
- [Issue Tracker](https://github.com/yourusername/network-device-monitor/issues)
- [Releases](https://github.com/yourusername/network-device-monitor/releases)
- [Roadmap](52-roadmap.md)
- [Contributing](50-contributing.md)

## Related Documentation

- [Roadmap](52-roadmap.md) - Future planned features
- [FAQ](60-faq.md) - Frequently asked questions
- [Contributing](50-contributing.md) - How to contribute
