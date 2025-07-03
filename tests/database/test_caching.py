# tests/database/test_caching.py
import pytest
import asyncio
import json
import time
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from database.caching import (
    CacheManager,
    QueryCache,
    CacheWarmer,
    cache_key,
    cached,
    get_cache_manager,
    get_query_cache,
    get_cached_patient_count,
    get_cached_risk_distribution
)


class TestCacheManager:
    """Test cache manager functionality"""

    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = cache_key("arg1", "arg2", param1="value1", param2="value2")
        key2 = cache_key("arg1", "arg2", param2="value2", param1="value1")
        key3 = cache_key("arg1", "arg3", param1="value1", param2="value2")

        # Same arguments should produce same key
        assert key1 == key2

        # Different arguments should produce different keys
        assert key1 != key3

    async def test_memory_cache_basic_operations(self):
        """Test basic memory cache operations"""
        cache = CacheManager(cache_type="memory", max_size=10, default_ttl=60)

        # Test set and get
        await cache.set("test_key", "test_value")
        value = await cache.get("test_key")
        assert value == "test_value"

        # Test non-existent key
        value = await cache.get("non_existent")
        assert value is None

        # Test delete
        deleted = await cache.delete("test_key")
        assert deleted is True

        value = await cache.get("test_key")
        assert value is None

    async def test_memory_cache_expiration(self):
        """Test memory cache TTL expiration"""
        cache = CacheManager(cache_type="memory", default_ttl=1)

        await cache.set("expiring_key", "expiring_value", ttl=1)

        # Should be available immediately
        value = await cache.get("expiring_key")
        assert value == "expiring_value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        value = await cache.get("expiring_key")
        assert value is None

    async def test_memory_cache_lru_eviction(self):
        """Test LRU eviction in memory cache"""
        cache = CacheManager(cache_type="memory", max_size=3, default_ttl=60)

        # Fill cache to capacity
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Access key1 to make it recently used
        await cache.get("key1")

        # Add another key, should evict key2 (least recently used)
        await cache.set("key4", "value4")

        # key1 and key3 should still exist, key2 should be evicted
        assert await cache.get("key1") == "value1"
        assert await cache.get("key3") == "value3"
        assert await cache.get("key4") == "value4"
        assert await cache.get("key2") is None

    async def test_cache_statistics(self):
        """Test cache statistics tracking"""
        cache = CacheManager(cache_type="memory")

        # Generate some cache activity
        await cache.set("key1", "value1")
        await cache.get("key1")  # Hit
        await cache.get("key2")  # Miss
        await cache.delete("key1")

        stats = cache.get_stats()

        assert stats["cache_type"] == "memory"
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert stats["sets"] >= 1
        assert stats["deletes"] >= 1
        assert "hit_rate_percent" in stats

    async def test_cache_health_check(self):
        """Test cache health check"""
        cache = CacheManager(cache_type="memory")

        health = await cache.health_check()

        assert health["status"] == "healthy"
        assert health["operations"]["set"] is True
        assert health["operations"]["get"] is True
        assert health["operations"]["delete"] is True
        assert health["backend"] == "memory"

    async def test_cache_clear(self):
        """Test cache clear functionality"""
        cache = CacheManager(cache_type="memory")

        # Add some data
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # Verify data exists
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"

        # Clear cache
        cleared = await cache.clear()
        assert cleared is True

        # Verify data is gone
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    async def test_cache_json_serialization(self):
        """Test caching of complex data structures"""
        cache = CacheManager(cache_type="memory")

        # Test dictionary
        test_dict = {"key": "value", "nested": {"inner": "data"}}
        await cache.set("dict_key", test_dict)
        retrieved_dict = await cache.get("dict_key")
        assert retrieved_dict == test_dict

        # Test list
        test_list = [1, 2, 3, {"nested": "item"}]
        await cache.set("list_key", test_list)
        retrieved_list = await cache.get("list_key")
        assert retrieved_list == test_list

    @patch('database.caching.REDIS_AVAILABLE', False)
    async def test_redis_fallback_to_memory(self):
        """Test fallback to memory cache when Redis is not available"""
        cache = CacheManager(cache_type="redis")

        # Should fallback to memory cache
        assert cache.cache_type == "memory"


