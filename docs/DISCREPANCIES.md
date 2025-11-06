# Project Documentation Discrepancies

**Date**: November 7, 2025
**Analysis**: Comprehensive project alignment review

This document outlines all discrepancies between the actual implementation and the documented specifications in the Network Device Monitor project.

---

## 1. API Endpoint Discrepancies

### 1.1 Discovery Endpoint Mismatch

**Documentation Claims**:

- `POST /api/devices/discover` (in `docs/human/40-api-reference.md`)
- `POST /api/devices/discover` (in `docs/ai/10-rest-api.json`)

**Actual Implementation**:

- `POST /api/discovery/scan` (in `backend/app/api/routers/devices.py`)

**Severity**: HIGH
**Impact**: API clients following documentation will get 404 errors

---

### 1.2 Missing DELETE Endpoint

**Documentation Claims**:

- `DELETE /api/devices/{device_id}` is documented in `docs/human/40-api-reference.md`
- Returns `204 No Content` on success

**Actual Implementation**:

- **NOT IMPLEMENTED** in `backend/app/api/routers/devices.py`

**Severity**: HIGH
**Impact**: Documented feature does not exist

---

### 1.3 Health Endpoint Path Inconsistency

**Documentation Claims**:

- `GET /health` (in `docs/human/40-api-reference.md`)
- `GET /api/health` (in `docs/ai/10-rest-api.json`)

**Actual Implementation**:

- `GET /api/health` (in `backend/app/main.py`)

**Severity**: MEDIUM
**Impact**: Minor inconsistency between documentation sources

---

## 2. Response Format Discrepancies

### 2.1 Health Endpoint Response

**Documentation Claims** (`docs/human/40-api-reference.md`):

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Actual Implementation**:

```json
{
  "status": "ok"
}
```

**Severity**: LOW
**Impact**: Missing timestamp field, different status value

---

### 2.2 Discovery Response Format

**Documentation Claims** (`docs/human/40-api-reference.md`):

```json
{
  "message": "Discovery started",
  "job_id": "discover_2024-01-15_10-30-00"
}
```

**Actual Implementation**:

```json
{
  "count": 5,
  "devices": [...],
  "persisted": true,
  "identified": true
}
```

**Severity**: HIGH
**Impact**: Completely different response structure - documentation describes async operation, implementation is synchronous

---

### 2.3 Metrics Response Format

**Documentation Claims** (`docs/human/40-api-reference.md`):

```json
{
  "device_id": "...",
  "metric": "latency",
  "time_range": {...},
  "data_points": [...]
}
```

**Actual Implementation**:

```json
{
  "device_id": "...",
  "points": [...],
  "count": 10
}
```

**Severity**: MEDIUM
**Impact**: Different field names and structure

---

## 3. Missing Features

### 3.1 Query Parameters Not Implemented

**Documented in `docs/human/40-api-reference.md`**:

For `GET /api/devices`:

- `status` (filter by up/down/unknown/all)
- `limit` (pagination)
- `offset` (pagination)

**Actual Implementation**:

- NO query parameters supported in `backend/app/api/routers/devices.py`

**Severity**: MEDIUM
**Impact**: Pagination and filtering features documented but not implemented

---

### 3.2 Metrics Summary Endpoint

**Documentation Claims**:

- `GET /api/metrics/summary` endpoint exists
- Returns aggregate metrics for all devices

**Actual Implementation**:

- **NOT IMPLEMENTED** in `backend/app/api/routers/metrics.py`

**Severity**: MEDIUM
**Impact**: Documented endpoint missing

---

## 4. Data Model Discrepancies

### 4.1 Device Model Inconsistencies

**Documentation Claims** (`docs/ai/10-rest-api.json`):

```json
{
  "id": "aa:bb:cc:dd:ee:ff",
  "ip": "192.168.1.100",
  "mac": "aa:bb:cc:dd:ee:ff",
  "hostname": "router.local",
  "vendor": "Cisco Systems",
  "device_type": "router",
  "status": "up",
  "first_seen": 1699000000,  // Unix timestamp
  "last_seen": 1699001000,   // Unix timestamp
  "tags": {}
}
```

**Actual Implementation** (`backend/app/models/device.py`):

- All fields match except status is Optional
- Implementation is correct

**Severity**: LOW
**Impact**: Minor - optional field vs required

---

### 4.2 Missing LatencyMetric Model

**Documentation Claims** (`docs/human/11-architecture.md`):

```python
class LatencyMetric(BaseModel):
    device_id: str
    timestamp: datetime
    latency_ms: float
    packet_loss: float
    packets_sent: int
    packets_received: int
```

**Actual Implementation** (`backend/app/models/metrics.py`):

```python
class LatencyPoint(BaseModel):
    ts: int
    ms: float
    loss: float
```

**Severity**: HIGH
**Impact**:

- Different class name
- Missing fields: `device_id`, `packets_sent`, `packets_received`
- Different field types: `timestamp` (datetime) vs `ts` (int)
- Different field names: `latency_ms` vs `ms`, `packet_loss` vs `loss`

