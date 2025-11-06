# Frequently Asked Questions (FAQ)

Common questions and answers about the Network Device Monitor.

## General Questions

### What is Network Device Monitor?

Network Device Monitor is an open-source network monitoring tool that discovers, identifies, and monitors devices on your local network. It provides real-time visibility into device health and network metrics.

### Who is this tool for?

- **Home Lab Enthusiasts** - Monitor your home network and lab equipment
- **Small Businesses** - Keep track of network devices and connectivity
- **IT Students** - Learn network monitoring and management
- **Network Administrators** - Simple monitoring for small deployments

### What makes this different from other network monitoring tools?

- **Lightweight** - Minimal resource requirements
- **Easy Setup** - Docker-based deployment in minutes
- **No Agents** - Discovers devices without installing software
- **Open Source** - Free to use and modify
- **Modern Stack** - FastAPI, InfluxDB, PyQt6

## Installation & Setup

### What are the system requirements?

**Minimum:**

- Python 3.11+
- 1GB RAM
- 5GB disk space
- Network interface with connectivity

**Recommended:**

- Python 3.11+
- 2GB RAM
- 10GB disk space
- Dedicated network interface

### Can I run this on a Raspberry Pi?

Yes! It runs well on Raspberry Pi 4 with 2GB+ RAM. Use Docker for easier deployment:

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Do I need root/admin privileges?

**For ARP scanning:** Yes, requires root or `CAP_NET_RAW` capability

**For ICMP ping:** No, works without special privileges

**Using Docker:** Handles permissions automatically

### Can I monitor multiple networks?

Currently, only one network (CIDR) is supported per instance. For multiple networks:

- Run multiple instances with different configurations
- Or use a network interface connected to all subnets

## Discovery & Identification

### Why aren't all my devices discovered?

Common reasons:

- **Firewall** - Devices may block ICMP/ARP
- **WiFi Isolation** - Some routers isolate wireless clients
- **Network Segmentation** - Devices on different VLANs
- **Wrong CIDR** - Check your network range

Try:

```bash
# Verify CIDR covers your network
# For 192.168.1.x network, use:
NETWORK_CIDR=192.168.1.0/24
```

### Why does discovery take so long?

Discovery speed depends on:

- **Network size** - Larger CIDRs take longer
- **Device response time** - Slow devices delay discovery
- **Network latency** - High latency increases scan time

Optimize by:

- Using smaller CIDR ranges
- Adjusting timeout values
- Running discovery off-peak hours

### Why is the vendor showing as "Unknown"?

Possible reasons:

- **OUI database not updated** - Run `./scripts/seed_oui.sh`
- **Private/Random MAC** - Some devices use randomized MACs
- **New vendor** - OUI database may not have entry

### What is OUI and why does it matter?

OUI (Organizationally Unique Identifier) is the first half of a MAC address that identifies the manufacturer. Used to determine device vendor (e.g., "Apple Inc", "Samsung").

### Why doesn't SNMP work for all devices?

SNMP must be:

- **Enabled** on the device
- **Configured** with same community string
- **Accessible** from monitoring system

Check:

```bash
# Test SNMP manually
snmpwalk -v2c -c public 192.168.1.1 system
```

## Monitoring & Metrics

### How often are devices monitored?

Default: Every 60 seconds

Configure in scheduler (future configuration option).

### Why are latency values so high?

Possible causes:

- **Network congestion** - Heavy traffic
- **Device load** - Device is busy
- **Network path** - Multiple hops
- **System load** - Monitoring system is busy

Troubleshoot:

```bash
# Test manually
ping -c 10 192.168.1.1

# Check network path
traceroute 192.168.1.1
```

### How long are metrics stored?

Default: InfluxDB retention policy (usually infinite)

Configure retention:

```bash
influx bucket update \
  --name network_metrics \
  --retention 30d
```

### Can I export metrics?

Yes! Export via:

- **InfluxDB UI** - Query and download
- **API** - Fetch via REST API
- **CLI** - Use InfluxDB CLI to export

Example:

```bash
curl "http://localhost:8000/api/metrics/latency?device_id=192.168.1.1&start=-24h"
```

## Performance

### How many devices can it monitor?

Tested up to:

- **100 devices** - Comfortably on standard hardware
- **500 devices** - Possible with optimization
- **1000+ devices** - Requires horizontal scaling (roadmap)

### Why is CPU usage high?

Common causes:

- **Large network** - Too many devices
- **Short interval** - Monitoring too frequently
- **Inefficient queries** - Database queries need optimization

Solutions:

- Increase monitoring interval
- Reduce network size (CIDR)
- Optimize database queries

### Why is memory usage growing?

Possible memory leak. Report as bug with:

- Memory usage graph
- Time running
- Number of devices
- Python version

## WebSocket & Real-time Updates

### WebSocket connection keeps dropping

Check:

- **Firewall** - May block WebSocket connections
- **Proxy** - Reverse proxy may need WebSocket config
- **Timeout** - Increase timeout values

