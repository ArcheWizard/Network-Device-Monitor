# CLI Commands Reference

Command-line interface reference for the Network Device Monitor.

## Overview

The application provides several ways to run commands:

- **Direct Python execution** - `python -m app.main`
- **Make commands** - `make run`, `make test`
- **Shell scripts** - `./scripts/run_backend.sh`
- **Docker commands** - `docker-compose exec backend ...`

## Development Commands

### Running the Application

```bash
# Run backend directly
cd backend
python -m app.main

# Using make
make run

# Using script
./scripts/run_backend.sh

# With Docker
docker-compose -f docker/docker-compose.yml up backend
```

### Running Tests

```bash
# All tests
cd backend
pytest

# Using make
make test

# Specific test file
pytest tests/test_discovery_api.py

# With coverage
pytest --cov=app --cov-report=html

# Using make with coverage
make test-cov

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Code Quality

```bash
# Type checking with mypy
cd backend
mypy app/

# Using make
make type-check

# Format code with black
black app/ tests/

# Using make
make format

# Lint with flake8
flake8 app/ tests/

# Using make
make lint

# All quality checks
make quality
```

## Database Commands

### SQLite Operations

```bash
# Open SQLite shell
sqlite3 backend/data/devices.db

# Query devices
sqlite3 backend/data/devices.db "SELECT * FROM devices;"

# Count devices
sqlite3 backend/data/devices.db "SELECT COUNT(*) FROM devices;"

# Export to CSV
sqlite3 backend/data/devices.db <<EOF
.headers on
.mode csv
.output devices.csv
SELECT * FROM devices;
EOF

# Backup database
sqlite3 backend/data/devices.db ".backup 'backup/devices.db'"

# Vacuum database
sqlite3 backend/data/devices.db "VACUUM;"
```

### InfluxDB Operations

```bash
# Query metrics (last hour)
influx query '
from(bucket: "network_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "latency")
' --org myorg --token your-token

# List buckets
influx bucket list --org myorg --token your-token

# Backup bucket
influx backup /path/to/backup \
  --host http://localhost:8086 \
  --token your-token \
  --bucket network_metrics

# Delete old data
influx delete \
  --bucket network_metrics \
  --start 2024-01-01T00:00:00Z \
  --stop 2024-02-01T00:00:00Z \
  --org myorg \
  --token your-token
```

## Network Operations

### Discovery

```bash
# Trigger discovery via API
curl -X POST http://localhost:8000/api/devices/discover

# With authentication (future)
curl -X POST http://localhost:8000/api/devices/discover \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Monitoring

```bash
# Get device metrics
curl "http://localhost:8000/api/metrics/latency?device_id=192.168.1.1&start=-1h"

# List all devices
curl http://localhost:8000/api/devices

# Get specific device
curl http://localhost:8000/api/devices/192.168.1.1
```

### Network Utilities

```bash
# Manual ARP scan
sudo arp-scan --interface=eth0 192.168.1.0/24

# Ping sweep
nmap -sn 192.168.1.0/24

# SNMP query
snmpwalk -v2c -c public 192.168.1.1 system

# mDNS discovery
avahi-browse -a -t

# DNS reverse lookup
nslookup 192.168.1.1
dig -x 192.168.1.1
```

## Docker Commands

### Container Management

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Start specific service
docker-compose -f docker/docker-compose.yml up -d backend

# Stop services
docker-compose -f docker/docker-compose.yml down

# View logs
docker-compose -f docker/docker-compose.yml logs -f backend

# Execute command in container
docker-compose -f docker/docker-compose.yml exec backend python -m app.main

# Shell access
docker-compose -f docker/docker-compose.yml exec backend bash
```

### Container Maintenance

```bash
# Rebuild containers
docker-compose -f docker/docker-compose.yml build

# Remove containers and volumes
docker-compose -f docker/docker-compose.yml down -v

# Clean up unused images
docker image prune -a

# View container stats
docker stats
```

## Environment Management

### Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Deactivate
deactivate

# Install dependencies
pip install -r backend/requirements/dev.txt

# Freeze dependencies
pip freeze > backend/requirements/dev.txt
```

### Environment Variables

```bash
# Show all environment variables
env | grep -E "INFLUX|SNMP|NETWORK"

# Set variable temporarily
export NETWORK_CIDR=192.168.1.0/24

# Set variable in .env file
echo "NETWORK_CIDR=192.168.1.0/24" >> .env

# Load .env file
export $(cat .env | xargs)
```

## Maintenance Commands

### Update OUI Database

```bash
# Download and update OUI database
cd backend
bash ../scripts/seed_oui.sh

# Verify update
ls -lh data/oui_cache.csv
wc -l data/oui_cache.csv
```

### Cleanup

```bash
# Remove Python cache files
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Using make
make clean

# Remove test artifacts
rm -rf .pytest_cache
rm -rf htmlcov
rm -f .coverage
```

### Logs

```bash
# View backend logs (if logging to file)
tail -f logs/backend.log

# Docker logs
docker-compose -f docker/docker-compose.yml logs -f backend

# Last 100 lines
docker-compose -f docker/docker-compose.yml logs --tail=100 backend

# Follow logs with timestamps
docker-compose -f docker/docker-compose.yml logs -f --timestamps backend
```

## Debugging Commands

### Python Debugging

```bash
# Run with pdb
python -m pdb -m app.main

# Run with better debugger (ipdb)
pip install ipdb
python -m ipdb -m app.main

# Enable debug logging
LOG_LEVEL=DEBUG python -m app.main
```

### Network Debugging

```bash
# Check network interface
ip addr show

# Check routing table
ip route

# Capture packets (requires root)
sudo tcpdump -i eth0 arp

# Check open ports
netstat -tuln | grep 8000
ss -tuln | grep 8000
```

### Process Management

```bash
# Find Python processes
ps aux | grep python

# Kill process by port
lsof -ti:8000 | xargs kill -9

# Monitor system resources
top
htop
```

## Performance Commands

### Profiling

```bash
# Profile application
python -m cProfile -o profile.stats app/main.py

# View profile results
python -m pstats profile.stats
> sort cumtime
> stats 20

# Memory profiling
pip install memory_profiler
python -m memory_profiler app/main.py
```

### Benchmarking

```bash
# API benchmark with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/api/devices

# With curl timing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/devices

# Load testing with locust
pip install locust
locust -f tests/locustfile.py
```

## Makefile Targets

```bash
# View all available targets
make help

# Common targets
make run          # Run backend
make test         # Run tests
make test-cov     # Run tests with coverage
make lint         # Run linter
make format       # Format code
make type-check   # Type checking
make quality      # All quality checks
make clean        # Clean cache files
make docker-build # Build Docker images
make docker-up    # Start Docker containers
make docker-down  # Stop Docker containers
```

## Best Practices

1. **Use make commands** - Consistent interface across platforms
2. **Virtual environment** - Always use venv for development
3. **Test before commit** - Run `make quality` before committing
4. **Check logs** - Monitor application logs for errors
5. **Backup before changes** - Backup databases before major changes
6. **Use Docker for production** - Consistent deployment environment

## Related Documentation

- [Development Guide](10-development.md) - Development workflow
- [Testing Guide](12-testing.md) - Testing procedures
- [Deployment](30-deployment.md) - Production deployment
- [Troubleshooting](31-troubleshooting.md) - Common issues
