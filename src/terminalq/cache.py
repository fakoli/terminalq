"""Simple file-based cache with TTL support."""
import json
import time
from pathlib import Path

from terminalq.config import CACHE_DIR
from terminalq.logging_config import log


def _cache_path(key: str) -> Path:
    """Get the file path for a cache key."""
    safe_key = key.replace("/", "_").replace(":", "_")
    return CACHE_DIR / f"{safe_key}.json"


def get(key: str) -> dict | list | None:
    """Get a cached value if it exists and hasn't expired."""
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if time.time() > data.get("expires_at", 0):
            path.unlink(missing_ok=True)
            log.debug("Cache expired: %s", key)
            return None
        log.debug("Cache hit: %s", key)
        return data.get("value")
    except (json.JSONDecodeError, KeyError):
        path.unlink(missing_ok=True)
        log.warning("Cache corrupt, removed: %s", key)
        return None


def set(key: str, value, ttl: int = 60) -> None:
    """Cache a value with a TTL in seconds."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "value": value,
            "cached_at": time.time(),
            "expires_at": time.time() + ttl,
        }
        _cache_path(key).write_text(json.dumps(data, default=str))
    except OSError as e:
        log.warning("Cache write failed for %s: %s", key, e)
