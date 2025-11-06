# Architecture Overview

System design and architectural decisions for Network Device Monitor.

## System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend Layer                        │
│  ┌──────────────────┐          ┌───────────────────────┐    │
│  │   PyQt6 Desktop  │          │   Web UI (Future)     │    │
│  │   Application    │          │                       │    │
│  └────────┬─────────┘          └───────────┬───────────┘    │
└───────────┼────────────────────────────────┼────────────────┘
            │ HTTP/WebSocket                 │
            ▼                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │   REST API   │  │  WebSocket   │  │  Health/Metrics │   │
│  │  /api/...    │  │  /ws/stream  │  │   /health       │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘   │
└─────────┼──────────────────┼────────────────────┼───────────┘
          │                  │                    │
          ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Discovery   │  │Identification│  │   Monitoring    │   │
│  │   Service    │  │   Service    │  │    Service      │   │
│  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘   │
│         │                  │                    │            │
│  ┌──────┴──────────────────┴────────────────────┴────────┐  │
│  │              Repository Interface                      │  │
│  └────────────────────────┬───────────────────────────────┘  │
└───────────────────────────┼──────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          ▼                                   ▼
┌─────────────────────┐           ┌──────────────────────┐
│  SQLite Database    │           │  InfluxDB (Optional) │
│  - Device Inventory │           │  - Time-series       │
│  - Current State    │           │  - Historical Metrics│
└─────────────────────┘           └──────────────────────┘

          │                                   │
          ▼                                   ▼
┌─────────────────────┐           ┌──────────────────────┐
│  Background Jobs    │           │   External Services  │
│  - APScheduler      │           │  - SNMP Agents       │
│  - Discovery Tasks  │           │  - mDNS Responders   │
│  - Monitoring Loop  │           │  - Network Devices   │
└─────────────────────┘           └──────────────────────┘
```

## Core Components

### 1. API Layer (`app/api/`)

**Responsibility**: HTTP interface for all client interactions

**Technology**: FastAPI with async/await

**Components**:

- **REST Routers** (`api/routers/`):
  - `devices.py`: Device management endpoints
  - `metrics.py`: Historical metrics queries
  - `ws.py`: WebSocket real-time streaming

**Key Patterns**:

- Async request handlers for concurrent operation
- Pydantic model validation on input/output
- Dependency injection for services
- Exception handlers for consistent error responses

### 2. Service Layer (`app/services/`)

**Responsibility**: Business logic and orchestration

**Components**:

#### Discovery Service (`discovery.py`)

- **Function**: Network scanning and device discovery
- **Methods**:
  - ARP scanning (Scapy)
  - ICMP ping (subprocess)
  - mDNS/DNS-SD (Zeroconf)
- **Output**: List of live IP/MAC addresses

#### Identification Service (`identification.py`)

- **Function**: Device type and vendor identification
- **Methods**:
  - SNMP sysDescr/sysObjectID queries
  - MAC OUI lookup
  - Hostname resolution
- **Output**: Enriched device metadata

#### Monitoring Service (`monitoring.py`)

- **Function**: Continuous device health monitoring
- **Methods**:
  - ICMP latency measurement
  - Packet loss calculation
  - Status change detection
- **Output**: Real-time metrics and alerts

#### SNMP Service (`snmp.py`)

- **Function**: Low-level SNMP protocol operations
- **Technology**: PySNMP
- **Operations**: GET, GETNEXT, WALK

#### Notification Service (`notifications.py`)

- **Function**: Alert distribution (future enhancement)
- **Channels**: WebSocket (implemented), Email/Slack (planned)

### 3. Storage Layer (`app/storage/`)

**Responsibility**: Data persistence abstraction

**Components**:

#### Repository Interface (`repository.py`)

Abstract base class defining storage contract:

```python
class DeviceRepository(ABC):
    @abstractmethod
    async def create(self, device: Device) -> Device: ...
    
    @abstractmethod
    async def get(self, device_id: str) -> Device | None: ...
    
    @abstractmethod
    async def list_all(self) -> list[Device]: ...
    
    @abstractmethod
    async def update(self, device_id: str, updates: dict) -> Device: ...
    
    @abstractmethod
    async def delete(self, device_id: str) -> bool: ...
