from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ..services import discovery as discovery_service
import time

_scheduler: AsyncIOScheduler | None = None


async def discovery_job():
    # Periodic discovery run; identify and persist results to repo
    try:
        from ..services import identification
        from ..api.routers.ws import get_manager

        results = await discovery_service.scan()
        print(f"[scheduler] discovery found {len(results)} devices")

        ws_manager = get_manager()

        # Identify devices
        for d in results:
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
                    d["vendor"] = ident_data.get("vendor")
                    d["hostname"] = ident_data.get("hostname") or d.get("hostname")
                    d["description"] = ident_data.get("description")
                except Exception as e:
                    print(f"[scheduler] failed to identify {ip}: {e}")

        # Access repo from app.state if available
        from ..main import app

        repo = getattr(app.state, "inventory_repo", None)
        if repo:
            now = int(time.time())
            for d in results:
                dev_id = d.get("mac") or d.get("ip") or "unknown"

                # Check if this is a new device
                existing = await repo.get_device(dev_id)
                is_new = existing is None

                device_data = {
                    "id": dev_id,
                    "ip": d.get("ip"),
                    "mac": d.get("mac"),
                    "hostname": d.get("hostname"),
                    "vendor": d.get("vendor"),
                    "device_type": None,
                    "status": "unknown",  # Will be updated by monitoring
                    "first_seen": now
                    if is_new
                    else (existing.get("first_seen") if existing else now),
                    "last_seen": now,
                    "tags": {"source": d.get("source", "unknown")},
                }
                await repo.upsert_device(device_data)

                # Broadcast newly discovered device via WebSocket
                if is_new:
                    await ws_manager.broadcast(
                        {
                            "type": "device_discovered",
                            "device": {
                                "id": dev_id,
                                "ip": d.get("ip"),
                                "mac": d.get("mac"),
                                "hostname": d.get("hostname"),
                                "vendor": d.get("vendor"),
                                "source": d.get("source"),
                            },
                            "ts": now,
                        }
                    )
                    print(
                        f"[scheduler] new device discovered: {d.get('ip')} ({d.get('vendor', 'unknown')})"
                    )

            print(f"[scheduler] persisted {len(results)} identified devices to SQLite")
    except Exception as e:
        print(f"[scheduler] discovery error: {e}")


async def monitoring_tick():
    """Monitor all devices by pinging and storing metrics to InfluxDB."""
    try:
        from ..services import monitoring
        from ..main import app
        from ..api.routers.ws import get_manager

        repo = getattr(app.state, "inventory_repo", None)
        influx_writer = getattr(app.state, "influx_writer", None)
        ws_manager = get_manager()

        if not repo:
            return  # No devices to monitor

        # Get all devices from SQLite
        devices = await repo.list_devices()

        if not devices:
            return

        print(f"[scheduler] monitoring {len(devices)} devices")

        # Ping each device
        for device in devices:
            ip = device.get("ip")
            device_id = device.get("id")

            if not ip or not device_id:
                continue

            try:
                # Ping device
                metrics_data = await monitoring.ping_device(ip, count=4, timeout=2.0)

                # Write to InfluxDB if available
                if influx_writer and metrics_data["status"] != "error":
                    await influx_writer.write_metric(
                        measurement="latency",
                        tags={"device_id": device_id, "ip": ip},
                        fields={
                            "latency_avg": metrics_data.get("latency_avg"),
                            "latency_min": metrics_data.get("latency_min"),
                            "latency_max": metrics_data.get("latency_max"),
                            "packet_loss": metrics_data.get("packet_loss"),
                        },
                    )

                # Broadcast latency metrics via WebSocket
                if metrics_data["status"] == "up":
                    await ws_manager.broadcast(
                        {
                            "type": "latency",
                            "device_id": device_id,
                            "ip": ip,
                            "latency_avg": metrics_data.get("latency_avg"),
                            "latency_min": metrics_data.get("latency_min"),
                            "latency_max": metrics_data.get("latency_max"),
                            "packet_loss": metrics_data.get("packet_loss"),
                            "ts": int(time.time()),
                        }
                    )

                # Update device status in SQLite and broadcast transitions
                current_status = metrics_data["status"]
                previous_status = device.get("status")

                if (
                    current_status in ("up", "down")
                    and current_status != previous_status
                ):
                    event_type = (
                        "device_up" if current_status == "up" else "device_down"
                    )
                    await ws_manager.broadcast(
                        {
                            "type": event_type,
                            "device_id": device_id,
                            "ip": ip,
                            "hostname": device.get("hostname"),
                            "vendor": device.get("vendor"),
                            "previous_status": previous_status,
                            "ts": int(time.time()),
                        }
                    )
                    print(
                        f"[scheduler] device {ip} status changed: {previous_status} → {current_status}"
                    )

                # Update last_seen timestamp and status
                now = int(time.time())
                await repo.upsert_device(
                    {
                        "id": device_id,
                        "status": current_status
                        if current_status in ("up", "down")
                        else previous_status,
                        "last_seen": now
                        if current_status == "up"
                        else device.get("last_seen"),
                    }
                )

            except Exception as e:
                print(f"[scheduler] monitoring error for {ip}: {e}")

    except Exception as e:
        print(f"[scheduler] monitoring_tick error: {e}")


async def init_scheduler(app: FastAPI):
    global _scheduler
    if _scheduler:
        return
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(discovery_job, "interval", minutes=10, id="discovery")
    _scheduler.add_job(monitoring_tick, "interval", seconds=5, id="monitoring")
    _scheduler.start()
