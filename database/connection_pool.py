# database/connection_pool.py
"""
Enterprise-grade database connection pooling and management
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, NullPool, StaticPool
from sqlalchemy import text, event
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """Advanced database connection pool manager"""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        echo: bool = False
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.echo = echo

        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "checked_out": 0,
            "overflow": 0,
            "invalid_connections": 0
        }

    async def initialize(self) -> None:
        """Initialize the connection pool"""
        try:
            self._engine = create_async_engine(
                self.database_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_recycle=self.pool_recycle,
                pool_pre_ping=self.pool_pre_ping,
                echo=self.echo,
                echo_pool=False,  # Set to True for pool debugging
                future=True
            )

            # Set up event listeners for connection monitoring
            self._setup_event_listeners()

            self._session_factory = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )

            # Test the connection
            await self.health_check()
            logger.info(f"✅ Database connection pool initialized with {self.pool_size} connections")

        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool: {e}")
            raise

    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for monitoring"""

        @event.listens_for(self._engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            self._connection_stats["total_connections"] += 1
            logger.debug("New database connection established")

        @event.listens_for(self._engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            self._connection_stats["checked_out"] += 1
            self._connection_stats["active_connections"] += 1

        @event.listens_for(self._engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            self._connection_stats["active_connections"] = max(0, self._connection_stats["active_connections"] - 1)

        @event.listens_for(self._engine.sync_engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            self._connection_stats["invalid_connections"] += 1
            logger.warning(f"Database connection invalidated: {exception}")

    @asynccontextmanager
    async def get_session(self):
        """Get a database session with proper cleanup"""
        if not self._session_factory:
            raise RuntimeError("Connection pool not initialized")

        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    async def get_session_direct(self) -> AsyncSession:
        """Get a session directly (caller responsible for cleanup)"""
        if not self._session_factory:
            raise RuntimeError("Connection pool not initialized")
        return self._session_factory()

    async def health_check(self) -> bool:
        """Perform a health check on the database connection"""
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and statistics"""
        if not self._engine:
            return {"status": "not_initialized"}

        pool = self._engine.pool

        try:
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": getattr(pool, 'invalid', lambda: 0)(),
                "total_connections": self._connection_stats["total_connections"],
                "active_connections": self._connection_stats["active_connections"],
                "invalid_connections": self._connection_stats["invalid_connections"],
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle
            }
        except Exception as e:
            # Fallback for async pools that don't support all methods
            return {
                "pool_size": getattr(pool, '_size', self.pool_size),
                "checked_in": getattr(pool, '_checked_in', 0),
                "checked_out": getattr(pool, '_checked_out', 0),
                "overflow": getattr(pool, '_overflow', 0),
                "invalid": 0,
                "total_connections": self._connection_stats["total_connections"],
                "active_connections": self._connection_stats["active_connections"],
                "invalid_connections": self._connection_stats["invalid_connections"],
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
                "note": "Some metrics unavailable for async pool"
            }

    async def warm_up_pool(self, target_connections: Optional[int] = None) -> None:
        """Warm up the connection pool by pre-creating connections"""
        if not target_connections:
            target_connections = min(5, self.pool_size)

        logger.info(f"Warming up connection pool with {target_connections} connections...")

        sessions = []
        try:
            for i in range(target_connections):
                session = await self.get_session_direct()
                await session.execute(text("SELECT 1"))
                sessions.append(session)
                logger.debug(f"Warmed up connection {i + 1}/{target_connections}")

            logger.info(f"✅ Connection pool warmed up with {target_connections} connections")

        except Exception as e:
            logger.error(f"❌ Failed to warm up connection pool: {e}")
            raise
        finally:
            # Close all test sessions
            for session in sessions:
                await session.close()

    async def close(self) -> None:
        """Close the connection pool"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connection pool closed")

    async def reset_pool(self) -> None:
        """Reset the connection pool (useful for testing)"""
        if self._engine:
            await self._engine.dispose()
        await self.initialize()
        logger.info("Database connection pool reset")


class ConnectionPoolMonitor:
    """Monitor and alert on connection pool health"""

    def __init__(self, pool_manager: DatabaseConnectionPool):
        self.pool_manager = pool_manager
        self.monitoring_active = False
        self.alert_thresholds = {
            "high_usage": 0.8,  # Alert when 80% of pool is used
            "overflow_usage": 0.5,  # Alert when 50% of overflow is used
            "invalid_connections": 5  # Alert when 5+ invalid connections
        }

    async def start_monitoring(self, interval: int = 30) -> None:
        """Start continuous pool monitoring"""
        self.monitoring_active = True
        logger.info(f"Starting connection pool monitoring (interval: {interval}s)")

        while self.monitoring_active:
            try:
                await self._check_pool_health()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Pool monitoring error: {e}")
                await asyncio.sleep(interval)

    def stop_monitoring(self) -> None:
        """Stop pool monitoring"""
        self.monitoring_active = False
        logger.info("Connection pool monitoring stopped")

    async def _check_pool_health(self) -> None:
        """Check pool health and trigger alerts if needed"""
        status = await self.pool_manager.get_pool_status()

        if status.get("status") == "not_initialized":
            return

        # Check pool usage
        pool_usage = status["checked_out"] / status["pool_size"] if status["pool_size"] > 0 else 0

        if pool_usage > self.alert_thresholds["high_usage"]:
            logger.warning(
                f"🚨 High connection pool usage: {pool_usage:.1%} "
                f"({status['checked_out']}/{status['pool_size']})"
            )

        # Check overflow usage
        if status["overflow"] > 0:
            max_overflow = self.pool_manager.max_overflow
            overflow_usage = status["overflow"] / max_overflow if max_overflow > 0 else 0

            if overflow_usage > self.alert_thresholds["overflow_usage"]:
                logger.warning(
                    f"🚨 High overflow usage: {overflow_usage:.1%} "
                    f"({status['overflow']}/{max_overflow})"
                )

        # Check invalid connections
        if status["invalid_connections"] > self.alert_thresholds["invalid_connections"]:
            logger.warning(
                f"🚨 High number of invalid connections: {status['invalid_connections']}"
            )

        # Log periodic status
        logger.debug(
            f"Pool status - Size: {status['pool_size']}, "
            f"Active: {status['checked_out']}, "
            f"Overflow: {status['overflow']}, "
            f"Invalid: {status['invalid']}"
        )


# Global pool manager instance
_pool_manager: Optional[DatabaseConnectionPool] = None


async def get_pool_manager() -> DatabaseConnectionPool:
    """Get or create the global pool manager"""
    global _pool_manager

    if _pool_manager is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        _pool_manager = DatabaseConnectionPool(
            database_url=database_url,
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "30")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
        await _pool_manager.initialize()

    return _pool_manager


async def get_db_session():
    """Dependency function for getting database sessions"""
    pool_manager = await get_pool_manager()
    async with pool_manager.get_session() as session:
        yield session


async def close_pool():
    """Close the global pool manager"""
    global _pool_manager
    if _pool_manager:
        await _pool_manager.close()
        _pool_manager = None