```

#### SQLite Implementation (`sqlite.py`)

- **Purpose**: Primary device inventory storage
- **Features**:
  - WAL mode for concurrent access
  - Automatic schema migration
  - Indexed queries
- **Storage**: `backend/data/devices.db`

#### InfluxDB Implementation (`influx.py`)

- **Purpose**: Time-series metrics storage
- **Features**:
  - High-frequency data ingestion
  - Retention policies
  - Downsampling
- **Optional**: Falls back to SQLite if unavailable

### 4. Scheduler (`app/scheduler/`)

**Responsibility**: Background task execution

**Technology**: APScheduler

**Jobs**:

- **Discovery Job**: Periodic network scans (configurable interval)
- **Monitoring Job**: Continuous device health checks
- **Cleanup Job**: Database maintenance (future)

### 5. Models (`app/models/`)

**Responsibility**: Data structure definitions

**Technology**: Pydantic v2

**Models**:

#### Device Model (`device.py`)

```python
class Device(BaseModel):
    id: str  # UUID
    ip: str  # IP address
    mac: str  # MAC address
    hostname: str | None
    vendor: str | None
    device_type: str | None
    status: Literal["up", "down", "unknown"]
    first_seen: datetime
    last_seen: datetime
```

#### Metrics Model (`metrics.py`)

```python
class LatencyMetric(BaseModel):
    device_id: str
    timestamp: datetime
    latency_ms: float
    packet_loss: float  # 0.0 to 1.0
    packets_sent: int
    packets_received: int
```

### 6. Utilities (`app/utils/`)

**Responsibility**: Helper functions and common utilities

**Modules**:

- `network.py`: IP validation, CIDR parsing, interface detection
- `oui.py`: MAC vendor lookup from IEEE OUI database

## Data Flow

### Discovery Flow

```
1. User triggers discovery (POST /api/devices/discover)
   │
2. API calls DiscoveryService.discover_network()
   │
3. Discovery Service:
   ├─ ARP scan (Scapy) → Live IPs + MACs
   ├─ ICMP ping → Latency data
   └─ mDNS discovery (Zeroconf) → Hostnames
   │
4. For each discovered device:
   │
5. Identification Service:
   ├─ SNMP query → sysDescr, sysObjectID
   ├─ OUI lookup → Vendor name
   └─ DNS lookup → Hostname
   │
6. Repository.create() → Save to SQLite
   │
7. WebSocket broadcast → Notify connected clients
   │
8. Return device list to API caller
```

### Monitoring Flow

```
1. Scheduler triggers monitoring job (every 30s)
   │
2. Repository.list_all() → Get all devices
   │
3. For each device:
   │
4. MonitoringService.check_device():
   ├─ ICMP ping → Latency + packet loss
   ├─ Detect status changes (up ↔ down)
   └─ Generate metrics
   │
5. Storage:
   ├─ InfluxDB.write() → Time-series metrics
   └─ Repository.update() → Status changes
   │
6. If status changed:
   │
7. WebSocket broadcast → device_up / device_down event
```

### WebSocket Real-time Updates

```
1. Client connects to ws://localhost:8000/ws/stream
   │
2. Server sends "hello" message
   │
3. Events broadcast to all connected clients:
   ├─ device_discovered (during discovery)
   ├─ device_up (status change)
   ├─ device_down (status change)
   └─ latency (every monitoring tick)
```

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | FastAPI | Async HTTP/WebSocket server |
| ASGI Server | Uvicorn | Production-grade ASGI runtime |
| Validation | Pydantic v2 | Data modeling & validation |
| Discovery | Scapy | ARP scanning, packet crafting |
| mDNS | Zeroconf | Service discovery |
| SNMP | PySNMP | Device identification |
| Scheduler | APScheduler | Background jobs |
| Database | SQLite | Device inventory |
| Time-series | InfluxDB | Historical metrics (optional) |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Desktop UI | PyQt6 | Native desktop application |
| HTTP Client | aiohttp | Async API communication |
| WebSocket | websockets | Real-time event streaming |
| Visualization | PyQtGraph | Network topology rendering |

## Design Patterns

### 1. Repository Pattern

**Purpose**: Abstract data storage implementation

**Benefits**:
- Swap storage backends (SQLite ↔ InfluxDB)
- Testable with mock repositories
- Clear separation of concerns

### 2. Service Layer Pattern

**Purpose**: Encapsulate business logic

**Benefits**:
- Reusable across API and background jobs
- Testable in isolation
- Single responsibility per service

### 3. Dependency Injection

**Purpose**: Provide dependencies at runtime

**Example**:

```python
def get_device_repo() -> DeviceRepository:
    return SQLiteRepository()

@router.get("/devices")
async def list_devices(
    repo: DeviceRepository = Depends(get_device_repo)
):
    return await repo.list_all()
