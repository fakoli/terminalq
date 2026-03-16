"""Monthly usage tracking for quota-limited APIs and tool call volume."""

import json
from datetime import datetime
from pathlib import Path

from terminalq.config import CACHE_DIR
from terminalq.logging_config import log

_USAGE_DIR = CACHE_DIR.parent / "usage"


def _usage_path(provider: str) -> Path:
    """Get the usage file path for a provider and current month."""
    month = datetime.now().strftime("%Y-%m")
    return _USAGE_DIR / f"usage_{provider}_{month}.json"


def _read_usage(provider: str) -> dict:
    """Read current usage data for a provider."""
    path = _usage_path(provider)
    if not path.exists():
        return {"calls_used": 0, "first_call": None, "last_call": None}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"calls_used": 0, "first_call": None, "last_call": None}


def _write_usage(provider: str, data: dict) -> None:
    """Write usage data for a provider."""
    _USAGE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        _usage_path(provider).write_text(json.dumps(data, default=str))
    except OSError as e:
        log.warning("Failed to write usage data for %s: %s", provider, e)


def get_monthly_usage(provider: str, limit: int = 0) -> dict:
    """Get monthly usage stats for a provider.

    Args:
        provider: Provider name (e.g., "brave_search", "polygon")
        limit: Monthly call limit (0 = unlimited)

    Returns:
        Dict with calls_used, calls_limit, month, remaining.
    """
    data = _read_usage(provider)
    month = datetime.now().strftime("%Y-%m")
    calls_used = data.get("calls_used", 0)
    return {
        "provider": provider,
        "calls_used": calls_used,
        "calls_limit": limit if limit > 0 else "unlimited",
        "month": month,
        "remaining": (limit - calls_used) if limit > 0 else "unlimited",
        "first_call": data.get("first_call"),
        "last_call": data.get("last_call"),
    }


def increment_usage(provider: str) -> dict:
    """Atomically increment usage counter and return updated stats.

    Returns:
        Dict with updated calls_used and timestamp.
    """
    data = _read_usage(provider)
    now = datetime.now().isoformat()
    data["calls_used"] = data.get("calls_used", 0) + 1
    if not data.get("first_call"):
        data["first_call"] = now
    data["last_call"] = now
    _write_usage(provider, data)
    return data


def check_budget(provider: str, limit: int) -> bool:
    """Check if provider is under its monthly call limit.

    Args:
        provider: Provider name
        limit: Monthly call limit

    Returns:
        True if under limit, False if at or over limit.
    """
    data = _read_usage(provider)
    return data.get("calls_used", 0) < limit


def get_daily_usage(provider: str) -> dict:
    """Get today's usage stats for a provider."""
    today = datetime.now().strftime("%Y-%m-%d")
    path = _USAGE_DIR / f"daily_{provider}_{today}.json"
    if not path.exists():
        return {"calls_used": 0, "date": today, "provider": provider}
    try:
        data = json.loads(path.read_text())
        data["date"] = today
        data["provider"] = provider
        return data
    except (json.JSONDecodeError, OSError):
        return {"calls_used": 0, "date": today, "provider": provider}


def increment_daily(provider: str) -> None:
    """Increment daily usage counter."""
    today = datetime.now().strftime("%Y-%m-%d")
    path = _USAGE_DIR / f"daily_{provider}_{today}.json"
    _USAGE_DIR.mkdir(parents=True, exist_ok=True)
    data = {"calls_used": 0, "total_bytes": 0}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    data["calls_used"] = data.get("calls_used", 0) + 1
    try:
        path.write_text(json.dumps(data, default=str))
    except OSError:
        pass


def record_payload_size(provider: str, size_bytes: int) -> None:
    """Record response payload size for token estimation."""
    today = datetime.now().strftime("%Y-%m-%d")
    path = _USAGE_DIR / f"daily_{provider}_{today}.json"
    _USAGE_DIR.mkdir(parents=True, exist_ok=True)
    data = {"calls_used": 0, "total_bytes": 0}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    data["total_bytes"] = data.get("total_bytes", 0) + size_bytes
    try:
        path.write_text(json.dumps(data, default=str))
    except OSError:
        pass
