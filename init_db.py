import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from app.db import Base
from app.config import settings

async def init_db():
    # Use the same engine logic as the app
    engine = create_async_engine(settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlitepysqlite3")) # simplified for script
    # Actually, the app uses sqlite+aiosqlite. Let's just use the same one.
    new_engine = create_async_engine(settings.DATABASE_URL)
    
    async with new_engine.begin() as conn:
        # This is a bit tricky with async_sessionmaker, but Base.metadata.create_all is usually the way.
        # Since we have SQLAlchemy 2.0, we use the 'run_sync' approach or just use a sync engine for init.
        pass

# Instead of a complex init script, I'll use a simpler one that just creates tables.
from sqlalchemy import create_engine
from app.models import User, Mission, Objective, Harvest, UserMission

def create_tables():
    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()
