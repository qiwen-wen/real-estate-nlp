"""Simple in-memory TTL cache shared across endpoints.

Endpoints decide whether to use it. Keys are flat strings like
``"search:3 bed in irvine:10"``. Values are JSON-serializable response dicts
(without the ``cached`` flag — that's set by the caller after retrieval).
"""

from typing import Any, Callable, Tuple

from cachetools import TTLCache

# 1 hour TTL, 1024 distinct keys. Plenty for a portfolio API.
_cache: TTLCache = TTLCache(maxsize=1024, ttl=3600)


def cache_key(*parts: Any) -> str:
    return ":".join(str(p) for p in parts)


def get_or_compute(key: str, factory: Callable[[], Any]) -> Tuple[Any, bool]:
    """Return ``(value, was_cached)``. Stores the factory result on miss."""
    if key in _cache:
        return _cache[key], True
    value = factory()
    _cache[key] = value
    return value, False


def stats() -> dict:
    return {"size": len(_cache), "maxsize": _cache.maxsize, "ttl": _cache.ttl}


def clear() -> None:
    _cache.clear()
