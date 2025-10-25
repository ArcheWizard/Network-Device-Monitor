from fastapi import APIRouter, Request
from ...models.device import Device
from ...services import discovery
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter()

# in-memory stub for now
_DEVICES: dict[str, Device] = {}


@router.get("/devices", response_model=list[Device])
async def list_devices(request: Request):
    # Try to use the SQLite repository if initialized; fallback to stub
    repo = getattr(request.app.state, "inventory_repo", None)
    if repo:
        items = await repo.list_devices()  # type: ignore[attr-defined]
        # Convert dicts to Device models for response_model enforcement
        return [Device(**it) for it in items]
    return list(_DEVICES.values())


@router.get("/devices/{device_id}", response_model=Device)
async def get_device(device_id: str, request: Request):
    """Get a single device by ID."""
    repo = getattr(request.app.state, "inventory_repo", None)
    if repo:
        item = await repo.get_device(device_id)  # type: ignore[attr-defined]
        if item:
            return Device(**item)
    # Fallback to in-memory stub
    dev = _DEVICES.get(device_id)
    if dev:
        return dev
    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="Device not found")


class DiscoveryScanRequest(BaseModel):
    cidr: Optional[str] = None
    interface: Optional[str] = None
    arp_timeout: Optional[float] = None
    ping_timeout: Optional[float] = None
    persist: Optional[bool] = True  # default to persisting results
    identify: Optional[bool] = True  # default to identifying devices (OUI + SNMP)


@router.post("/discovery/scan")
async def discovery_scan(request: Request, req: DiscoveryScanRequest | None = None):
    """Trigger on-demand discovery scan and return discovered devices.

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
            await repo.upsert_device(device_data)  # type: ignore[attr-defined]

    return {
        "count": len(devices),
        "devices": devices,
        "persisted": persist and repo is not None,
        "identified": identify_flag,
    }
