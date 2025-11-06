# Remediation Plan

**Date**: November 7, 2025
**Purpose**: Step-by-step fixes for documented discrepancies

This document provides actionable remediation steps for each discrepancy identified in `DISCREPANCIES.md`.

---

## Priority 1: Security Review ✅

### Issue 1.1: Security Configuration Verified

**Status**: ✅ NO SECURITY ISSUES FOUND

**Verification Completed**:

1. **`.gitignore` properly configured**:
   ```bash
   # Confirmed .env is ignored
   cat .gitignore | grep .env
   # Output: .env
   ```

2. **Only `.env.example` in repository**:
   - Contains placeholder values only
   - Actual `.env` with real credentials is local-only
   - ✅ No sensitive data committed

3. **Best practices followed**:
   - ✅ Environment files properly ignored
   - ✅ Example file provides template
   - ✅ Actual credentials stored securely

**No action required** - Security is properly configured!

---

## Priority 2: HIGH - API Endpoint Fixes

### Issue 2.1: Discovery Endpoint Path Mismatch

**Problem**: Documentation says `/api/devices/discover`, code implements `/api/discovery/scan`

**Decision Required**: Choose one of two options

#### Option A: Update Code to Match Documentation (RECOMMENDED)

**Why**: Keep documented API stable, less breaking change for potential users

**Steps**:

1. **Move endpoint in `backend/app/api/routers/devices.py`**:

   ```python
   @router.post("/devices/discover")  # Changed from /discovery/scan
   async def discovery_scan(request: Request, req: DiscoveryScanRequest | None = None):
       # ... existing implementation
   ```

2. **Update test files** to use new path:
   - `backend/tests/test_discovery_api.py`
   - Any integration tests

3. **Verification**:

   ```bash
   curl -X POST http://localhost:8000/api/devices/discover
   ```

#### Option B: Update Documentation to Match Code

**Why**: If `/api/discovery/scan` is preferred for better API organization

**Steps**:

1. **Update `docs/human/40-api-reference.md`**:
   - Change all references from `/api/devices/discover` to `/api/discovery/scan`

2. **Update `docs/ai/10-rest-api.json`**:
   - Change path from `/api/devices/discover` to `/api/discovery/scan`

3. **Update Quick Start and examples**:
   - `docs/human/01-quick-start.md`
   - `docs/ai/12-api-examples.json`

**Recommendation**: Choose Option A (update code) for consistency with RESTful design where discovery is an action on devices.

---

### Issue 2.2: Missing DELETE Endpoint

**Problem**: Documented but not implemented

**Fix Steps**:

1. **Add DELETE endpoint to `backend/app/api/routers/devices.py`**:

   ```python
   @router.delete("/devices/{device_id}", status_code=204)
   async def delete_device(device_id: str, request: Request):
       """Delete a device from inventory.

       Args:
           device_id: Device identifier (MAC or IP)
           request: FastAPI request

       Returns:
           204 No Content on success

       Raises:
           404: Device not found
       """
       repo = getattr(request.app.state, "inventory_repo", None)
       if not repo:
           from fastapi import HTTPException
           raise HTTPException(status_code=503, detail="Database unavailable")

       # Check if device exists
       existing = await repo.get_device(device_id)
       if not existing:
           from fastapi import HTTPException
           raise HTTPException(status_code=404, detail="Device not found")

       # Delete device (requires new repo method)
       await repo.delete_device(device_id)

       # Return 204 No Content
       from fastapi.responses import Response
       return Response(status_code=204)
   ```

2. **Add delete method to `backend/app/storage/sqlite.py`**:

   ```python
   async def delete_device(self, device_id: str) -> bool:
       """Delete a device from the database.

       Args:
           device_id: Device identifier

       Returns:
           True if device was deleted, False if not found
       """
       async with self._conn.execute(
           "DELETE FROM devices WHERE id=?",
           (device_id,)
       ) as cur:
           await self._conn.commit()
           return cur.rowcount > 0
   ```

3. **Add tests for DELETE endpoint**:

   Create `backend/tests/test_device_delete.py`:

   ```python
   import pytest
   from httpx import AsyncClient

   @pytest.mark.asyncio
   async def test_delete_device_success(client: AsyncClient):
       # First create a device
       # Then delete it
       response = await client.delete("/api/devices/test-device-id")
       assert response.status_code == 204

   @pytest.mark.asyncio
   async def test_delete_device_not_found(client: AsyncClient):
       response = await client.delete("/api/devices/nonexistent")
       assert response.status_code == 404
   ```

