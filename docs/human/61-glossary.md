# Glossary

Technical terms and concepts used in the Network Device Monitor.

## A

**ARP (Address Resolution Protocol)**

- Protocol for mapping IP addresses to MAC addresses on local networks
- Used for device discovery
- Requires elevated privileges (root or CAP_NET_RAW)

**APScheduler**

- Advanced Python Scheduler library
- Used for running periodic monitoring tasks
- Supports cron-like scheduling

**Availability**

- Percentage of time a device is reachable
- Calculated from monitoring history
- Example: 99.9% uptime

## B

**Backend**

- Server-side application component
- FastAPI-based REST API
- Handles discovery, monitoring, and data storage

**Bonjour**

- Apple's implementation of mDNS/DNS-SD
- Used for zero-configuration networking
- See also: mDNS, Zeroconf

**Bucket (InfluxDB)**

- Container for time-series data in InfluxDB
- Similar to database in traditional DBMS
- Default: `network_metrics`

## C

**CDP (Cisco Discovery Protocol)**

- Proprietary protocol by Cisco
- Discovers network topology
- Future feature (not yet implemented)

**CIDR (Classless Inter-Domain Routing)**

- IP address notation format
- Example: `192.168.1.0/24` represents 256 addresses
- Used to specify network range for discovery

**Community String (SNMP)**

- Password for SNMPv1/v2c
- Common default: "public"
- Should be changed for security

## D

**Device**

- Network-connected hardware
- Identified by IP and MAC address
- Stored in SQLite inventory

**Device Identification**

- Process of determining device details
- Methods: OUI lookup, SNMP queries, DNS
- Gathers vendor, hostname, model info

**Discovery**

- Process of finding devices on network
- Methods: ARP scan, ICMP ping, mDNS
- Runs on-demand or scheduled

**DNS-SD (DNS Service Discovery)**

- Protocol for discovering services
- Works with mDNS
- Used for finding network services

## F

**FastAPI**

- Modern Python web framework
- Used for REST API and WebSocket
- Auto-generates OpenAPI documentation

**Field (InfluxDB)**

- Value columns in InfluxDB measurement
- Examples: latency_ms, packet_loss
- Typically numeric values

**Flux**

- InfluxDB query language
- Used to query time-series data
- Replaces InfluxQL in InfluxDB 2.x

## H

**Health Check**

- Periodic verification that device is reachable
- Uses ICMP ping
- Updates device status (up/down)

**Hostname**

- Human-readable name for device
- Example: "router.local" or "laptop-john"
- Obtained via DNS reverse lookup

## I

**ICMP (Internet Control Message Protocol)**

- Network protocol for diagnostics
- Used by ping command
- No special privileges required

**InfluxDB**

- Time-series database
- Stores monitoring metrics
- Version 2.x required

**Interface**

- Network adapter on monitoring system
- Examples: eth0, wlan0, enp0s3
- Must have connectivity to monitored network

## L

**Latency**

- Time for packet to travel to device and back
- Measured in milliseconds (ms)
- Lower is better

**LLDP (Link Layer Discovery Protocol)**

- Vendor-neutral discovery protocol
- Discovers network topology
- Future feature (not yet implemented)

## M

**MAC Address (Media Access Control)**

- Hardware address of network interface
- Format: `aa:bb:cc:dd:ee:ff`
- Used as device identifier

**mDNS (Multicast DNS)**

- Protocol for name resolution without DNS server
- Uses .local domain
- Used for device discovery

**Measurement (InfluxDB)**

- Table equivalent in InfluxDB
- Example: "latency" measurement
- Contains fields and tags

**Metrics**

- Quantitative measurements
- Examples: latency, packet loss, uptime
- Stored in InfluxDB

**Monitoring**

- Continuous health checking of devices
- Collects performance metrics
- Default interval: 60 seconds

## N

**Network Device**

- Hardware with network connectivity
- Examples: router, switch, computer, IoT device
- Target of monitoring

## O

**OUI (Organizationally Unique Identifier)**

- First 24 bits of MAC address
- Identifies manufacturer
- Example: Apple Inc = 00:03:93

**OUI Database**

