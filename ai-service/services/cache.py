"""
Redis AI Cache — AI Developer 2 responsibility
SHA256 cache key, 15-min TTL, hit/miss counters, cache skip flag.
"""

import os
import json
import hashlib
import logging
import time
import redis

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 15 * 60  # 15 minutes


class AiCacheService:
    """
    Wraps Redis for AI response caching.
    - Key: SHA256 of (endpoint + sorted request payload)
    - TTL: 15 minutes
    - Tracks hit/miss counters in Redis itself
    """

    def __init__(self):
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))
        password = os.getenv("REDIS_PASSWORD", None)
        self.redis = None
        self._memory_cache: dict[str, tuple[float, str]] = {}
        self._memory_hits = 0
        self._memory_misses = 0
        try:
            self.redis = redis.Redis(
                host=host,
                port=port,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            self.redis.ping()
            self._available = True
            self._backend = "redis"
            logger.info("Redis cache connected at %s:%d", host, port)
        except Exception as e:
            self._available = True
            self._backend = "memory"
            logger.info(
                "Redis unavailable (%s). Using in-memory AI cache fallback.",
                str(e),
            )

    @property
    def available(self) -> bool:
        return self._available

    def _make_key(self, endpoint: str, payload: dict) -> str:
        """Build a deterministic SHA256 cache key."""
        canonical = json.dumps({"endpoint": endpoint, "payload": payload}, sort_keys=True)
        sha = hashlib.sha256(canonical.encode()).hexdigest()
        return f"ai_cache:{sha}"

    def get(self, endpoint: str, payload: dict) -> dict | None:
        """Return cached value or None if miss / unavailable."""
        if not self._available:
            return None
        key = self._make_key(endpoint, payload)
        if self._backend == "memory":
            return self._memory_get(key)

        try:
            raw = self.redis.get(key)
            if raw:
                self.redis.incr("ai_cache:hits")
                from services.groq_client import increment_cache_hit
                increment_cache_hit()
                logger.debug("Cache HIT for key %s", key[:20])
                data = json.loads(raw)
                # Mark the response as cached
                if isinstance(data, dict) and "meta" in data:
                    data["meta"]["cached"] = True
                return data
            else:
                self.redis.incr("ai_cache:misses")
                from services.groq_client import increment_cache_miss
                increment_cache_miss()
                logger.debug("Cache MISS for key %s", key[:20])
                return None
        except Exception as e:
            logger.warning("Cache GET error: %s", str(e))
            return None

    def set(self, endpoint: str, payload: dict, value: dict) -> bool:
        """Store value with TTL. Returns True on success."""
        if not self._available:
            return False
        key = self._make_key(endpoint, payload)
        if self._backend == "memory":
            self._memory_cache[key] = (time.time() + CACHE_TTL_SECONDS, json.dumps(value))
            return True

        try:
            self.redis.setex(key, CACHE_TTL_SECONDS, json.dumps(value))
            logger.debug("Cached response for key %s (TTL %ds)", key[:20], CACHE_TTL_SECONDS)
            return True
        except Exception as e:
            logger.warning("Cache SET error: %s", str(e))
            return False

    def get_stats(self) -> dict:
        if not self._available:
            return {"available": False, "hits": 0, "misses": 0}
        if self._backend == "memory":
            self._purge_expired_memory_keys()
            total = self._memory_hits + self._memory_misses
            hit_rate = round(self._memory_hits / total * 100, 1) if total > 0 else 0.0
            return {
                "available": True,
                "backend": "memory",
                "hits": self._memory_hits,
                "misses": self._memory_misses,
                "total_requests": total,
                "hit_rate_percent": hit_rate,
                "ttl_seconds": CACHE_TTL_SECONDS,
                "entries": len(self._memory_cache),
            }

        try:
            hits = int(self.redis.get("ai_cache:hits") or 0)
            misses = int(self.redis.get("ai_cache:misses") or 0)
            total = hits + misses
            hit_rate = round(hits / total * 100, 1) if total > 0 else 0.0
            return {
                "available": True,
                "backend": "redis",
                "hits": hits,
                "misses": misses,
                "total_requests": total,
                "hit_rate_percent": hit_rate,
                "ttl_seconds": CACHE_TTL_SECONDS,
            }
        except Exception as e:
            return {"available": False, "error": str(e)}

    def invalidate(self, endpoint: str, payload: dict) -> bool:
        """Delete a specific cache entry (for fresh=true requests)."""
        if not self._available:
            return False
        key = self._make_key(endpoint, payload)
        if self._backend == "memory":
            return self._memory_cache.pop(key, None) is not None

        try:
            self.redis.delete(key)
            return True
        except Exception:
            return False

    def _memory_get(self, key: str) -> dict | None:
        item = self._memory_cache.get(key)
        if not item:
            self._memory_misses += 1
            from services.groq_client import increment_cache_miss
            increment_cache_miss()
            return None

        expires_at, raw = item
        if expires_at <= time.time():
            self._memory_cache.pop(key, None)
            self._memory_misses += 1
            from services.groq_client import increment_cache_miss
            increment_cache_miss()
            return None

        self._memory_hits += 1
        from services.groq_client import increment_cache_hit
        increment_cache_hit()
        data = json.loads(raw)
        if isinstance(data, dict) and "meta" in data:
            data["meta"]["cached"] = True
        return data

    def _purge_expired_memory_keys(self) -> None:
        now = time.time()
        expired = [
            key for key, (expires_at, _raw) in self._memory_cache.items()
            if expires_at <= now
        ]
        for key in expired:
            self._memory_cache.pop(key, None)


# Module-level singleton
_cache_service: AiCacheService | None = None


def get_cache_service() -> AiCacheService:
    global _cache_service
    if _cache_service is None:
        _cache_service = AiCacheService()
    return _cache_service