```

### 4. Async/Await

**Purpose**: Non-blocking I/O for concurrency

**Usage**:
- All API handlers are async
- Database operations are async
- Network operations use async libraries

### 5. Event-driven Architecture

**Purpose**: Real-time notifications

**Implementation**:
- Services emit events (device discovered, status changed)
- WebSocket manager broadcasts to clients
- Decoupled components

## Security Architecture

### Network Security

- **Principle**: Least privilege
- **Implementation**:
  - Read-only SNMP community strings
  - Bind to specific interfaces only
  - No outbound connections except monitored network

### API Security

- **Current**: No authentication (local network assumption)
- **Planned**:
  - JWT token authentication
  - Role-based access control
  - API key management

### Data Security

- **At Rest**: SQLite database file permissions (600)
- **In Transit**: No TLS (local network assumption)
- **Secrets**: Environment variables, never committed

## Performance Considerations

### Discovery Performance

- **Challenge**: Large networks (e.g., /16 CIDR = 65,536 IPs)
- **Optimizations**:
  - Async scanning (1000+ concurrent pings)
  - SNMP timeout tuning
  - Chunked discovery (future)

### Monitoring Performance

- **Challenge**: Continuous monitoring of 100+ devices
- **Optimizations**:
  - Configurable interval (trade-off: latency vs load)
  - Batch ICMP pings
  - Skip offline devices

### Database Performance

- **SQLite**:
  - WAL mode for concurrent reads
  - Indexed queries (device_id, ip, mac)
  - Periodic vacuum
- **InfluxDB**:
  - Batch writes
  - Retention policies
  - Downsampling for long-term storage

## Scalability

### Current Limitations

- **Single-process**: No horizontal scaling
- **In-memory scheduler**: No distributed jobs
- **SQLite**: Single-writer bottleneck

### Future Enhancements

- **Distributed discovery**: Multiple scanners
- **Message queue**: RabbitMQ/Redis for async tasks
- **PostgreSQL**: Replace SQLite for multi-writer support
- **Load balancer**: Multiple API instances

## Deployment Architecture

### Development

```
Single Machine
├── Backend (localhost:8000)
├── Frontend (PyQt desktop app)
└── Optional: InfluxDB (localhost:8086)
```

### Production (Docker)

```
Docker Network
├── Backend Container (Python)
├── InfluxDB Container
└── Frontend runs on user's machine
```

### Production (Bare Metal)

```
Linux Server
├── Backend (systemd service)
├── InfluxDB (separate service)
└── Nginx (reverse proxy)
```

## Error Handling

### API Layer

- **400**: Invalid input (Pydantic validation)
- **404**: Resource not found
- **500**: Internal server error
- **503**: Service unavailable (e.g., database down)

### Service Layer

- **Exceptions**: Custom exception classes
- **Logging**: Structured logging with context
- **Retries**: Exponential backoff for network operations

### Storage Layer

- **Database errors**: Logged and raised as HTTP 500
- **Connection failures**: Automatic retry with backoff
- **Data corruption**: Validation before storage

## Testing Architecture

### Unit Tests

- **Scope**: Individual functions/classes
- **Mocking**: External dependencies (network, database)
- **Coverage**: >80% for business logic

### Integration Tests

- **Scope**: Component interactions
- **Real dependencies**: SQLite (in-memory), test network
- **Fixtures**: Pytest fixtures for setup/teardown

### End-to-End Tests

- **Scope**: Full API workflows
- **Test client**: FastAPI TestClient
- **Assertions**: HTTP responses, database state

## Configuration Management

### Layered Configuration

1. **Defaults**: Hard-coded in `config.py`
2. **Environment variables**: Override defaults
3. **`.env` file**: Override environment
4. **Command-line**: Highest priority (future)

### Validation

- **Pydantic Settings**: Type-safe configuration
- **Startup checks**: Validate on application boot
- **Fail-fast**: Invalid config prevents startup

## Monitoring & Observability

### Logging

- **Library**: Python `logging` module
- **Format**: JSON (production), text (development)
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Metrics (Future)

- **Library**: Prometheus client
- **Metrics**: Request count, latency, device count
- **Endpoint**: `/metrics`

### Tracing (Future)

- **Library**: OpenTelemetry
- **Spans**: API requests, service calls, database queries

## Next Steps

- [Development Guide](10-development.md) - Set up development environment
- [Testing Guide](12-testing.md) - Testing strategies
- [API Reference](40-api-reference.md) - REST API documentation
- [Security](42-security.md) - Security best practices
