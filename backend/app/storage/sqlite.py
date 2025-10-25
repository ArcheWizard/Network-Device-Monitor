from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import aiosqlite


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS devices (
  id TEXT PRIMARY KEY,
  ip TEXT,
  mac TEXT,
  hostname TEXT,
  vendor TEXT,
  device_type TEXT,
  status TEXT,
  first_seen INTEGER,
  last_seen INTEGER,
  tags TEXT
);
"""


class SqliteInventoryRepo:
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def upsert_device(self, data: dict) -> None:
        # If we have a MAC, check if there's an existing device with same IP but IP-based ID
        mac = data.get("mac")
        ip = data.get("ip")
        dev_id = data.get("id")

        if mac and ip:
            # Check for IP-only entry to merge
            async with self._conn.execute(
                "SELECT id FROM devices WHERE ip=? AND id=? AND mac IS NULL", (ip, ip)
            ) as cur:
                old_row = await cur.fetchone()
                if old_row:
                    # Delete the IP-only entry; we'll create MAC-based one below
                    await self._conn.execute("DELETE FROM devices WHERE id=?", (ip,))

        tags_str = json.dumps(data.get("tags") or {})
        async with self._conn.execute(
            """
            INSERT INTO devices(id, ip, mac, hostname, vendor, device_type, status, first_seen, last_seen, tags)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              ip=COALESCE(excluded.ip, devices.ip),
              mac=COALESCE(excluded.mac, devices.mac),
              hostname=COALESCE(excluded.hostname, devices.hostname),
              vendor=COALESCE(excluded.vendor, devices.vendor),
              device_type=COALESCE(excluded.device_type, devices.device_type),
              status=COALESCE(excluded.status, devices.status),
              first_seen=COALESCE(devices.first_seen, excluded.first_seen),
              last_seen=COALESCE(excluded.last_seen, devices.last_seen),
              tags=COALESCE(excluded.tags, devices.tags)
            """,
            (
                dev_id,
                data.get("ip"),
                data.get("mac"),
                data.get("hostname"),
                data.get("vendor"),
                data.get("device_type"),
                data.get("status"),
                data.get("first_seen"),
                data.get("last_seen"),
                tags_str,
            ),
        ):
            pass
        await self._conn.commit()

    async def list_devices(self) -> list[dict]:
        rows = []
        async with self._conn.execute(
            "SELECT id, ip, mac, hostname, vendor, device_type, status, first_seen, last_seen, tags FROM devices"
        ) as cur:
            async for row in cur:
                rows.append(row)
        devices: list[dict] = []
        for r in rows:
            tags: dict[str, Any] = {}
            try:
                tags = json.loads(r[9]) if r[9] else {}
            except Exception:
                tags = {}
            devices.append(
                {
                    "id": r[0],
                    "ip": r[1],
                    "mac": r[2],
                    "hostname": r[3],
                    "vendor": r[4],
                    "device_type": r[5],
                    "status": r[6],
                    "first_seen": r[7],
                    "last_seen": r[8],
                    "tags": tags,
                }
            )
        return devices

    async def get_device(self, id: str) -> Optional[dict]:
        async with self._conn.execute(
            "SELECT id, ip, mac, hostname, vendor, device_type, status, first_seen, last_seen, tags FROM devices WHERE id=?",
            (id,),
        ) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            try:
                tags = json.loads(row[9]) if row[9] else {}
            except Exception:
                tags = {}
            return {
                "id": row[0],
                "ip": row[1],
                "mac": row[2],
                "hostname": row[3],
                "vendor": row[4],
                "device_type": row[5],
                "status": row[6],
                "first_seen": row[7],
                "last_seen": row[8],
                "tags": tags,
            }


async def init_sqlite(db_path: Optional[str] = None) -> SqliteInventoryRepo:
    """Initialize SQLite DB and return repository instance."""
    if db_path is None:
        # backend/app/storage/sqlite.py -> backend dir at parents[2]
        backend_dir = Path(__file__).resolve().parents[2]
        data_dir = backend_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(data_dir / "devices.db")

    conn = await aiosqlite.connect(db_path)
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute(SCHEMA_SQL)
    await conn.commit()
    return SqliteInventoryRepo(conn)
