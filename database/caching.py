# database/caching.py
"""
Advanced database caching and optimization layer
"""
import asyncio
import json
import logging
import hashlib
from typing import Any, Dict, Optional, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import pickle
import os

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheManager:
    """Advanced caching manager with multiple backends"""

    def __init__(self, cache_type: str = "memory", **kwargs):
        self.cache_type = cache_type
        self.cache_backend = None
        self._memory_cache = {}
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }

        if cache_type == "redis" and REDIS_AVAILABLE:
            self._init_redis_cache(**kwargs)
        elif cache_type == "memory":
            self._init_memory_cache(**kwargs)
        else:
            logger.warning(f"Cache type '{cache_type}' not available, falling back to memory cache")
            self._init_memory_cache(**kwargs)

    def _init_redis_cache(self, **kwargs):
        """Initialize Redis cache backend"""
        try:
            redis_url = kwargs.get("redis_url", os.getenv("REDIS_URL", "redis://localhost:6379"))
            self.cache_backend = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.cache_type = "redis"
            logger.info("✅ Redis cache backend initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis cache: {e}")
            self._init_memory_cache(**kwargs)

    def _init_memory_cache(self, **kwargs):
        """Initialize memory cache backend"""
        self.max_size = kwargs.get("max_size", 1000)
        self.default_ttl = kwargs.get("default_ttl", 300)  # 5 minutes
        self._memory_cache = {}
        self._cache_access_times = {}
        self.cache_type = "memory"
        logger.info(f"✅ Memory cache backend initialized (max_size: {self.max_size})")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.cache_type == "redis" and self.cache_backend:
                value = await self.cache_backend.get(key)
                if value is not None:
                    self._cache_stats["hits"] += 1
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                else:
                    self._cache_stats["misses"] += 1
                    return None

            else:  # Memory cache
                if key in self._memory_cache:
                    entry = self._memory_cache[key]
                    if entry["expires_at"] > datetime.now():
                        self._cache_stats["hits"] += 1
                        self._cache_access_times[key] = datetime.now()
                        return entry["value"]
                    else:
                        # Expired entry
                        del self._memory_cache[key]
                        if key in self._cache_access_times:
                            del self._cache_access_times[key]

                self._cache_stats["misses"] += 1
                return None

        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            self._cache_stats["misses"] += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            if self.cache_type == "redis" and self.cache_backend:
                serialized_value = json.dumps(value) if not isinstance(value, str) else value
                result = await self.cache_backend.setex(
                    key,
                    ttl or self.default_ttl,
                    serialized_value
                )
                self._cache_stats["sets"] += 1
                return bool(result)

            else:  # Memory cache
                # Implement LRU eviction if cache is full
                if len(self._memory_cache) >= self.max_size:
                    await self._evict_lru()

                expires_at = datetime.now() + timedelta(seconds=ttl or self.default_ttl)
                self._memory_cache[key] = {
                    "value": value,
                    "expires_at": expires_at,
                    "created_at": datetime.now()
                }
                self._cache_access_times[key] = datetime.now()
                self._cache_stats["sets"] += 1
                return True

        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            if self.cache_type == "redis" and self.cache_backend:
                result = await self.cache_backend.delete(key)
                self._cache_stats["deletes"] += 1
                return bool(result)

            else:  # Memory cache
                if key in self._memory_cache:
                    del self._memory_cache[key]
                    if key in self._cache_access_times:
                        del self._cache_access_times[key]
                    self._cache_stats["deletes"] += 1
                    return True
                return False

        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False

    async def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.cache_type == "redis" and self.cache_backend:
                await self.cache_backend.flushdb()
            else:
                self._memory_cache.clear()
                self._cache_access_times.clear()

            logger.info("Cache cleared successfully")
            return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def _evict_lru(self):
        """Evict least recently used items from memory cache"""
        if not self._cache_access_times:
            return

        # Find least recently used key
        lru_key = min(self._cache_access_times.keys(),
                     key=lambda k: self._cache_access_times[k])

        if lru_key in self._memory_cache:
            del self._memory_cache[lru_key]
        if lru_key in self._cache_access_times:
            del self._cache_access_times[lru_key]

        logger.debug(f"Evicted LRU cache entry: {lru_key}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (self._cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        stats = {
            "cache_type": self.cache_type,
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "sets": self._cache_stats["sets"],
            "deletes": self._cache_stats["deletes"],
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }

        if self.cache_type == "memory":
            stats.update({
                "memory_cache_size": len(self._memory_cache),
                "max_cache_size": self.max_size,
                "cache_utilization_percent": round(len(self._memory_cache) / self.max_size * 100, 2)
            })

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        try:
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.now().isoformat()}

            # Test set operation
            set_success = await self.set(test_key, test_value, ttl=5)

            # Test get operation
            retrieved_value = await self.get(test_key)
            get_success = retrieved_value is not None

            # Test delete operation
            delete_success = await self.delete(test_key)

            return {
                "status": "healthy" if all([set_success, get_success, delete_success]) else "unhealthy",
                "operations": {
                    "set": set_success,
                    "get": get_success,
                    "delete": delete_success
                },
                "backend": self.cache_type,
                "stats": self.get_stats()
            }

        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "backend": self.cache_type
            }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager"""
    global _cache_manager

    if _cache_manager is None:
        cache_type = os.getenv("CACHE_TYPE", "memory")
        _cache_manager = CacheManager(
            cache_type=cache_type,
            redis_url=os.getenv("REDIS_URL"),
            max_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "300"))
        )

    return _cache_manager


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items()) if kwargs else {}
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()

            # Generate cache key
            func_key = f"{key_prefix}{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = await cache_manager.get(func_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(func_key, result, ttl=ttl)
            logger.debug(f"Cached result for {func.__name__}")

            return result

        return wrapper
    return decorator


class QueryCache:
    """Specialized caching for database queries"""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager or get_cache_manager()

    async def get_or_set_query_result(
        self,
        query_key: str,
        query_func: Callable,
        ttl: int = 300,
        *args,
        **kwargs
    ) -> Any:
        """Get query result from cache or execute and cache"""
        full_key = f"query:{query_key}"

        # Try cache first
        cached_result = await self.cache_manager.get(full_key)
        if cached_result is not None:
            logger.debug(f"Query cache hit: {query_key}")
            return cached_result

        # Execute query and cache result
        result = await query_func(*args, **kwargs)
        await self.cache_manager.set(full_key, result, ttl=ttl)
        logger.debug(f"Query result cached: {query_key}")

        return result

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        if self.cache_manager.cache_type == "redis" and self.cache_manager.cache_backend:
            try:
                keys = await self.cache_manager.cache_backend.keys(f"*{pattern}*")
                if keys:
                    await self.cache_manager.cache_backend.delete(*keys)
                    logger.info(f"Invalidated {len(keys)} cache entries matching pattern: {pattern}")
            except Exception as e:
                logger.error(f"Failed to invalidate cache pattern '{pattern}': {e}")

        else:  # Memory cache
            keys_to_delete = [
                key for key in self.cache_manager._memory_cache.keys()
                if pattern in key
            ]
            for key in keys_to_delete:
                await self.cache_manager.delete(key)
            logger.info(f"Invalidated {len(keys_to_delete)} memory cache entries matching pattern: {pattern}")

    async def invalidate_patient_cache(self, patient_id: str):
        """Invalidate all cache entries for a specific patient"""
        await self.invalidate_pattern(f"patient:{patient_id}")

    async def invalidate_assessment_cache(self, assessment_id: str):
        """Invalidate all cache entries for a specific assessment"""
        await self.invalidate_pattern(f"assessment:{assessment_id}")


# Commonly used cached query functions
@cached(ttl=600, key_prefix="analytics:")
async def get_cached_patient_count():
    """Get cached patient count"""
    from .connection_pool import get_pool_manager
    from .models import Patient
    from sqlalchemy import select, func

    pool_manager = await get_pool_manager()
    async with pool_manager.get_session() as session:
        result = await session.execute(select(func.count(Patient.id)))
        return result.scalar()


@cached(ttl=300, key_prefix="analytics:")
async def get_cached_risk_distribution():
    """Get cached risk level distribution"""
    from .connection_pool import get_pool_manager
    from .models import HealthAssessment
    from sqlalchemy import select, func

    pool_manager = await get_pool_manager()
    async with pool_manager.get_session() as session:
        result = await session.execute(
            select(
                HealthAssessment.risk_level,
                func.count(HealthAssessment.id).label("count")
            )
            .group_by(HealthAssessment.risk_level)
        )
        return {row.risk_level: row.count for row in result.fetchall()}


class CacheWarmer:
    """Proactive cache warming for frequently accessed data"""

    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager or get_cache_manager()
        self.warming_active = False

    async def start_cache_warming(self, interval: int = 3600):
        """Start periodic cache warming"""
        self.warming_active = True
        logger.info(f"Starting cache warming (interval: {interval}s)")

        while self.warming_active:
            try:
                await self.warm_common_queries()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Cache warming error: {e}")
                await asyncio.sleep(interval)

    def stop_cache_warming(self):
        """Stop cache warming"""
        self.warming_active = False
        logger.info("Cache warming stopped")

    async def warm_common_queries(self):
        """Warm up commonly accessed queries"""
        try:
            # Warm patient count
            await get_cached_patient_count()

            # Warm risk distribution
            await get_cached_risk_distribution()

            logger.debug("Cache warming completed successfully")

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")


# Global query cache instance
_query_cache: Optional[QueryCache] = None


def get_query_cache() -> QueryCache:
    """Get or create the global query cache"""
    global _query_cache

    if _query_cache is None:
        _query_cache = QueryCache()

    return _query_cache
