from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from typing import AsyncGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL environment variable is missing!")

print(f"�� Connecting to Supabase (direct connection)...")

# Create async engine - simple configuration for direct connection
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Dependency to get database session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            print(f"❌ Database session error: {e}")
            raise
        finally:
            await session.close()

# Database initialization
async def init_db():
    """Initialize database tables"""
    try:
        from database.models import Base
        print("📋 Creating database tables (direct connection)...")
        
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
        print("✅ Database tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

# Health check function
async def check_db_connection():
    """Check if database connection is working"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1 as test"))
            value = result.scalar()
            print(f"✅ Database ping successful: {value}")
            return value == 1
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
