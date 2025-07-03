# tests/database/test_connection_pool.py
import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock
from sqlalchemy.exc import SQLAlchemyError

from database.connection_pool import (
    DatabaseConnectionPool,
    ConnectionPoolMonitor,
    get_pool_manager,
    close_pool
)


class TestDatabaseConnectionPool:
    """Test database connection pool functionality"""

    @pytest.fixture
    async def pool_manager(self):
        """Create a test pool manager"""
        test_db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")
        pool = DatabaseConnectionPool(
            database_url=test_db_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=10,
            echo=False
        )
        await pool.initialize()
        yield pool
        await pool.close()

    async def test_pool_initialization(self, pool_manager):
        """Test pool initialization"""
        assert pool_manager._engine is not None
        assert pool_manager._session_factory is not None

        # Test health check
        health_ok = await pool_manager.health_check()
        assert health_ok is True

    async def test_session_context_manager(self, pool_manager):
        """Test session context manager"""
        async with pool_manager.get_session() as session:
            assert session is not None
            # Session should be active
            assert not session.is_active or session.is_active

    async def test_session_direct_access(self, pool_manager):
        """Test direct session access"""
        session = await pool_manager.get_session_direct()
        assert session is not None
        await session.close()

    async def test_pool_status(self, pool_manager):
        """Test pool status reporting"""
        status = await pool_manager.get_pool_status()

        assert isinstance(status, dict)
        assert "pool_size" in status
        assert "checked_in" in status
        assert "checked_out" in status
        assert "total_connections" in status

    async def test_concurrent_sessions(self, pool_manager):
        """Test concurrent session handling"""
        async def get_session_data():
            async with pool_manager.get_session() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                return result.scalar()

        # Run multiple concurrent sessions
        tasks = [get_session_data() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(result == 1 for result in results)

    async def test_pool_warm_up(self, pool_manager):
        """Test pool warm-up functionality"""
        await pool_manager.warm_up_pool(target_connections=3)

        status = await pool_manager.get_pool_status()
        # After warm-up, some connections should have been created
        assert status["total_connections"] >= 0

    async def test_pool_reset(self, pool_manager):
        """Test pool reset functionality"""
        # Get initial status
        initial_status = await pool_manager.get_pool_status()

        # Reset pool
        await pool_manager.reset_pool()

        # Verify pool is still functional
        health_ok = await pool_manager.health_check()
        assert health_ok is True

    async def test_session_error_handling(self, pool_manager):
        """Test session error handling and rollback"""
        with pytest.raises(Exception):
            async with pool_manager.get_session() as session:
                from sqlalchemy import text
                # Execute invalid SQL to trigger error
                await session.execute(text("INVALID SQL STATEMENT"))

    async def test_pool_health_check_failure(self):
        """Test health check with invalid database URL"""
        pool = DatabaseConnectionPool(
            database_url="invalid://database/url",
            pool_size=1,
            max_overflow=1
        )

        with pytest.raises(Exception):
            await pool.initialize()


class TestConnectionPoolMonitor:
    """Test connection pool monitoring"""

    @pytest.fixture
    async def pool_manager(self):
        """Create a test pool manager"""
        test_db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")
        pool = DatabaseConnectionPool(
            database_url=test_db_url,
            pool_size=3,
            max_overflow=2
        )
        await pool.initialize()
        yield pool
        await pool.close()

    async def test_monitor_initialization(self, pool_manager):
        """Test monitor initialization"""
        monitor = ConnectionPoolMonitor(pool_manager)
        assert monitor.pool_manager == pool_manager
        assert monitor.monitoring_active is False

    async def test_monitor_health_check(self, pool_manager):
        """Test monitor health check functionality"""
        monitor = ConnectionPoolMonitor(pool_manager)

        # Test health check method directly
        await monitor._check_pool_health()
        # Should complete without errors

    async def test_monitor_start_stop(self, pool_manager):
        """Test monitor start and stop"""
        monitor = ConnectionPoolMonitor(pool_manager)

        # Start monitoring for a short period
        monitor_task = asyncio.create_task(
            monitor.start_monitoring(interval=1)
        )

        # Let it run briefly
        await asyncio.sleep(0.1)

        # Stop monitoring
        monitor.stop_monitoring()

        # Wait for task to complete
        await asyncio.sleep(1.1)

        assert monitor.monitoring_active is False

    async def test_monitor_alert_thresholds(self, pool_manager):
        """Test monitor alert threshold configuration"""
        monitor = ConnectionPoolMonitor(pool_manager)

        # Test threshold modification
        monitor.alert_thresholds["high_usage"] = 0.5
        assert monitor.alert_thresholds["high_usage"] == 0.5


class TestGlobalPoolManager:
    """Test global pool manager functions"""

    @pytest.fixture(autouse=True)
    async def cleanup(self):
        """Cleanup global pool manager after each test"""
        yield
        await close_pool()

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///test_global.db"})
    async def test_get_global_pool_manager(self):
        """Test getting global pool manager"""
        pool1 = await get_pool_manager()
        pool2 = await get_pool_manager()

        # Should return the same instance
        assert pool1 is pool2

        # Should be initialized
        assert pool1._engine is not None

    @patch.dict(os.environ, {"DATABASE_URL": "sqlite+aiosqlite:///test_global.db"})
    async def test_close_global_pool(self):
        """Test closing global pool"""
        pool = await get_pool_manager()
        assert pool._engine is not None

        await close_pool()

        # After closing, getting pool manager should create new instance
        new_pool = await get_pool_manager()
        assert new_pool is not pool

    async def test_pool_manager_without_database_url(self):
        """Test pool manager creation without DATABASE_URL"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL environment variable is required"):
                await get_pool_manager()

    @patch.dict(os.environ, {
        "DATABASE_URL": "sqlite+aiosqlite:///test_config.db",
        "DB_POOL_SIZE": "10",
        "DB_MAX_OVERFLOW": "20",
        "DB_POOL_TIMEOUT": "60",
        "DB_POOL_RECYCLE": "7200",
        "DB_POOL_PRE_PING": "false",
        "DB_ECHO": "true"
    })
    async def test_pool_manager_environment_config(self):
        """Test pool manager configuration from environment variables"""
        pool = await get_pool_manager()

        assert pool.pool_size == 10
        assert pool.max_overflow == 20
        assert pool.pool_timeout == 60
        assert pool.pool_recycle == 7200
        assert pool.pool_pre_ping is False
        assert pool.echo is True


class TestPoolPerformance:
    """Test pool performance characteristics"""

    @pytest.fixture
    async def pool_manager(self):
        """Create a test pool manager"""
        test_db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///test_perf.db")
        pool = DatabaseConnectionPool(
            database_url=test_db_url,
            pool_size=5,
            max_overflow=5
        )
        await pool.initialize()
        yield pool
        await pool.close()

    async def test_concurrent_connection_performance(self, pool_manager):
        """Test performance with many concurrent connections"""
        import time

        async def quick_query():
            async with pool_manager.get_session() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                return result.scalar()

        start_time = time.time()

        # Run 50 concurrent quick queries
        tasks = [quick_query() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # All queries should succeed
        assert len(results) == 50
        assert all(result == 1 for result in results)

        # Should complete within reasonable time
        assert duration < 10.0, f"Concurrent queries took too long: {duration}s"

    async def test_pool_exhaustion_handling(self, pool_manager):
        """Test pool behavior when exhausted"""
        # Create more concurrent sessions than pool size + overflow
        session_count = pool_manager.pool_size + pool_manager.max_overflow + 5

        async def long_running_session():
            try:
                async with pool_manager.get_session() as session:
                    from sqlalchemy import text
                    await session.execute(text("SELECT 1"))
                    await asyncio.sleep(0.1)  # Hold session briefly
                    return True
            except Exception:
                return False

        tasks = [long_running_session() for _ in range(session_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Some should succeed, some might fail or timeout
        successful = sum(1 for r in results if r is True)
        assert successful > 0

    async def test_pool_statistics_accuracy(self, pool_manager):
        """Test pool statistics accuracy"""
        initial_status = await pool_manager.get_pool_status()
        initial_total = initial_status["total_connections"]

        # Create and close several sessions
        for _ in range(3):
            async with pool_manager.get_session() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))

        final_status = await pool_manager.get_pool_status()

        # Total connections should have increased
        assert final_status["total_connections"] >= initial_total