class TestCachedDecorator:
    """Test cached decorator functionality"""

    async def test_cached_decorator_basic(self):
        """Test basic cached decorator functionality"""
        call_count = 0

        @cached(ttl=60)
        async def test_function(arg1, arg2):
            nonlocal call_count
            call_count += 1
            return f"{arg1}_{arg2}_{call_count}"

        # First call should execute function
        result1 = await test_function("a", "b")
        assert call_count == 1
        assert result1 == "a_b_1"

        # Second call with same args should use cache
        result2 = await test_function("a", "b")
        assert call_count == 1  # Function not called again
        assert result2 == "a_b_1"

        # Different args should execute function again
        result3 = await test_function("c", "d")
        assert call_count == 2
        assert result3 == "c_d_2"

    async def test_cached_decorator_ttl(self):
        """Test cached decorator TTL functionality"""
        call_count = 0

        @cached(ttl=1)
        async def test_function():
            nonlocal call_count
            call_count += 1
            return call_count

        # First call
        result1 = await test_function()
        assert result1 == 1

        # Second call immediately (should use cache)
        result2 = await test_function()
        assert result2 == 1

        # Wait for TTL expiration
        await asyncio.sleep(1.1)

        # Third call after expiration (should execute function)
        result3 = await test_function()
        assert result3 == 2

    async def test_cached_decorator_with_key_prefix(self):
        """Test cached decorator with key prefix"""
        @cached(ttl=60, key_prefix="test_prefix:")
        async def test_function(value):
            return value * 2

        # This should work without errors
        result = await test_function(5)
        assert result == 10


class TestQueryCache:
    """Test query cache functionality"""

    async def test_query_cache_basic(self):
        """Test basic query cache functionality"""
        cache_manager = CacheManager(cache_type="memory")
        query_cache = QueryCache(cache_manager)

        call_count = 0

        async def test_query():
            nonlocal call_count
            call_count += 1
            return {"result": call_count}

        # First call should execute query
        result1 = await query_cache.get_or_set_query_result(
            "test_query", test_query, ttl=60
        )
        assert call_count == 1
        assert result1 == {"result": 1}

        # Second call should use cache
        result2 = await query_cache.get_or_set_query_result(
            "test_query", test_query, ttl=60
        )
        assert call_count == 1  # Query not executed again
        assert result2 == {"result": 1}

    async def test_query_cache_invalidation(self):
        """Test query cache invalidation"""
        cache_manager = CacheManager(cache_type="memory")
        query_cache = QueryCache(cache_manager)

        # Set some test data
        await cache_manager.set("query:patient:123:data", {"name": "Test"})
        await cache_manager.set("query:patient:456:data", {"name": "Test2"})
        await cache_manager.set("query:assessment:789:data", {"risk": "low"})

        # Invalidate patient pattern
        await query_cache.invalidate_pattern("patient:123")

        # Patient 123 data should be gone
        assert await cache_manager.get("query:patient:123:data") is None

        # Other data should remain
        assert await cache_manager.get("query:patient:456:data") is not None
        assert await cache_manager.get("query:assessment:789:data") is not None

    async def test_patient_cache_invalidation(self):
        """Test patient-specific cache invalidation"""
        cache_manager = CacheManager(cache_type="memory")
        query_cache = QueryCache(cache_manager)

        # Set patient-related data
        await cache_manager.set("query:patient:123:assessments", [])
        await cache_manager.set("query:patient:123:profile", {})

        # Invalidate patient cache
        await query_cache.invalidate_patient_cache("123")

        # All patient 123 data should be gone
        assert await cache_manager.get("query:patient:123:assessments") is None
        assert await cache_manager.get("query:patient:123:profile") is None

    async def test_assessment_cache_invalidation(self):
        """Test assessment-specific cache invalidation"""
        cache_manager = CacheManager(cache_type="memory")
        query_cache = QueryCache(cache_manager)

        # Set assessment-related data
        await cache_manager.set("query:assessment:789:details", {})
        await cache_manager.set("query:assessment:789:symptoms", [])

        # Invalidate assessment cache
        await query_cache.invalidate_assessment_cache("789")

        # All assessment 789 data should be gone
        assert await cache_manager.get("query:assessment:789:details") is None
        assert await cache_manager.get("query:assessment:789:symptoms") is None


