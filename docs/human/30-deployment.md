# Deployment Guide

Production deployment guide for the Network Device Monitor.

## Overview

This guide covers deploying the application in production environments using Docker Compose.

## Prerequisites

- Docker 20.10+ and Docker Compose v2+
- Network access to monitored subnet
- InfluxDB 2.x instance (or deploy with compose)
- 2GB+ RAM recommended

## Docker Deployment

### Standard Deployment

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/network-device-monitor.git
cd network-device-monitor
```

2. **Create environment file:**

```bash
cp .env.example .env
nano .env
```

Configure required variables:

```bash
# Network Configuration
NETWORK_CIDR=192.168.1.0/24
INTERFACE=eth0

# SNMP Configuration
SNMP_COMMUNITY=public

# InfluxDB Configuration
INFLUX_URL=http://influxdb:8086
INFLUX_TOKEN=your-influx-token
INFLUX_ORG=myorg
INFLUX_BUCKET=network_metrics

# Alert Thresholds
ALERT_LATENCY_MS=200.0
ALERT_PACKET_LOSS=0.5
```

3. **Start services:**

```bash
docker-compose -f docker/docker-compose.yml up -d
```

4. **Verify deployment:**

```bash
# Check container status
docker ps

# View logs
docker-compose -f docker/docker-compose.yml logs -f backend

# Test API
curl http://localhost:8000/health
```

### With External InfluxDB

If using an existing InfluxDB instance:

```yaml
# docker/docker-compose.yml
services:
  backend:
    # ... other config
    environment:
      - INFLUX_URL=https://influxdb.example.com
      - INFLUX_TOKEN=${INFLUX_TOKEN}
      - INFLUX_ORG=${INFLUX_ORG}
      - INFLUX_BUCKET=${INFLUX_BUCKET}
```

## Network Configuration

### Host Network Mode

For direct network access (required for ARP scanning):

```yaml
services:
  backend:
    network_mode: host
    cap_add:
      - NET_RAW
      - NET_ADMIN
```

### Bridge Mode with Macvlan

For isolated network with direct device access:

```yaml
networks:
  monitored_network:
    driver: macvlan
    driver_opts:
      parent: eth0
    ipam:
      config:
        - subnet: 192.168.1.0/24
          gateway: 192.168.1.1

services:
  backend:
    networks:
      - monitored_network
```

## Reverse Proxy Setup

### Nginx

```nginx
server {
    listen 80;
    server_name monitor.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Traefik

```yaml
services:
  backend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.monitor.rule=Host(`monitor.example.com`)"
      - "traefik.http.services.monitor.loadbalancer.server.port=8000"
```

## SSL/TLS Configuration

### Using Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d monitor.example.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Using Let's Encrypt with Traefik

```yaml
services:
  traefik:
    command:
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"

  backend:
    labels:
      - "traefik.http.routers.monitor.tls.certresolver=letsencrypt"
```

## Data Persistence

### Volumes

Ensure data persists across restarts:

```yaml
services:
  backend:
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  influxdb:
    volumes:
      - influxdb_data:/var/lib/influxdb2

volumes:
  influxdb_data:
```

### Backup Strategy

```bash
# Backup SQLite database
docker cp backend:/app/data/devices.db ./backups/devices-$(date +%Y%m%d).db

# Backup InfluxDB
docker exec influxdb influx backup /backup/influxdb-$(date +%Y%m%d)
docker cp influxdb:/backup/influxdb-$(date +%Y%m%d) ./backups/
```

## Monitoring and Logging

### Centralized Logging

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Health Checks

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## Scaling Considerations

### Horizontal Scaling

Not currently supported (single-instance scheduler). Future feature.

### Vertical Scaling

Adjust resource limits:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Security Hardening

1. **Use non-root user:**

```dockerfile
USER appuser
```

2. **Read-only filesystem:**

```yaml
services:
  backend:
    read_only: true
    tmpfs:
      - /tmp
```

3. **Drop capabilities:**

```yaml
services:
  backend:
    cap_drop:
      - ALL
    cap_add:
      - NET_RAW
      - NET_ADMIN
```

4. **Network isolation:**

```yaml
networks:
  internal:
    internal: true
  external:
```

## Updates and Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose -f docker/docker-compose.yml build

# Restart services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

### Database Migrations

Currently no migration system. Future feature.

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs backend

# Check resource availability
docker stats

# Verify environment variables
docker exec backend env
```

### Network Discovery Not Working

- Verify `NET_RAW` and `NET_ADMIN` capabilities
- Check `INTERFACE` environment variable
- Ensure network_mode is appropriate

### InfluxDB Connection Failed

```bash
# Test connection from container
docker exec backend curl -v $INFLUX_URL/health

# Check InfluxDB logs
docker logs influxdb
```

## Related Documentation

- [Configuration](03-configuration.md) - Environment variables
- [Troubleshooting](31-troubleshooting.md) - Common issues
- [Database Management](32-database.md) - Data management
