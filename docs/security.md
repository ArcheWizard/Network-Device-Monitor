# Security

## Current Security Measures

### Environment Security

- Store secrets in environment variables or a secret manager
- `.env` file excluded from version control via `.gitignore`
- Separate `.env.example` template for safe sharing

### Network Security

- Avoid binding API to public interfaces without auth
- SNMP v2c is plaintext; prefer v3 where possible (future work)
- Validate CIDR inputs to avoid scanning unintended networks
- scapy requires elevated privileges (CAP_NET_RAW) - use setcap, not sudo

### Input Validation

- FastAPI Pydantic models validate all API inputs
- CIDR validation prevents scanning unintended networks
- Type checking with mypy ensures type safety

## Planned Security Hardening (Milestone 5)

### Authentication & Authorization

**Priority:** HIGH

- **JWT-based authentication** for API endpoints
  - `/api/auth/login` - Issue JWT tokens
  - `/api/auth/refresh` - Refresh expired tokens
  - Protected routes require valid Bearer token
- **Role-based access control (RBAC)**
  - Admin role: full access to discovery, monitoring, configuration
  - Viewer role: read-only access to devices and metrics
  - Operator role: trigger scans, acknowledge alerts
- **WebSocket authentication**
  - Require JWT token for WebSocket connections
  - Connection-level authorization checks
- **API key support** for programmatic access
  - Generate, rotate, and revoke API keys
  - Rate limiting per key

### Transport Security

**Priority:** HIGH

- **TLS/HTTPS support**
  - Certificate management (Let's Encrypt integration)
  - Automatic HTTP→HTTPS redirect
  - HSTS headers for browsers
- **WebSocket over TLS (WSS)**
  - Encrypted real-time communication
- **Certificate pinning** for PyQt client (optional)

### SNMP Security

**Priority:** MEDIUM

- **SNMPv3 support**
  - Authentication: MD5/SHA
  - Privacy: DES/AES encryption
  - User-based security model (USM)
- **SNMP credential management**
  - Per-device credentials
  - Encrypted credential storage
  - Credential rotation

### Input Validation & Sanitization

**Priority:** HIGH

- **CIDR validation enhancement**
  - Block private/reserved ranges by default
  - Configurable allow/deny lists
  - Scan rate limiting
- **MAC address validation**
  - Format enforcement
  - Prevent MAC spoofing attacks
- **SQL injection prevention**
  - Parameterized queries (already using aiosqlite properly)
  - ORM validation via SQLAlchemy
- **Command injection prevention**
  - Sanitize inputs to ping/system commands
  - Use libraries instead of shell commands where possible

### Database Security

**Priority:** MEDIUM

- **SQLite encryption at rest**
  - SQLCipher integration
  - Key derivation from master password
- **InfluxDB security**
  - Token rotation
  - Least-privilege access tokens
  - Audit logging
- **Sensitive data handling**
  - Hash/encrypt SNMP community strings
  - Secure credential storage
  - PII handling compliance

### API Security

**Priority:** HIGH

- **Rate limiting**
  - Per-IP rate limits
  - Per-user rate limits
  - Adaptive rate limiting
- **CORS configuration**
  - Whitelist allowed origins
  - Credential handling
- **Request validation**
  - Size limits
  - Content-type validation
  - Request timeout enforcement
- **Security headers**
  - X-Content-Type-Options
  - X-Frame-Options
  - Content-Security-Policy

### Logging & Auditing

**Priority:** MEDIUM

- **Audit trail**
  - Log all authentication attempts
  - Log configuration changes
  - Log discovery scans initiated
  - Log device access attempts
- **Secure logging**
  - Sanitize sensitive data in logs
  - Log rotation and retention
  - Tamper-proof logging (write-once)
- **Security monitoring**
  - Failed authentication alerts
  - Unusual scanning patterns
  - Privilege escalation attempts

### Deployment Security

**Priority:** MEDIUM

- **Docker security**
  - Non-root containers
  - Minimal base images
  - Security scanning (Trivy/Snyk)
  - Secrets management via Docker secrets
- **Network isolation**
  - Separate networks for services
  - Firewall rules
  - No unnecessary port exposure
- **Dependency scanning**
  - Automated vulnerability scanning (Dependabot)
  - Regular dependency updates
  - SBOM generation

### Frontend Security

**Priority:** MEDIUM

- **PyQt application security**
  - Code signing for distributions
  - Secure update mechanism
  - Local credential storage (keyring)
- **Web frontend security** (future)
  - XSS prevention
  - CSRF tokens
  - Content Security Policy

## Security Best Practices

### Development

- Run security linters (bandit, safety)
- Code review for security issues
- Static analysis (mypy, ruff)
- Dependency vulnerability scanning

### Operations

- Principle of least privilege
- Regular security updates
- Backup and recovery procedures
- Incident response plan

### Compliance

- Data retention policies
- Privacy considerations (GDPR if applicable)
- Network scanning ethics and legal compliance

## Security Roadmap

### Phase 1: Core Security (Milestone 5)

- JWT authentication
- TLS/HTTPS support
- Rate limiting
- Enhanced input validation

### Phase 2: Advanced Security

- SNMPv3 support
- RBAC implementation
- Audit logging
- Database encryption

### Phase 3: Production Hardening

- Security monitoring and alerting
- Penetration testing
- Security certifications
- Compliance documentation

## Reporting Security Issues

If you discover a security vulnerability, please email <faress22.dadi@gmail.com> instead of using the public issue tracker.