**Verification**:

```bash
# Start server
make dev

# Test delete
curl -X DELETE http://localhost:8000/api/devices/{device_id}
# Should return 204 with empty body
```

---

### Issue 2.3: Health Endpoint Response Format

**Problem**: Missing timestamp field

**Fix Steps**:

1. **Update `backend/app/main.py`**:

   ```python
   from datetime import datetime, timezone

   @app.get("/api/health")
   async def health():
       return {
           "status": "healthy",  # Changed from "ok"
           "timestamp": datetime.now(timezone.utc).isoformat()
       }
   ```

2. **Update response model** (optional, for type safety):

   Create `backend/app/models/health.py`:

   ```python
   from pydantic import BaseModel
   from datetime import datetime

   class HealthResponse(BaseModel):
       status: str
       timestamp: datetime
   ```

   Then in `main.py`:

   ```python
   from .models.health import HealthResponse

   @app.get("/api/health", response_model=HealthResponse)
   async def health():
       return {
           "status": "healthy",
           "timestamp": datetime.now(timezone.utc)
       }
   ```

**Verification**:

```bash
curl http://localhost:8000/api/health | jq
# Should show:
# {
#   "status": "healthy",
#   "timestamp": "2025-11-07T..."
# }
```

---

### Issue 2.4: Discovery Response Format Mismatch

**Problem**: Documentation describes async operation, implementation is synchronous

**Decision Required**: This is a design decision

#### Option A: Keep Synchronous (Current Implementation)

Update documentation to match synchronous behavior

**Fix Documentation**:

1. **Update `docs/human/40-api-reference.md`**:

   Change response example to:

   ```json
   {
     "count": 5,
     "devices": [
       {
         "ip": "192.168.1.10",
         "mac": "aa:bb:cc:dd:ee:ff",
         "hostname": "router.local",
         "vendor": "Cisco Systems",
         "source": "arp"
       }
     ],
     "persisted": true,
     "identified": true
   }
   ```

   Update description: "Initiates and completes network scan synchronously. Returns discovered devices immediately."

2. **Update `docs/ai/10-rest-api.json`**:

   ```json
   "responses": {
     "200": {
       "description": "Scan completed",
       "content": {
         "application/json": {
           "schema": {
             "$ref": "#/components/schemas/DiscoveryScanResponse"
           }
         }
       }
     }
   }
   ```

#### Option B: Implement Async Discovery (BETTER for large networks)

Make discovery truly asynchronous for better UX

**Implementation**:

1. **Create job tracking** in `backend/app/scheduler/jobs.py`
2. **Return job ID immediately**
3. **Add endpoint to check job status**: `GET /api/discovery/jobs/{job_id}`
4. **Broadcast results via WebSocket when complete**

This is more complex but better for production. See detailed steps in separate task.

**Recommendation**: For MVP, use Option A (update docs). Plan Option B for v0.2.0.

---

## Priority 3: MEDIUM - Query Parameters and Features

### Issue 3.1: Missing Query Parameters for GET /api/devices

**Fix Steps**:

1. **Update `backend/app/api/routers/devices.py`**:

   ```python
   from typing import Optional, Literal

   @router.get("/devices", response_model=list[Device])
   async def list_devices(
       request: Request,
       status: Optional[Literal["up", "down", "unknown", "all"]] = "all",
       limit: int = 100,
       offset: int = 0
   ):
       """List all devices with optional filtering and pagination.

       Args:
           status: Filter by device status (up/down/unknown/all)
           limit: Maximum number of results (default 100)
           offset: Pagination offset (default 0)
       """
       repo = getattr(request.app.state, "inventory_repo", None)
       if repo:
           # Get all devices first
           all_devices = await repo.list_devices()

           # Filter by status
           if status != "all":
               all_devices = [d for d in all_devices if d.get("status") == status]

           # Apply pagination
           paginated = all_devices[offset:offset + limit]

           # Convert to Device models
           return [Device(**d) for d in paginated]

       return list(_DEVICES.values())
   ```

