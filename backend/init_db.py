import asyncio
import os
import sys

# Ensure we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import postgres
from app.db.postgres import Base, init_db
import app.models.db_models  # Import all models to register them with Base

async def create_tables():
    print("Initializing DB connection...")
    await init_db()
    if not postgres.engine:
        print("Failed to initialize database engine!")
        return

    print("Creating any missing tables from db_models.py...")
    async with postgres.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Schema created successfully!")

if __name__ == "__main__":
    asyncio.run(create_tables())
