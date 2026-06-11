"""Database initialization script.

Creates all tables and optionally seeds reference data.
Run: python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.db.database import init_db


async def main():
    print("Initializing database...")
    await init_db()
    print("✅ Database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(main())