2. **Add tests**:

   ```python
   @pytest.mark.asyncio
   async def test_list_devices_with_status_filter(client: AsyncClient):
       response = await client.get("/api/devices?status=up")
       assert response.status_code == 200
       devices = response.json()
       assert all(d["status"] == "up" for d in devices)

   @pytest.mark.asyncio
   async def test_list_devices_with_pagination(client: AsyncClient):
       response = await client.get("/api/devices?limit=5&offset=0")
       assert response.status_code == 200
       assert len(response.json()) <= 5
   ```

**Verification**:

```bash
curl "http://localhost:8000/api/devices?status=up&limit=10"
curl "http://localhost:8000/api/devices?offset=10&limit=10"
```

---

### Issue 3.2: Missing Metrics Summary Endpoint

**Fix Steps**:

1. **Add endpoint to `backend/app/api/routers/metrics.py`**:

   ```python
   @router.get("/metrics/summary")
   async def get_metrics_summary(request: Request = None):
       """Get aggregate metrics for all devices.

       Returns:
           Dictionary with summary statistics
       """
       repo = getattr(request.app.state, "inventory_repo", None) if request else None

       if not repo:
           return {
               "total_devices": 0,
               "devices_up": 0,
               "devices_down": 0,
               "devices_unknown": 0,
               "avg_latency_ms": None,
               "max_latency_ms": None,
               "total_packet_loss": None
           }

       # Get all devices
       devices = await repo.list_devices()

       # Calculate statistics
       total = len(devices)
       up = sum(1 for d in devices if d.get("status") == "up")
       down = sum(1 for d in devices if d.get("status") == "down")
       unknown = total - up - down

       # Get recent metrics from InfluxDB if available
       influx_writer = getattr(request.app.state, "influx_writer", None) if request else None
       avg_latency = None
       max_latency = None
       total_loss = None

       if influx_writer:
           # Query aggregate metrics from InfluxDB
           # This would require additional InfluxDB query methods
           pass

       return {
           "total_devices": total,
           "devices_up": up,
           "devices_down": down,
           "devices_unknown": unknown,
           "avg_latency_ms": avg_latency,
           "max_latency_ms": max_latency,
           "total_packet_loss": total_loss
       }
   ```

2. **Add Pydantic model** for response:

   ```python
   from pydantic import BaseModel
   from typing import Optional

   class MetricsSummary(BaseModel):
       total_devices: int
       devices_up: int
       devices_down: int
       devices_unknown: int
       avg_latency_ms: Optional[float]
       max_latency_ms: Optional[float]
       total_packet_loss: Optional[float]
   ```

**Verification**:

```bash
curl http://localhost:8000/api/metrics/summary | jq
```

---

## Priority 4: MEDIUM - Data Model Fixes

### Issue 4.1: LatencyMetric Model Discrepancies

**Problem**: Model doesn't match architecture documentation

**Fix Steps**:

1. **Update `backend/app/models/metrics.py`**:

   ```python
   from pydantic import BaseModel
   from datetime import datetime
   from typing import Optional

   class LatencyMetric(BaseModel):
       """Complete latency metric with all fields."""
       device_id: str
       timestamp: datetime
       latency_ms: float
       packet_loss: float  # 0.0 to 1.0
       packets_sent: int
       packets_received: int

   class LatencyPoint(BaseModel):
       """Simplified latency point for API responses."""
       ts: int  # Unix timestamp
       ms: float  # Latency in milliseconds
       loss: float  # Packet loss ratio
   ```

2. **Update monitoring service** to use full model:

   ```python
   # In backend/app/services/monitoring.py

   async def ping_device(ip: str, count: int = 4, timeout: float = 2.0) -> LatencyMetric:
       # ... existing ping logic ...

       return LatencyMetric(
           device_id=ip,  # Or MAC if available
           timestamp=datetime.now(timezone.utc),
           latency_ms=latency_avg,
           packet_loss=packet_loss / 100.0,  # Convert percentage to ratio
           packets_sent=count,
           packets_received=int(count * (1 - packet_loss / 100.0))
       )
   ```

3. **Update InfluxDB writer** to accept LatencyMetric:

   ```python
   # In backend/app/storage/influx.py

   async def write_latency_metric(self, metric: LatencyMetric) -> bool:
       return await self.write_metric(
           measurement="latency",
           tags={"device_id": metric.device_id},
           fields={
               "latency_ms": metric.latency_ms,
               "packet_loss": metric.packet_loss,
               "packets_sent": metric.packets_sent,
               "packets_received": metric.packets_received
           },
           timestamp=metric.timestamp
       )
   ```

**Verification**:

