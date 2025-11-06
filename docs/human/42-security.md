# Security Best Practices

Security considerations and best practices for the Network Device Monitor.

## Overview

This document covers security considerations for deploying and operating the Network Device Monitor in production environments.

## Network Security

### Firewall Configuration

**Backend API:**
```bash
# Allow only necessary ports
sudo ufw allow 8000/tcp  # API/WebSocket
sudo ufw enable

# Or restrict to specific network
sudo ufw allow from 192.168.1.0/24 to any port 8000
```

**InfluxDB:**
```bash
# Restrict InfluxDB to localhost only
sudo ufw deny 8086
# Or allow from backend container
sudo ufw allow from 172.18.0.0/16 to any port 8086
```

### Network Isolation

**Docker networks:**
```yaml
networks:
  internal:
    internal: true  # No external access
  external:
    # Internet access

services:
  backend:
    networks:
      - internal
      - external

  influxdb:
    networks:
      - internal  # No direct internet access
```

### Privilege Management

**Capabilities:**
```yaml
services:
  backend:
    cap_drop:
      - ALL
    cap_add:
      - NET_RAW    # Required for ARP scanning
      - NET_ADMIN  # Required for network interface access
```

**Run as non-root:**
```dockerfile
# In Dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

## Authentication & Authorization

### API Authentication (Future Feature)

Currently no authentication. Planned features:

- **API Keys** - Token-based authentication
- **JWT Tokens** - JSON Web Tokens for session management
- **RBAC** - Role-based access control
- **OAuth2** - Third-party authentication

### Interim Security Measures

1. **Firewall rules** - Restrict access by IP
2. **VPN access** - Require VPN for access
3. **Reverse proxy** - Add authentication at proxy level

**Example with Nginx auth:**
```nginx
location / {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}
```

## Database Security

### SQLite Protection

**File permissions:**
```bash
# Restrict database file access
chmod 600 backend/data/devices.db
chown appuser:appuser backend/data/devices.db

# Restrict data directory
chmod 700 backend/data/
```

**Backup encryption:**
```bash
# Encrypt backups with GPG
gpg --symmetric --cipher-algo AES256 devices.db
```

### InfluxDB Security

**Token management:**
```bash
# Use environment variables, never hardcode
export INFLUX_TOKEN=$(cat /run/secrets/influx_token)

# Rotate tokens regularly
influx auth create \
  --org myorg \
  --all-access \
  --user admin
```

**Access control:**
```bash
# Create read-only token for monitoring
influx auth create \
  --org myorg \
  --read-bucket network_metrics \
  --user readonly-user
```

**Encryption at rest:**
```yaml
# InfluxDB config
storage-cache-max-memory-size: 1GB
storage-wal-fsync-delay: 0s
# Enable TLS
tls-cert: /path/to/cert.pem
tls-key: /path/to/key.pem
```

## SNMP Security

### Community Strings

**Never use default:**
```bash
# Change from "public"
SNMP_COMMUNITY=MySecureC0mmunity123

# Use different strings for different devices
```

**SNMPv3 (Future):**
```python
# Upgrade to SNMPv3 with authentication
from pysnmp.hlapi import *

errorIndication, errorStatus, errorIndex, varBinds = next(
    getCmd(SnmpEngine(),
           UsmUserData('username', 'authKey', 'privKey'),
           UdpTransportTarget(('192.168.1.1', 161)),
           ContextData(),
           ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0)))
)
```

### Network Segmentation

- Place monitoring system in management VLAN
- Restrict SNMP access with ACLs on devices
- Use read-only SNMP community strings

## Environment Variables

### Secure Storage

**Never commit secrets:**
```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "*.pem" >> .gitignore
```

**Use secrets management:**
```yaml
# Docker secrets
services:
  backend:
    secrets:
      - influx_token
    environment:
      INFLUX_TOKEN_FILE: /run/secrets/influx_token

secrets:
  influx_token:
    file: ./secrets/influx_token.txt
```

**Encryption:**
```bash
# Encrypt .env file
ansible-vault encrypt .env

# Decrypt when needed
ansible-vault decrypt .env
```

## Transport Security

### HTTPS/TLS

**Reverse proxy with SSL:**
```nginx
server {
    listen 443 ssl http2;
    server_name monitor.example.com;

    ssl_certificate /etc/letsencrypt/live/monitor.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/monitor.example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }
}
```

**WebSocket over TLS:**
```javascript
// Use wss:// instead of ws://
const ws = new WebSocket('wss://monitor.example.com/ws/stream');
```

### Certificate Management

```bash
# Auto-renewal with certbot
sudo certbot renew --dry-run

