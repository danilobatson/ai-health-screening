import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from dotenv import load_dotenv
from .models import Base

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"❌ Database session error: {e}")
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database and create tables"""
    try:
        print("🗄️ Connecting to Supabase (direct connection)...")
        print("📋 Recreating database tables with AI fields...")

        async with engine.begin() as conn:
            # Drop all tables first (this will remove old schema)
            await conn.run_sync(Base.metadata.drop_all)
            # Create all tables with new schema
            await conn.run_sync(Base.metadata.create_all)

        print("✅ Database tables recreated successfully!")
        return True

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def check_db_connection():
    """Check if database connection is working"""
    try:
        # Simple connection test using the engine directly
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("✅ Database connection verified!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