class TestCacheWarmer:
    """Test cache warmer functionality"""

    async def test_cache_warmer_initialization(self):
        """Test cache warmer initialization"""
        cache_manager = CacheManager(cache_type="memory")
        warmer = CacheWarmer(cache_manager)

        assert warmer.cache_manager == cache_manager
        assert warmer.warming_active is False

    async def test_cache_warmer_start_stop(self):
        """Test cache warmer start and stop"""
        cache_manager = CacheManager(cache_type="memory")
        warmer = CacheWarmer(cache_manager)

        # Start warming for a short period
        warming_task = asyncio.create_task(
            warmer.start_cache_warming(interval=1)
        )

        # Let it run briefly
        await asyncio.sleep(0.1)
        assert warmer.warming_active is True

        # Stop warming
        warmer.stop_cache_warming()

        # Wait for task to complete
        await asyncio.sleep(1.1)
        assert warmer.warming_active is False

    @patch('database.caching.get_cached_patient_count')
    @patch('database.caching.get_cached_risk_distribution')
    async def test_warm_common_queries(self, mock_risk_dist, mock_patient_count):
        """Test warming of common queries"""
        mock_patient_count.return_value = 100
        mock_risk_dist.return_value = {"low": 50, "medium": 30, "high": 20}

        cache_manager = CacheManager(cache_type="memory")
        warmer = CacheWarmer(cache_manager)

        await warmer.warm_common_queries()

        # Verify that warming functions were called
        mock_patient_count.assert_called_once()
        mock_risk_dist.assert_called_once()


class TestGlobalCacheInstances:
    """Test global cache instance management"""

    @patch.dict('os.environ', {
        'CACHE_TYPE': 'memory',
        'CACHE_MAX_SIZE': '500',
        'CACHE_DEFAULT_TTL': '600'
    })
    def test_get_cache_manager_singleton(self):
        """Test global cache manager singleton"""
        # Clear any existing instance
        import database.caching
        database.caching._cache_manager = None

        cache1 = get_cache_manager()
        cache2 = get_cache_manager()

        # Should return the same instance
        assert cache1 is cache2

        # Should have correct configuration
        assert cache1.cache_type == "memory"
        assert cache1.max_size == 500
        assert cache1.default_ttl == 600

    def test_get_query_cache_singleton(self):
        """Test global query cache singleton"""
        # Clear any existing instance
        import database.caching
        database.caching._query_cache = None

        cache1 = get_query_cache()
        cache2 = get_query_cache()

        # Should return the same instance
        assert cache1 is cache2


class TestCachedQueryFunctions:
    """Test cached query functions"""

    @patch('database.caching.get_pool_manager')
    async def test_get_cached_patient_count(self, mock_pool_manager):
        """Test cached patient count function"""
        # Mock the database session and query
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 150
        mock_session.execute.return_value = mock_result

        mock_pool = AsyncMock()
        mock_pool.get_session.return_value.__aenter__.return_value = mock_session
        mock_pool_manager.return_value = mock_pool

        # Clear cache to ensure fresh call
        cache_manager = get_cache_manager()
        await cache_manager.clear()

        # Call the cached function
        count = await get_cached_patient_count()
        assert count == 150

    @patch('database.caching.get_pool_manager')
    async def test_get_cached_risk_distribution(self, mock_pool_manager):
        """Test cached risk distribution function"""
        # Mock the database session and query
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(risk_level="low", count=50),
            MagicMock(risk_level="medium", count=30),
            MagicMock(risk_level="high", count=20)
        ]
        mock_session.execute.return_value = mock_result

        mock_pool = AsyncMock()
        mock_pool.get_session.return_value.__aenter__.return_value = mock_session
        mock_pool_manager.return_value = mock_pool

        # Clear cache to ensure fresh call
        cache_manager = get_cache_manager()
        await cache_manager.clear()

        # Call the cached function
        distribution = await get_cached_risk_distribution()
        expected = {"low": 50, "medium": 30, "high": 20}
        assert distribution == expected


class TestCacheErrorHandling:
    """Test cache error handling"""

    async def test_cache_operation_errors(self):
        """Test cache operation error handling"""
        cache = CacheManager(cache_type="memory")

        # Test error handling in get operation
        with patch.object(cache, '_memory_cache', side_effect=Exception("Test error")):
            result = await cache.get("test_key")
            assert result is None

    async def test_health_check_error_handling(self):
        """Test health check error handling"""
        cache = CacheManager(cache_type="memory")

        # Mock an error during health check
        with patch.object(cache, 'set', side_effect=Exception("Health check error")):
            health = await cache.health_check()
            assert health["status"] == "unhealthy"
            assert "error" in health

    async def test_cache_warmer_error_handling(self):
        """Test cache warmer error handling"""
        cache_manager = CacheManager(cache_type="memory")
        warmer = CacheWarmer(cache_manager)

        # Mock an error in warm_common_queries
        with patch.object(warmer, 'warm_common_queries', side_effect=Exception("Warming error")):
            # Should handle the error gracefully
            await warmer.warm_common_queries()  # Should not raise
