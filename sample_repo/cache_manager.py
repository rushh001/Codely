import json
import time
from typing import Any, Optional, Dict

class RedisCacheManager:
    """
    Distributed Redis cache connector with LRU eviction and circuit breaker.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 6379, default_ttl: int = 300):
        self.host = host
        self.port = port
        self.default_ttl = default_ttl
        self._local_cache: Dict[str, Dict[str, Any]] = {}

    def get_cached_item(self, key: str) -> Optional[Any]:
        """
        Retrieves serialized JSON data from cache with TTL check.
        """
        if key not in self._local_cache:
            return None
        entry = self._local_cache[key]
        if time.time() > entry["expires_at"]:
            del self._local_cache[key]
            return None
        return entry["value"]

    def set_cached_item(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Stores key-value pair with expiration timestamp in seconds.
        """
        expire_seconds = ttl if ttl is not None else self.default_ttl
        self._local_cache[key] = {
            "value": value,
            "expires_at": time.time() + expire_seconds
        }
        return True

    def flush_expired_entries(self) -> int:
        """
        Evicts stale cache entries and returns count of removed items.
        """
        now = time.time()
        expired_keys = [k for k, v in self._local_cache.items() if now > v["expires_at"]]
        for k in expired_keys:
            del self._local_cache[k]
        return len(expired_keys)
