#!/usr/bin/env python3
"""Database migration script for Network Device Monitor.

This script migrates existing v0.1.0 databases to v0.2.0 by adding
the users table for authentication support.

Usage:
    python scripts/migrate_db.py
    python scripts/migrate_db.py --db-path /path/to/devices.db
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.storage.migrations import check_and_migrate


async def main():
    parser = argparse.ArgumentParser(
        description="Migrate Network Device Monitor database"
    )
    parser.add_argument(
        "--db-path",
        help="Path to database file (default: backend/data/devices.db)",
        default=None,
    )
    parser.add_argument(
        "--version",
        type=int,
        help="Target schema version (default: latest)",
        default=None,
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check version, don't migrate",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Network Device Monitor - Database Migration")
    print("=" * 60)
    print()

    if args.check_only:
        print("[INFO] Check-only mode: No changes will be made")
        print()

    try:
        if not args.check_only:
            await check_and_migrate(db_path=args.db_path, target_version=args.version)
        else:
            # Just check version
            import aiosqlite
            from app.storage.migrations import get_schema_version

            db_path = args.db_path
            if db_path is None:
                backend_dir = Path(__file__).resolve().parent.parent / "backend"
                data_dir = backend_dir / "data"
                db_path = str(data_dir / "devices.db")

            if Path(db_path).exists():
                conn = await aiosqlite.connect(db_path)
                try:
                    version = await get_schema_version(conn)
                    print(f"[INFO] Current schema version: {version}")
                finally:
                    await conn.close()
            else:
                print(f"[INFO] Database {db_path} does not exist yet")

        print()
        print("=" * 60)
        print("[SUCCESS] Migration completed successfully")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print(f"[ERROR] Migration failed: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