Nginx WebSocket config:

```nginx
location /ws/ {
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### Why aren't updates real-time?

WebSocket sends updates when events occur:

- **Device discovered** - During discovery scan
- **Status change** - When device goes up/down
- **Metrics** - After each monitoring cycle

If nothing changes, no messages sent.

## Database & Storage

### How much disk space is needed?

Depends on:

- **Number of devices**
- **Monitoring interval**
- **Retention period**

Estimate:

- SQLite: ~1KB per device (~100KB for 100 devices)
- InfluxDB: ~100KB per device per day (~10MB for 100 devices/day)

### Can I use external InfluxDB?

Yes! Configure in `.env`:

```bash
INFLUX_URL=https://influxdb.example.com
INFLUX_TOKEN=your-token
INFLUX_ORG=your-org
INFLUX_BUCKET=network_metrics
```

### How do I backup databases?

**SQLite:**

```bash
sqlite3 backend/data/devices.db ".backup 'backup/devices.db'"
```

**InfluxDB:**

```bash
influx backup /path/to/backup \
  --host http://localhost:8086 \
  --token your-token
```

See [Database Management](32-database.md) for details.

## Troubleshooting

### "No module named 'app'" error

Ensure you're running from the correct directory:

```bash
cd backend
python -m app.main
```

Or adjust PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"
```

### "InfluxDB connection failed" error

Check:

1. InfluxDB is running: `curl http://localhost:8086/health`
2. Token is valid: Check InfluxDB UI
3. Environment variables: `echo $INFLUX_TOKEN`

### Frontend can't connect to backend

Verify:

1. Backend is running: `curl http://localhost:8000/health`
2. Firewall allows connections
3. Correct host/port in frontend config

### Discovery returns empty list

Debug steps:

1. Check network interface: `ip addr show`
2. Verify CIDR: Ensure it covers your network
3. Test permissions: May need root for ARP
4. Check logs for errors

See [Troubleshooting Guide](31-troubleshooting.md) for more.

## Security

### Is there authentication?

Not yet. Planned for v0.2.0. Current workarounds:

- Firewall rules to restrict access
- VPN for remote access
- Reverse proxy with authentication

### Is data encrypted?

- **In transit:** Use HTTPS/TLS with reverse proxy
- **At rest:** Database files not encrypted by default
- **Backups:** Encrypt with GPG or similar

See [Security Guide](42-security.md).

### Can I use SNMPv3?

Not yet. Currently only SNMPv2c is supported. SNMPv3 is on the roadmap for v0.2.0.

## Development

### How can I contribute?

See [Contributing Guide](50-contributing.md) for:

- Development setup
- Coding standards
- Pull request process
- Areas needing help

### Where can I report bugs?

GitHub Issues: <https://github.com/yourusername/network-device-monitor/issues>

Include:

- Description of issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Logs

### How do I request features?

Open a feature request on GitHub Issues with:

- Description of feature
- Use case
- Why it's valuable
- Proposed implementation (optional)

### Can I use this commercially?

Yes! It's open source (check LICENSE file for specific terms). You can:

- Use in commercial environments
- Modify and redistribute
- Integrate into products

Please:

- Comply with license terms
- Consider contributing improvements back
- Give credit where appropriate

## Deployment

### Can I deploy to cloud platforms?

Yes! Works on:

- **AWS** - EC2, ECS, EKS
- **Azure** - VM, Container Instances, AKS
- **GCP** - Compute Engine, Cloud Run, GKE
- **DigitalOcean** - Droplets, App Platform

See [Deployment Guide](30-deployment.md).

### Do I need a domain name?

No, but recommended for:

- SSL/TLS certificates
- Easier access
- Professional appearance

Can use:

- IP address (<http://192.168.1.100:8000>)
- Local hostname (<http://monitoring.local:8000>)
- Dynamic DNS service

### Can I run behind a reverse proxy?

Yes! Works with:

- Nginx
- Apache
- Traefik
- Caddy

See nginx example in [Deployment Guide](30-deployment.md).

## Future Features

### When will authentication be added?

Planned for v0.2.0 (Q2 2024). See [Roadmap](52-roadmap.md).

### Will there be a web UI?

Yes! React-based web UI planned for v0.4.0 (Q4 2024). Currently has PyQt6 desktop UI.

### Can you add support for [feature]?

Maybe! Check the [Roadmap](52-roadmap.md) or open a feature request. Popular requests get priority.

## Still Have Questions?

- **Documentation:** Check other docs in `docs/human/`
- **GitHub Issues:** Search existing issues
- **Discussions:** GitHub Discussions for Q&A
- **Email:** Contact maintainers (see README)

## Related Documentation

- [Quick Start](01-quick-start.md) - Get started quickly
- [Troubleshooting](31-troubleshooting.md) - Common issues
- [Configuration](03-configuration.md) - Configuration options
- [Roadmap](52-roadmap.md) - Future features