```bash
# Check model imports
python -c "from backend.app.models.metrics import LatencyMetric; print(LatencyMetric.__fields__)"
```

---

## Priority 5: LOW - Documentation Updates

### Issue 5.1: Request Body Field Name Mismatch

**Problem**: Documentation uses `network`, code uses `cidr`

**Fix Documentation**:

1. **Update `docs/human/40-api-reference.md`**:

   Change:

   ```json
   {
     "network": "192.168.1.0/24",  // ❌ Wrong
     "interface": "eth0"
   }
   ```

   To:

   ```json
   {
     "cidr": "192.168.1.0/24",  // ✅ Correct
     "interface": "eth0",
     "arp_timeout": 3.0,
     "ping_timeout": 1.0,
     "persist": true,
     "identify": true
   }
   ```

2. **Update all example cURL commands**:

   ```bash
   curl -X POST http://localhost:8000/api/discovery/scan \
     -H "Content-Type: application/json" \
     -d '{"cidr": "10.0.0.0/24", "persist": true, "identify": true}'
   ```

---

### Issue 5.2: Scheduler Interval Documentation

**Fix Documentation**:

1. **Update `docs/human/11-architecture.md`**:

   Change:

   ```
   - Discovery Job: Periodic network scans (configurable interval)
   - Monitoring Job: Continuous device health checks
   ```

   To:

   ```
   - Discovery Job: Periodic network scans (every 10 minutes, hardcoded)
   - Monitoring Job: Continuous device health checks (every 5 seconds)
   ```

2. **Future Enhancement**: Make intervals configurable via environment variables:

   ```python
   # In backend/app/config.py
   DISCOVERY_INTERVAL_MINUTES: int = 10
   MONITORING_INTERVAL_SECONDS: int = 5

   # In backend/app/scheduler/jobs.py
   from ..config import settings

   _scheduler.add_job(
       discovery_job,
       "interval",
       minutes=settings.DISCOVERY_INTERVAL_MINUTES,
       id="discovery"
   )
   ```

---

## Implementation Order

Recommended order for maximum impact with minimum risk:

1. **HIGH - API Endpoints** (Issues 2.1, 2.2): Fix discovery path, add DELETE
2. **HIGH - Response Formats** (Issues 2.3, 2.4): Update health and discovery responses
3. **MEDIUM - Data Models** (Issue 4.1): Fix LatencyMetric model
4. **MEDIUM - Query Parameters** (Issue 3.1): Add filtering and pagination
5. **MEDIUM - Missing Endpoints** (Issue 3.2): Add metrics summary
6. **LOW - Documentation** (Issues 5.1, 5.2): Update docs to match reality

---

## Testing Strategy

After each fix:

1. **Unit Tests**: Add/update tests for new functionality
2. **Integration Tests**: Test full API workflow
3. **Manual Verification**: Use cURL to verify endpoints
4. **Documentation Review**: Update docs to match implementation

---

## Automation Checklist

- [ ] Create GitHub Issues for each HIGH/CRITICAL item
- [ ] Set up CI/CD to catch API/doc mismatches
- [ ] Add OpenAPI schema validation tests
- [ ] Create pre-commit hook to prevent `.env` commits
- [ ] Add automated doc generation from code

---

## Long-term Improvements

### Architecture Refactoring

1. **Implement proper Repository pattern**:
   - Create abstract base class
   - Implement all CRUD methods
   - Add to architecture documentation

2. **Add API versioning**:
   - `/api/v1/devices`
   - Allow gradual migration

3. **Implement async discovery**:
   - Job queue system
   - Status tracking
   - WebSocket notifications

### Documentation

1. **Auto-generate API docs** from code:
   - Use FastAPI's OpenAPI schema
   - Generate markdown from schema

2. **Add contract tests**:
   - Ensure code matches documented schemas

3. **Create API changelog**:
   - Track breaking changes
   - Version API separately from project

---

## Success Criteria

After remediation, verify:

- ✅ All documented endpoints exist and work as documented
- ✅ All response formats match documentation
- ✅ No security credentials in repository
- ✅ Query parameters work as documented
- ✅ All tests pass
- ✅ OpenAPI schema is accurate
- ✅ Architecture documentation reflects reality

---

## Support

If you encounter issues during remediation:

1. Check existing tests for examples
2. Review FastAPI documentation
3. Consult architecture diagrams
4. Ask in project discussions
