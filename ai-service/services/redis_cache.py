from __future__ import annotations

import json
import os
from typing import Any


class RedisCache:
    def __init__(
        self,
        url: str | None = None,
        ttl_s: int = 600,
        namespace: str = "ai-cache",
    ):
        self._ttl_s = max(0, int(ttl_s))
        self._namespace = namespace.strip(":") or "ai-cache"
        self._client = None

        try:
            from redis import Redis
        except ImportError:
            return

        redis_url = (url or os.getenv("REDIS_URL", "")).strip()
        if redis_url:
            self._client = Redis.from_url(redis_url, decode_responses=True)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def get(self, key: str) -> Any | None:
        if self._client is None:
            return None

        raw = self._client.get(self._cache_key(key))
        if raw is None:
            return None

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            self._client.delete(self._cache_key(key))
            return None

    def set(self, key: str, value: Any) -> None:
        if self._client is None:
            return

        payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
        cache_key = self._cache_key(key)
        if self._ttl_s > 0:
            self._client.setex(cache_key, self._ttl_s, payload)
        else:
            self._client.set(cache_key, payload)

    def _cache_key(self, key: str) -> str:
        return f"{self._namespace}:{key}"
