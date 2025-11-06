# Migration Templates

## Overview

Database migration templates for schema changes in Network Device Monitor.

## SQLite Migration Template

### Migration Script Structure

`backend/migrations/001_initial_schema.py`:

```python
"""Initial database schema migration.

Revision: 001
Description: Create initial devices table
Created: 2024-01-01
"""

REVISION = "001"
DOWN_REVISION = None
DESCRIPTION = "Create initial devices table"


async def upgrade(conn):
    """Apply migration (upgrade)."""
    await conn.execute("""
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
        )
    """)

    # Create indexes
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip)")
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac)")

    await conn.commit()
    print(f"✓ Applied migration {REVISION}: {DESCRIPTION}")


async def downgrade(conn):
    """Revert migration (downgrade)."""
    await conn.execute("DROP TABLE IF EXISTS devices")
    await conn.commit()
    print(f"✓ Reverted migration {REVISION}: {DESCRIPTION}")
```

### Add Column Migration

`backend/migrations/002_add_description_column.py`:

```python
"""Add description column to devices table.

Revision: 002
Down Revision: 001
Description: Add description field for device details
Created: 2024-01-15
"""

REVISION = "002"
DOWN_REVISION = "001"
DESCRIPTION = "Add description column to devices"


async def upgrade(conn):
    """Add description column."""
    await conn.execute("""
        ALTER TABLE devices
        ADD COLUMN description TEXT
    """)
    await conn.commit()
    print(f"✓ Applied migration {REVISION}: {DESCRIPTION}")


async def downgrade(conn):
    """Remove description column.

    Note: SQLite doesn't support DROP COLUMN before version 3.35.0.
    This creates a new table without the column and copies data.
    """
    await conn.execute("""
        CREATE TABLE devices_backup (
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
        )
    """)

    await conn.execute("""
        INSERT INTO devices_backup
        SELECT id, ip, mac, hostname, vendor, device_type, status, first_seen, last_seen, tags
        FROM devices
    """)

    await conn.execute("DROP TABLE devices")
    await conn.execute("ALTER TABLE devices_backup RENAME TO devices")

    # Recreate indexes
    await conn.execute("CREATE INDEX idx_devices_ip ON devices(ip)")
    await conn.execute("CREATE INDEX idx_devices_mac ON devices(mac)")

    await conn.commit()
    print(f"✓ Reverted migration {REVISION}: {DESCRIPTION}")
```

### Create Table Migration

`backend/migrations/003_create_alerts_table.py`:

```python
"""Create alerts table.

Revision: 003
Down Revision: 002
Description: Create table for storing alert history
Created: 2024-02-01
"""

REVISION = "003"
DOWN_REVISION = "002"
DESCRIPTION = "Create alerts table"


async def upgrade(conn):
    """Create alerts table."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            resolved_at INTEGER,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)

    await conn.execute("CREATE INDEX idx_alerts_device_id ON alerts(device_id)")
    await conn.execute("CREATE INDEX idx_alerts_created_at ON alerts(created_at)")

    await conn.commit()
    print(f"✓ Applied migration {REVISION}: {DESCRIPTION}")


async def downgrade(conn):
    """Drop alerts table."""
    await conn.execute("DROP TABLE IF EXISTS alerts")
    await conn.commit()
    print(f"✓ Reverted migration {REVISION}: {DESCRIPTION}")
```

### Data Migration Template

`backend/migrations/004_migrate_device_data.py`:

```python
"""Migrate existing device data.

Revision: 004
Down Revision: 003
Description: Update device status values
Created: 2024-03-01
"""

REVISION = "004"
DOWN_REVISION = "003"
DESCRIPTION = "Migrate device status values"


async def upgrade(conn):
    """Update device status values from old to new format."""
    # Map old status values to new ones
    await conn.execute("""
        UPDATE devices
        SET status = CASE
            WHEN status = 'online' THEN 'up'
            WHEN status = 'offline' THEN 'down'
            ELSE 'unknown'
        END
    """)

    await conn.commit()
    print(f"✓ Applied migration {REVISION}: {DESCRIPTION}")


async def downgrade(conn):
    """Revert status values to old format."""
    await conn.execute("""
        UPDATE devices
        SET status = CASE
            WHEN status = 'up' THEN 'online'
            WHEN status = 'down' THEN 'offline'
            ELSE 'unknown'
        END
    """)

    await conn.commit()
    print(f"✓ Reverted migration {REVISION}: {DESCRIPTION}")
```

## Migration Runner

`backend/migrations/runner.py`:

