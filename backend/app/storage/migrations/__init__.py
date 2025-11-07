"""Database migration module.

This module provides utilities for managing database schema migrations.
"""

from pathlib import Path
from typing import Optional

import aiosqlite


async def get_schema_version(conn: aiosqlite.Connection) -> int:
    """Get current database schema version.

    Args:
        conn: Database connection

    Returns:
        Current schema version (0 if not set)
    """
    try:
        async with conn.execute(
            "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else 0
    except aiosqlite.OperationalError:
        # Table doesn't exist yet
        return 0


async def set_schema_version(conn: aiosqlite.Connection, version: int) -> None:
    """Set database schema version.

    Args:
        conn: Database connection
        version: New schema version
    """
    # Create schema_version table if it doesn't exist
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at INTEGER NOT NULL
        )
        """
    )

    # Insert new version
    import time

    await conn.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
        (version, int(time.time())),
    )
    await conn.commit()


async def run_migration(
    conn: aiosqlite.Connection, from_version: int, to_version: int
) -> None:
    """Run database migration from one version to another.

    Args:
        conn: Database connection
        from_version: Current schema version
        to_version: Target schema version

    Raises:
        ValueError: If migration path is not supported
    """
    if from_version == to_version:
        print(f"[migration] Already at version {to_version}")
        return

    if from_version > to_version:
        raise ValueError("Downgrade migrations are not supported")

    # Migration from v0 to v1: Add users table
    if from_version == 0 and to_version >= 1:
        print("[migration] Applying migration v0 -> v1: Add users table")
        await migrate_v0_to_v1(conn)
        await set_schema_version(conn, 1)
        from_version = 1

    print(f"[migration] Migration complete. Current version: {from_version}")


async def migrate_v0_to_v1(conn: aiosqlite.Connection) -> None:
    """Migrate from v0 to v1: Add users table.

    This migration adds the users table and related indexes
    for authentication and authorization support.

    Args:
        conn: Database connection
    """
    # Create users table
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            role TEXT NOT NULL DEFAULT 'viewer',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at INTEGER NOT NULL,
            updated_at INTEGER,
            last_login INTEGER
        )
        """
    )

    # Create indexes
    await conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"
    )
    await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    await conn.commit()
    print("[migration] Users table and indexes created")


async def check_and_migrate(
    db_path: Optional[str] = None, target_version: Optional[int] = None
) -> None:
    """Check schema version and run migrations if needed.

    Args:
        db_path: Path to database file (default: backend/data/devices.db)
        target_version: Target schema version (default: latest)
    """
    if db_path is None:
        # Get default database path
        backend_dir = Path(__file__).resolve().parents[3]
        data_dir = backend_dir / "data"
        db_path = str(data_dir / "devices.db")

    if not Path(db_path).exists():
        print(f"[migration] Database {db_path} does not exist yet")
        return

    # Latest schema version
    LATEST_VERSION = 1

    if target_version is None:
        target_version = LATEST_VERSION

    conn = await aiosqlite.connect(db_path)
    try:
        current_version = await get_schema_version(conn)
        print(f"[migration] Current schema version: {current_version}")
        print(f"[migration] Target schema version: {target_version}")

        if current_version < target_version:
            await run_migration(conn, current_version, target_version)
        else:
            print("[migration] No migration needed")
    finally:
        await conn.close()


if __name__ == "__main__":
    import asyncio

    # Run migration when script is executed directly
    asyncio.run(check_and_migrate())
