"""Tests for terminalq.cache — file-based cache with TTL."""

import json
import time

from terminalq import cache


def test_set_and_get(tmp_cache_dir):
    """Store a value and retrieve it before expiry."""
    cache.set("test_key", {"price": 42.0}, ttl=300)
    result = cache.get("test_key")
    assert result == {"price": 42.0}


def test_expired_entry(tmp_cache_dir):
    """Expired entries return None and are deleted."""
    cache.set("expired_key", {"old": True}, ttl=1)
    # Manually set expiry in the past
    path = tmp_cache_dir / "expired_key.json"
    data = json.loads(path.read_text())
    data["expires_at"] = time.time() - 10
    path.write_text(json.dumps(data))

    result = cache.get("expired_key")
    assert result is None
    assert not path.exists()


def test_corrupt_json(tmp_cache_dir):
    """Corrupt cache files return None and are removed."""
    path = tmp_cache_dir / "corrupt_key.json"
    path.write_text("{{{not valid json")

    result = cache.get("corrupt_key")
    assert result is None
    assert not path.exists()


def test_missing_dir(tmp_path, monkeypatch):
    """Cache set creates the directory if it does not exist."""
    new_dir = tmp_path / "subdir" / "cache"
    monkeypatch.setattr("terminalq.cache.CACHE_DIR", new_dir)

    cache.set("new_key", [1, 2, 3], ttl=60)
    assert new_dir.exists()
    assert cache.get("new_key") == [1, 2, 3]


def test_key_sanitization(tmp_cache_dir):
    """Keys with / and : are sanitized in file names."""
    cache.set("finnhub/quote:AAPL", {"symbol": "AAPL"}, ttl=60)
    result = cache.get("finnhub/quote:AAPL")
    assert result == {"symbol": "AAPL"}
    # File should use underscores instead of special chars
    expected_file = tmp_cache_dir / "finnhub_quote_AAPL.json"
    assert expected_file.exists()
