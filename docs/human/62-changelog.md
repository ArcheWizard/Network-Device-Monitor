# Changelog

All notable changes to the Network Device Monitor project.

## [Unreleased]

### Planned

- SNMPv3 support
- Email/Slack notifications
- Network topology visualization
- React web UI
- Configuration backup

## [0.2.0] - 2025-11-07

### Added - Authentication & Security

- **JWT Token Authentication** - Secure token-based API authentication
  - Token generation and validation
  - Configurable token expiration (default: 1 hour)
  - Bearer token scheme with HTTP Authorization header
- **User Management System** - Complete user lifecycle management
  - User registration with validation
  - User login with JWT token issuance
  - Get current user information endpoint
  - List, view, update, and delete users (admin only)
  - Password strength validation (8+ chars, mixed case, numbers)
  - Unique username and email constraints
- **Role-Based Access Control (RBAC)** - Three-tier permission system
  - **Admin** - Full system access, user management
  - **Operator** - Device management, discovery operations
  - **Viewer** - Read-only access to all data
- **Password Security** - Industry-standard hashing
  - Bcrypt password hashing
  - Salt generation for each password
  - Secure password verification
- **Database Schema** - User storage
  - Users table with SQLite
  - Indexed username and email for fast lookups
  - Created/updated/last_login timestamps
  - User activation status
- **Configuration Options** - Flexible authentication setup
  - `REQUIRE_AUTH` - Enable/disable authentication (default: false)
  - `JWT_SECRET_KEY` - Signing key for tokens (auto-generated)
  - `JWT_ALGORITHM` - Token signing algorithm (HS256)
  - `JWT_EXPIRATION_MINUTES` - Token lifetime (default: 60)
- **API Endpoints** - Complete auth REST API
  - `POST /api/auth/register` - Register new user
  - `POST /api/auth/login` - Authenticate and get token
  - `GET /api/auth/me` - Get current user info
  - `GET /api/auth/users` - List all users (admin)
  - `GET /api/auth/users/{id}` - Get user by ID (admin)
  - `PATCH /api/auth/users/{id}` - Update user (admin)
  - `DELETE /api/auth/users/{id}` - Delete user (admin)
- **API Dependencies** - Reusable auth middleware
  - `get_current_user` - Optional authentication
  - `require_auth` - Enforce authentication
  - `require_role()` - Role-based authorization
  - `require_admin` - Admin-only access
  - `require_operator` - Operator+ access
  - `require_viewer` - Any authenticated user

### Added - Testing & Documentation

- **Authentication Tests** - Comprehensive test suite (test_auth.py)
  - User registration tests (success, duplicate, validation)
  - Login tests (success, wrong password, nonexistent user)
  - Token validation tests
  - Protected endpoint tests
  - Role-based access control tests
  - Password hashing tests
- **Authentication Documentation** - Complete user guide (43-authentication.md)
  - Quick start guide
  - User roles and permissions
  - User management operations
  - Configuration options
  - Security best practices
  - Python and JavaScript client examples
  - Troubleshooting guide
  - Migration guide from v0.1.0
- **Database Migration** - Automated schema updates
  - Migration system for schema versioning
  - Migration script for v0 → v1 (users table)
  - Standalone migration tool (scripts/migrate_db.py)
  - Backward compatible with v0.1.0 databases

### Changed

- **Version Bump** - Application version updated to 0.2.0
- **Database Initialization** - Now returns both device and user repositories
- **API Main** - Includes authentication router
- **Dependencies** - Added authentication libraries
  - python-jose[cryptography]==3.3.0 (JWT handling)
  - passlib[bcrypt]==1.7.4 (password hashing)
  - python-multipart==0.0.9 (form data parsing)

### Backward Compatibility

- **Optional Authentication** - Authentication disabled by default
  - Existing deployments continue to work without changes
  - Can be enabled with `REQUIRE_AUTH=true` when ready
- **Database Migration** - Automatic schema updates
  - Users table created automatically on first run
  - No manual intervention required
  - Safe for existing databases

### Security Notes

- Default JWT secret key is auto-generated (secure random)
- **Production deployment**: Set custom `JWT_SECRET_KEY` in .env
- **HTTPS recommended**: Always use HTTPS in production
- Token storage: Use secure methods (httpOnly cookies, not localStorage)
- First user registration: Always allowed to bootstrap admin account

### Known Limitations

- No token refresh mechanism (users must re-authenticate after expiration)
- No password reset functionality
- No email verification
- No 2FA/MFA support
- No session management (stateless tokens only)
- No rate limiting on authentication endpoints

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
