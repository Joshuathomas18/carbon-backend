"""Simple in-memory cache with TTL support."""

import time
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class InMemoryCache:
    """Thread-safe in-memory cache for satellite data and predictions."""

    def __init__(self, default_ttl: int = 604800):  # Default 7 days
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None
        
        value, expires_at = self._cache[key]
        if time.time() > expires_at:
            del self._cache[key]
            return None
            
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + ttl
        self._cache[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()


# Global cache instance
cache = InMemoryCache()