```python
"""Database migration runner."""

import asyncio
import importlib
import aiosqlite
from pathlib import Path
from typing import List, Optional


async def get_current_revision(conn: aiosqlite.Connection) -> Optional[str]:
    """Get current migration revision."""
    try:
        async with conn.execute("SELECT revision FROM migrations ORDER BY id DESC LIMIT 1") as cur:
            row = await cur.fetchone()
            return row[0] if row else None
    except aiosqlite.OperationalError:
        # migrations table doesn't exist yet
        return None


async def init_migrations_table(conn: aiosqlite.Connection):
    """Initialize migrations tracking table."""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            revision TEXT NOT NULL UNIQUE,
            description TEXT,
            applied_at INTEGER NOT NULL
        )
    """)
    await conn.commit()


async def apply_migration(conn: aiosqlite.Connection, migration_file: Path):
    """Apply a single migration."""
    # Import migration module
    module_name = f"migrations.{migration_file.stem}"
    migration = importlib.import_module(module_name)

    # Check if already applied
    current_rev = await get_current_revision(conn)
    if current_rev == migration.REVISION:
        print(f"Migration {migration.REVISION} already applied")
        return

    # Run upgrade
    await migration.upgrade(conn)

    # Record migration
    import time
    await conn.execute(
        "INSERT INTO migrations(revision, description, applied_at) VALUES(?, ?, ?)",
        (migration.REVISION, migration.DESCRIPTION, int(time.time()))
    )
    await conn.commit()


async def migrate(db_path: str = "backend/data/devices.db", target_revision: Optional[str] = None):
    """Run migrations to target revision (or latest if None)."""
    conn = await aiosqlite.connect(db_path)

    try:
        await init_migrations_table(conn)

        # Get migration files
        migrations_dir = Path(__file__).parent
        migration_files = sorted(migrations_dir.glob("[0-9]*.py"))

        # Apply migrations
        for migration_file in migration_files:
            await apply_migration(conn, migration_file)

            # Stop if target reached
            if target_revision:
                module_name = f"migrations.{migration_file.stem}"
                migration = importlib.import_module(module_name)
                if migration.REVISION == target_revision:
                    break

        print("✓ All migrations applied successfully")

    finally:
        await conn.close()


async def rollback(db_path: str = "backend/data/devices.db", steps: int = 1):
    """Rollback the last N migrations."""
    conn = await aiosqlite.connect(db_path)

    try:
        # Get applied migrations
        async with conn.execute(
            "SELECT revision FROM migrations ORDER BY id DESC LIMIT ?",
            (steps,)
        ) as cur:
            revisions = [row[0] async for row in cur]

        # Rollback each
        for revision in revisions:
            # Find migration file
            migrations_dir = Path(__file__).parent
            for migration_file in migrations_dir.glob("[0-9]*.py"):
                module_name = f"migrations.{migration_file.stem}"
                migration = importlib.import_module(module_name)

                if migration.REVISION == revision:
                    await migration.downgrade(conn)
                    await conn.execute("DELETE FROM migrations WHERE revision=?", (revision,))
                    await conn.commit()
                    break

        print(f"✓ Rolled back {len(revisions)} migration(s)")

    finally:
        await conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m migrations.runner [migrate|rollback] [args]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "migrate":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        asyncio.run(migrate(target_revision=target))

    elif command == "rollback":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        asyncio.run(rollback(steps=steps))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
```

## Usage Examples

### Apply All Migrations

```bash
python -m migrations.runner migrate
```

### Apply Migrations to Specific Revision

```bash
python -m migrations.runner migrate 003
```

### Rollback Last Migration

```bash
python -m migrations.runner rollback 1
```

### Rollback Multiple Migrations

```bash
python -m migrations.runner rollback 3
```

## InfluxDB Schema Changes

InfluxDB is schema-less, but you may need to manage bucket/org changes:

```python
"""InfluxDB configuration migration."""

from influxdb_client import InfluxDBClient


def migrate_influx_schema(url: str, token: str):
    """Migrate InfluxDB schema."""
    client = InfluxDBClient(url=url, token=token)

    # Create new bucket
    buckets_api = client.buckets_api()
    org_api = client.organizations_api()

    org = org_api.find_organizations(org="local")[0]

    # Create new bucket if not exists
    existing = buckets_api.find_buckets().buckets
    if not any(b.name == "network_metrics_v2" for b in existing):
        buckets_api.create_bucket(
            bucket_name="network_metrics_v2",
            org_id=org.id,
            retention_rules=[{"everySeconds": 2592000}]  # 30 days
        )

    print("✓ InfluxDB migration complete")

    client.close()
```

## Best Practices

1. **Always include downgrade**: Every migration should be reversible
2. **Test migrations**: Test both upgrade and downgrade on dev database
3. **Backup before migrate**: Always backup production database first
4. **Small migrations**: Keep migrations focused on single changes
5. **Version control**: Commit migrations to git
6. **Document changes**: Include clear description in migration
7. **Sequential numbering**: Use incrementing numbers (001, 002, 003...)
8. **Test with data**: Test migrations on database with realistic data

## Backup Command

```bash
# Backup before migration
cp backend/data/devices.db backend/data/devices.db.backup-$(date +%Y%m%d_%H%M%S)

# Restore from backup if needed
cp backend/data/devices.db.backup-20240101_120000 backend/data/devices.db
```
