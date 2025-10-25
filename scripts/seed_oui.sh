#!/usr/bin/env bash
# Download and cache IEEE OUI database for vendor identification

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Activate virtual environment
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -f "$BACKEND_DIR/.venv/bin/activate" ]; then
    source "$BACKEND_DIR/.venv/bin/activate"
else
    echo "Warning: No virtual environment found. Ensure dependencies are installed."
fi

# Run OUI download
python -c "
import asyncio
import sys
sys.path.insert(0, '$BACKEND_DIR')
from app.utils.oui import download_oui_database

async def main():
    success = await download_oui_database(force=True)
    if success:
        print('OUI database downloaded successfully')
    else:
        print('Failed to download OUI database', file=sys.stderr)
        sys.exit(1)

asyncio.run(main())
"

echo "OUI database seeded successfully"