- List of OUI to vendor mappings
- Maintained by IEEE
- Updated periodically via script

## P

**Packet Loss**

- Percentage of packets not returned
- Indicates network reliability
- 0% is ideal

**Ping**

- Network utility using ICMP
- Tests reachability and latency
- Primary monitoring method

**Pydantic**

- Python data validation library
- Used for API models and settings
- Provides type checking and validation

**PyQt6**

- Python bindings for Qt GUI framework
- Used for desktop frontend
- Cross-platform UI toolkit

## R

**Repository**

- Data access layer abstraction
- Handles database operations
- Example: SqliteInventoryRepository

**REST API**

- HTTP-based API for communication
- Endpoints for devices, metrics, discovery
- Uses JSON format

**Retention Policy**

- How long data is kept in database
- Configurable in InfluxDB
- Example: 30 days, 90 days, infinite

## S

**Scapy**

- Python library for packet manipulation
- Used for ARP scanning
- Requires elevated privileges

**Scheduler**

- Component that runs periodic tasks
- Uses APScheduler
- Runs discovery and monitoring jobs

**SNMP (Simple Network Management Protocol)**

- Protocol for managing network devices
- Used for device identification
- Currently supports v2c, v3 planned

**SQLite**

- Embedded relational database
- Stores device inventory
- File: `backend/data/devices.db`

**Status**

- Current reachability state of device
- Values: up, down, unknown
- Updated by monitoring

**sysDescr (SNMP)**

- System description from SNMP
- Contains device model/software info
- Example: "Cisco IOS Software, Version 15.2"

**sysName (SNMP)**

- System name from SNMP
- Usually hostname
- Example: "core-switch-01"

## T

**Tag (InfluxDB)**

- Indexed metadata in InfluxDB
- Used for filtering queries
- Examples: device_id, ip

**Time-series Data**

- Data points with timestamps
- Used for tracking metrics over time
- Stored in InfluxDB

## V

**Vendor**

- Device manufacturer
- Determined from MAC OUI
- Examples: "Apple Inc", "Cisco Systems"

## W

**WebSocket**

- Protocol for real-time bidirectional communication
- Used for live updates
- Endpoint: `/ws/stream`

## Z

**Zeroconf**

- Zero-configuration networking
- Includes mDNS and DNS-SD
- Python library: `zeroconf`

## Network Concepts

### IPv4 Address

- 32-bit network address
- Format: `192.168.1.1`
- Four octets separated by dots

### Subnet Mask

- Defines network and host portions of IP
- Example: `255.255.255.0` (/24)
- Used with CIDR notation

### VLAN (Virtual LAN)

- Logical network segmentation
- May require separate monitoring instance
- Currently not directly supported

## Monitoring Concepts

### Uptime

- Time device has been continuously up
- Measured from last down event
- Expressed in days/hours/minutes

### Downtime

- Time device was unreachable
- Impacts availability percentage
- Tracked in monitoring history

### Threshold

- Value that triggers alert
- Examples: latency > 200ms, loss > 50%
- Configurable in settings

## Database Concepts

### Write (InfluxDB)**

- Inserting data points into database
- Batched for performance
- Async operation

### Query (InfluxDB)**

- Retrieving data from database
- Uses Flux query language
- Filtered by time range and tags

### Retention

- How long data is stored
- Automatic deletion after period
- Saves disk space

## Common Abbreviations

- **API** - Application Programming Interface
- **CPU** - Central Processing Unit
- **DNS** - Domain Name System
- **GUI** - Graphical User Interface
- **HTTP** - Hypertext Transfer Protocol
- **HTTPS** - HTTP Secure
- **IP** - Internet Protocol
- **JSON** - JavaScript Object Notation
- **REST** - Representational State Transfer
- **TLS** - Transport Layer Security
- **UI** - User Interface
- **URL** - Uniform Resource Locator
- **UTC** - Coordinated Universal Time
- **VLAN** - Virtual Local Area Network

## Related Documentation

- [Architecture](11-architecture.md) - System architecture details
- [API Reference](40-api-reference.md) - API endpoints
- [FAQ](60-faq.md) - Frequently asked questions