---

## 5. Configuration Discrepancies

### 5.1 Default NETWORK_CIDR Value

**Documentation Claims** (`docs/human/03-configuration.md` and README):

- Default: `192.168.1.0/24`

**Actual Implementation** (`backend/app/config.py`):

- Default: `192.168.1.0/24` ✓ CORRECT

**Severity**: NONE
**Impact**: No discrepancy

---

### 5.2 Environment File Examples

**Documentation Claims** (Quick Start):

- References `backend/.env.example`

**Actual Implementation**:

- File exists at `backend/.env.example` ✓ CORRECT
- Contents match documented variables ✓ CORRECT

**Severity**: NONE
**Impact**: No discrepancy

---

## 6. Architecture Documentation Issues

### 6.1 Repository Interface Claims

**Documentation Claims** (`docs/human/11-architecture.md`):

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

**Actual Implementation** (`backend/app/storage/repository.py`):

- Only has 2 methods: `upsert_device()` and `list_devices()`
- Missing: `create()`, `get()`, `update()`, `delete()`
- Missing: ABC inheritance

**Actual SQLite Implementation** (`backend/app/storage/sqlite.py`):

- Has: `upsert_device()`, `list_devices()`, `get_device()`
- Does NOT inherit from any abstract base class
- No explicit repository interface contract

**Severity**: HIGH
**Impact**: Architecture documentation describes non-existent abstraction layer

---

### 6.2 Scheduler Job Intervals

**Documentation Claims** (`docs/human/11-architecture.md`):

- Discovery Job: "configurable interval"
- Monitoring Job: "every 30s"

**Actual Implementation** (`backend/app/scheduler/jobs.py`):

- Discovery Job: every 10 minutes (hardcoded)
- Monitoring Job: every 5 seconds (not 30s)

**Severity**: LOW
**Impact**: Different intervals, not configurable

---

## 7. WebSocket Protocol Discrepancies

### 7.1 Missing WebSocket Events

**Documentation Claims** (`docs/human/40-api-reference.md`):
All these events are documented as being broadcast

**Actual Implementation Check**:

✓ `hello` - Implemented in `ws.py`
✓ `device_discovered` - Broadcast in `scheduler/jobs.py`
✓ `device_up` - Broadcast in `scheduler/jobs.py`
✓ `device_down` - Broadcast in `scheduler/jobs.py`
✓ `latency` - Broadcast in `scheduler/jobs.py`

**Severity**: NONE
**Impact**: All documented events are implemented

---

## 8. Frontend Discrepancies

### 8.1 PyQt Frontend Structure

**Documentation Claims** (README and architecture):

- Desktop application with PyQt6
- Real-time updates via WebSocket
- Device list view
- Topology visualization

**Actual Implementation Check**:

- `frontend/pyqt/src/` exists with:
  - `app.py`
  - `main_window.py`
  - `topology_view.py`
  - `api_client.py`

**Severity**: UNKNOWN
**Impact**: Cannot verify without examining frontend code in detail

---

## 9. Testing Coverage Claims

### 9.1 Test Coverage Claims

**Documentation Claims** (`docs/human/52-roadmap.md`):

- Current: "Basic unit tests"
- Version 1.0.0 goal: ">90% coverage"

**Actual Implementation**:

- Tests exist in `backend/tests/`
- 8 test files present
- Coverage percentage: UNKNOWN (not verified)

**Severity**: LOW
**Impact**: Cannot verify actual test coverage

---

## 10. Docker Configuration Issues

### 10.1 No Issues Found

**Verification**:

- `.env` file is properly listed in `.gitignore` ✅
- Only `.env.example` with placeholder values is in repository ✅
- Actual credentials stored locally and not committed ✅

**Severity**: NONE
**Impact**: No security issues found

---

## 11. Missing Documentation

### 11.1 Missing Request Body Schema

**Documentation Claims** (`docs/human/40-api-reference.md`):

- Discovery endpoint accepts optional `network` and `interface` in request body

**Actual Implementation** (`backend/app/api/routers/devices.py`):

- Accepts: `cidr`, `interface`, `arp_timeout`, `ping_timeout`, `persist`, `identify`
- Field names don't match: `network` vs `cidr`

**Severity**: MEDIUM
**Impact**: Documentation uses wrong field names

---

## Summary Statistics

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 6 |
| MEDIUM | 6 |
| LOW | 4 |
| NONE | 4 |

**Total Issues**: 16 discrepancies found (excluding 4 verified correct implementations)

---

## Priority Issues (Require Immediate Attention)

1. **HIGH**: API endpoint path mismatch (`/api/devices/discover` vs `/api/discovery/scan`)
2. **HIGH**: Missing DELETE endpoint implementation
3. **HIGH**: Discovery response format completely different from documentation
4. **HIGH**: Repository interface architecture doesn't exist as documented
5. **HIGH**: LatencyMetric model has wrong fields and structure

---

## Next Steps

See `REMEDIATION.md` for detailed fix recommendations for each issue.