# Monitor expiration
openssl x509 -enddate -noout -in /etc/letsencrypt/live/monitor.example.com/cert.pem
```

## Input Validation

### API Validation

Already implemented with Pydantic:

```python
class Device(BaseModel):
    id: str = Field(..., pattern=r'^[0-9a-f:]{17}$')  # MAC address
    ip: str = Field(..., pattern=r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    hostname: Optional[str] = Field(None, max_length=255)
```

### Additional Validation

```python
# Validate CIDR notation
import ipaddress

def validate_cidr(cidr: str) -> bool:
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False

# Validate interface name
import re

def validate_interface(interface: str) -> bool:
    return bool(re.match(r'^[a-z0-9]+$', interface))
```

## Dependency Security

### Vulnerability Scanning

```bash
# Check for vulnerable dependencies
pip install safety
safety check

# Or use
pip install pip-audit
pip-audit

# GitHub Dependabot (automated)
# Enable in repository settings
```

### Dependency Pinning

```bash
# Pin exact versions
pip freeze > requirements/prod.txt

# Regular updates
pip install --upgrade pip
pip list --outdated
```

### Container Scanning

```bash
# Scan Docker images
docker scan backend:latest

# Or use Trivy
trivy image backend:latest
```

## Logging & Monitoring

### Security Logging

```python
# Log security events
import logging

logger = logging.getLogger(__name__)

# Log authentication attempts (future)
logger.warning(f"Failed authentication attempt from {ip}")

# Log SNMP failures
logger.warning(f"SNMP authentication failed for {device_ip}")

# Log unusual network activity
logger.warning(f"Port scan detected from {ip}")
```

### Log Protection

```bash
# Restrict log file access
chmod 640 /var/log/network-monitor/backend.log
chown appuser:appuser /var/log/network-monitor/backend.log

# Log rotation
cat > /etc/logrotate.d/network-monitor <<EOF
/var/log/network-monitor/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 640 appuser appuser
}
EOF
```

### Security Monitoring

```bash
# Monitor failed authentication (future)
tail -f /var/log/network-monitor/backend.log | grep "Failed authentication"

# Monitor SNMP failures
tail -f /var/log/network-monitor/backend.log | grep "SNMP.*failed"
```

## Container Security

### Base Image

```dockerfile
# Use minimal base image
FROM python:3.11-slim

# Update packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### Read-only Filesystem

```yaml
services:
  backend:
    read_only: true
    tmpfs:
      - /tmp
      - /app/data  # If needed
```

### Security Scanning

```bash
# Scan Dockerfile
hadolint docker/backend.Dockerfile

# Scan running containers
docker scan $(docker ps -q)
```

## Incident Response

### Preparation

1. **Backup strategy** - Regular automated backups
2. **Monitoring alerts** - Security event notifications
3. **Incident plan** - Documented response procedures
4. **Contact list** - Emergency contact information

### Detection

```bash
# Monitor logs for suspicious activity
grep -i "error\|failed\|denied" /var/log/network-monitor/backend.log

# Check for unauthorized access
last -a | grep -v "$(hostname)"

# Monitor network connections
netstat -tuln | grep ESTABLISHED
```

### Response

1. **Isolate** - Disconnect affected systems
2. **Investigate** - Review logs and activity
3. **Remediate** - Patch vulnerabilities
4. **Document** - Record incident details
5. **Review** - Update security measures

## Compliance

### Data Privacy

- **Personal data** - No PII collected by default
- **Network data** - IP/MAC addresses may be sensitive
- **Retention** - Configure appropriate retention policies
- **Access control** - Restrict access to authorized users

### Audit Trail

```python
# Log all administrative actions
logger.info(f"User {user} performed {action} on {resource}")

# Log configuration changes
logger.info(f"Configuration changed: {key} = {value}")

# Log data exports
logger.info(f"Data exported by {user}: {resource}")
```

## Security Checklist

- [ ] Change default SNMP community strings
- [ ] Configure firewall rules
- [ ] Use non-root user in containers
- [ ] Enable HTTPS/TLS
- [ ] Restrict database file permissions
- [ ] Encrypt backups
- [ ] Use Docker secrets for sensitive data
- [ ] Scan dependencies for vulnerabilities
- [ ] Enable security logging
- [ ] Configure log rotation
- [ ] Regular security updates
- [ ] Incident response plan documented
- [ ] Regular security audits scheduled

## Future Security Features

1. **API authentication** - Token-based auth
2. **User management** - Multi-user support
3. **Audit logging** - Comprehensive audit trail
4. **SNMPv3** - Encrypted SNMP queries
5. **2FA** - Two-factor authentication
6. **Rate limiting** - API rate limiting
7. **IP allowlist** - Restrict access by IP
8. **Webhook validation** - Verify webhook signatures

## Related Documentation

- [Configuration](03-configuration.md) - Environment setup
- [Deployment](30-deployment.md) - Production deployment
- [Database Management](32-database.md) - Database security
