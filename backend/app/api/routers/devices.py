import time
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ...models.device import Device
from ...models.user import User
from ...services import discovery
from ..dependencies import get_current_user, require_operator

router = APIRouter()

# in-memory stub for now
_DEVICES: dict[str, Device] = {}


@router.get("/devices", response_model=list[Device])
async def list_devices(
    request: Request,
    status: Optional[Literal["up", "down", "unknown", "all"]] = "all",
    limit: int = 100,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user),
):
    """List all devices with optional filtering and pagination.

    Requires: Viewer role or higher (if auth enabled)

    Args:
        status: Filter by device status (up/down/unknown/all)
        limit: Maximum number of results (default 100)
        offset: Pagination offset (default 0)

    Returns:
        List of Device objects
    """
    # Try to use the SQLite repository if initialized; fallback to stub
    repo = getattr(request.app.state, "inventory_repo", None)
    if repo:
        items = await repo.list_devices()

        # Filter by status if not "all"
        if status != "all":
            items = [d for d in items if d.get("status") == status]

        # Apply pagination
        paginated = items[offset : offset + limit]

        # Convert dicts to Device models for response_model enforcement
        return [Device(**it) for it in paginated]

    # Fallback to in-memory stub
    devices_list = list(_DEVICES.values())

    # Filter by status if not "all"
    if status != "all":
        devices_list = [d for d in devices_list if d.status == status]

    # Apply pagination
    return devices_list[offset : offset + limit]


# IMPORTANT: Specific routes MUST come before parameterized routes to avoid conflicts
# FastAPI matches routes in order, so /devices/live and /devices/archived must be
# defined before /devices/{device_id} to prevent "live" and "archived" from being
# treated as device IDs.

@router.get("/devices/live", response_model=list[Device])
async def list_live_devices(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    """List only live/offline devices (excludes archived).

    Requires: Viewer role or higher (if auth enabled)

    Returns:
        List of non-archived Device objects
    """
    repo = getattr(request.app.state, "inventory_repo", None)
    if repo:
        items = await repo.list_live_devices()
        return [Device(**it) for it in items]
    return []


@router.get("/devices/archived", response_model=list[Device])
async def list_archived_devices(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    """List archived devices.

    Requires: Viewer role or higher (if auth enabled)

    Returns:
        List of archived Device objects
    """
    repo = getattr(request.app.state, "inventory_repo", None)
    if repo:
        items = await repo.list_archived_devices()
        return [Device(**it) for it in items]
    return []


# Parameterized routes come AFTER specific routes
@router.get("/devices/{device_id}", response_model=Device)
async def get_device(
    device_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get a single device by ID.

    Requires: Viewer role or higher (if auth enabled)
    """
    repo = getattr(request.app.state, "inventory_repo", None)
    if repo:
        item = await repo.get_device(device_id)
        if item:
            return Device(**item)
    # Fallback to in-memory stub
    dev = _DEVICES.get(device_id)
    if dev:
        return dev
    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="Device not found")


@router.delete("/devices/{device_id}", status_code=204)
async def delete_device(
    device_id: str,
    request: Request,
    current_user: User = Depends(require_operator),
):
    """Delete a device from inventory.

    Requires: Operator role or higher

    Args:
        device_id: Device identifier (MAC or IP)

    Returns:
        204 No Content on success

    Raises:
        404: Device not found
        503: Database unavailable
    """
    from fastapi import HTTPException
    from fastapi.responses import Response

    repo = getattr(request.app.state, "inventory_repo", None)
    if not repo:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Check if device exists
    existing = await repo.get_device(device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")

    # Delete device
    await repo.delete_device(device_id)

    # Return 204 No Content
    return Response(status_code=204)


@router.post("/devices/{device_id}/archive", status_code=204)
async def archive_device(
    device_id: str,
    request: Request,
    current_user: User = Depends(require_operator),
):
    """Archive a device (soft delete).

    Requires: Operator role or higher

    Args:
        device_id: Device identifier (MAC or IP)

    Returns:
        204 No Content on success

    Raises:
        404: Device not found
        503: Database unavailable
    """
    from fastapi import HTTPException
    from fastapi.responses import Response

    repo = getattr(request.app.state, "inventory_repo", None)
    if not repo:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Check if device exists
    existing = await repo.get_device(device_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")

    # Archive device
    await repo.archive_device(device_id)

    return Response(status_code=204)


@router.post("/devices/{device_id}/restore", status_code=204)
async def restore_device(
    device_id: str,
    request: Request,
    current_user: User = Depends(require_operator),
):
    """Restore an archived device.

    Requires: Operator role or higher

    Args:
        device_id: Device identifier (MAC or IP)

    Returns:
        204 No Content on success

    Raises:
        404: Device not found
        503: Database unavailable
    """
    from fastapi import HTTPException
    from fastapi.responses import Response

    repo = getattr(request.app.state, "inventory_repo", None)
    if not repo:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Restore device
    success = await repo.restore_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")

    return Response(status_code=204)


class DiscoveryScanRequest(BaseModel):
    cidr: Optional[str] = None
    interface: Optional[str] = None
    arp_timeout: Optional[float] = None
    ping_timeout: Optional[float] = None
    persist: Optional[bool] = True  # default to persisting results
    identify: Optional[bool] = True  # default to identifying devices (OUI + SNMP)


@router.post("/devices/discover")
async def discovery_scan(
    request: Request,
    req: DiscoveryScanRequest | None = None,
    current_user: User = Depends(require_operator),
):
    """Trigger on-demand discovery scan and return discovered devices.

    Requires: Operator role or higher

    If persist=True (default), discovered devices are upserted to SQLite.
    If identify=True (default), discovered devices are identified via OUI and SNMP.
    """
    from ...services import identification

    params = req.model_dump() if req else {}  # Pydantic v2
    devices = await discovery.scan(
        cidr=params.get("cidr"),
        interface=params.get("interface"),
        arp_timeout=params.get("arp_timeout") or 3.0,
        ping_timeout=params.get("ping_timeout") or 1.0,
    )

    # Identify devices if requested
    identify_flag = params.get("identify", True)
    if identify_flag:
        for d in devices:
            ip = d.get("ip")
            mac = d.get("mac")
            if ip:
                try:
                    ident_data = await identification.identify_device(
                        ip=ip,
                        mac=mac,
                        use_oui=True,
                        use_snmp=True,
                    )
                    # Merge identification data into device dict
                    d["vendor"] = ident_data.get("vendor")
                    d["hostname"] = ident_data.get("hostname") or d.get("hostname")
                    d["description"] = ident_data.get("description")
                except Exception as e:
                    import logging

                    logging.warning("Failed to identify device %s: %s", ip, e)

    # Persist to repo if available and requested
    persist = params.get("persist", True)
    repo = getattr(request.app.state, "inventory_repo", None) if request else None
    if persist and repo:
        now = int(time.time())
        for d in devices:
            # Derive stable ID from MAC if available, else IP
            dev_id = d.get("mac") or d.get("ip") or "unknown"
            device_data = {
                "id": dev_id,
                "ip": d.get("ip"),
                "mac": d.get("mac"),
                "hostname": d.get("hostname"),
                "vendor": d.get("vendor"),
                "device_type": None,
                "first_seen": now,
                "last_seen": now,
                "tags": {"source": d.get("source", "unknown")},
            }
            await repo.upsert_device(device_data)

    return {
        "count": len(devices),
        "devices": devices,
        "persisted": persist and repo is not None,
        "identified": identify_flag,
    }
