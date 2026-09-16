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

    print("Dropping existing tables and creating new schema based on db_models.py...")
    async with postgres.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Schema created successfully!")
    
    # We can also insert a default tenant here
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from app.models.db_models import Tenant
    
    async with AsyncSession(postgres.engine) as session:
        result = await session.execute(select(Tenant).where(Tenant.id == "default_tenant"))
        if not result.scalars().first():
            tenant = Tenant(
                id="default_tenant",
                name="Acme Corp Demo",
                api_key_hash="hashed_demo_key_123"
            )
            session.add(tenant)
            await session.commit()
            print("Default tenant 'Acme Corp Demo' created.")

if __name__ == "__main__":
    asyncio.run(create_tables())
