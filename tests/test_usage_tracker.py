"""Tests for terminalq.usage_tracker — monthly and daily usage tracking."""

import pytest

from terminalq import usage_tracker


@pytest.fixture(autouse=True)
def tmp_usage_dir(tmp_path, monkeypatch):
    """Use a temporary directory for usage data."""
    monkeypatch.setattr("terminalq.usage_tracker._USAGE_DIR", tmp_path)
    return tmp_path


def test_initial_usage():
    """Fresh provider has zero calls."""
    usage = usage_tracker.get_monthly_usage("test_provider")
    assert usage["calls_used"] == 0
    assert usage["remaining"] == "unlimited"


def test_increment_usage():
    """Incrementing increases the call count."""
    usage_tracker.increment_usage("test_provider")
    usage_tracker.increment_usage("test_provider")
    usage = usage_tracker.get_monthly_usage("test_provider")
    assert usage["calls_used"] == 2


def test_check_budget_under():
    """Under budget returns True."""
    assert usage_tracker.check_budget("test_provider", 100) is True


def test_check_budget_over():
    """Over budget returns False."""
    for _ in range(5):
        usage_tracker.increment_usage("limited_provider")
    assert usage_tracker.check_budget("limited_provider", 5) is False


def test_monthly_limit_display():
    """Monthly usage shows remaining correctly."""
    usage_tracker.increment_usage("brave")
    usage_tracker.increment_usage("brave")
    usage = usage_tracker.get_monthly_usage("brave", 2000)
    assert usage["calls_used"] == 2
    assert usage["calls_limit"] == 2000
    assert usage["remaining"] == 1998


async def test_daily_usage():
    """Daily usage tracking works."""
    await usage_tracker.increment_daily("test_daily")
    await usage_tracker.increment_daily("test_daily")
    daily = usage_tracker.get_daily_usage("test_daily")
    assert daily["calls_used"] == 2


async def test_payload_recording():
    """Payload size recording accumulates."""
    await usage_tracker.record_payload_size("test_payload", 1000)
    await usage_tracker.record_payload_size("test_payload", 2000)
    daily = usage_tracker.get_daily_usage("test_payload")
    assert daily.get("total_bytes", 0) == 3000


async def test_increment_and_check_within_budget():
    """Atomic increment_and_check returns True when within budget."""
    within, usage = await usage_tracker.increment_and_check("atomic_test", 100)
    assert within is True
    assert usage["calls_used"] == 1
    assert usage["remaining"] == 99


async def test_increment_and_check_over_budget():
    """Atomic increment_and_check returns False when over budget."""
    for _ in range(5):
        usage_tracker.increment_usage("atomic_over")
    within, usage = await usage_tracker.increment_and_check("atomic_over", 5)
    assert within is False
    assert usage["calls_used"] == 6
    assert usage["remaining"] == 0


# ---------------------------------------------------------------------------
# Coverage gap: JSONDecodeError in _read_usage (lines 26-27)
# ---------------------------------------------------------------------------


def test_read_usage_json_decode_error(tmp_usage_dir):
    """Corrupt usage file returns default data."""
    from datetime import datetime

    month = datetime.now().strftime("%Y-%m")
    path = tmp_usage_dir / f"usage_corrupt_{month}.json"
    path.write_text("NOT VALID JSON {{{")

    usage = usage_tracker.get_monthly_usage("corrupt")
    assert usage["calls_used"] == 0


# ---------------------------------------------------------------------------
# Coverage gap: OSError in _write_usage (lines 35-36)
# ---------------------------------------------------------------------------


def test_write_usage_oserror(tmp_usage_dir, monkeypatch):
    """OSError during write is caught, not raised."""
    from pathlib import Path
    from unittest.mock import patch

    def _fail_write_text(self, *args, **kwargs):
        raise OSError("read-only filesystem")

    with patch.object(Path, "write_text", _fail_write_text):
        # Should not raise
        usage_tracker.increment_usage("fail_provider")

    # Data was not persisted, so reading gives defaults
    usage = usage_tracker.get_monthly_usage("fail_provider")
    assert usage["calls_used"] == 0


# ---------------------------------------------------------------------------
# Coverage gap: daily read errors (lines 98, 104-105)
# ---------------------------------------------------------------------------


def test_get_daily_usage_no_file():
    """Daily usage for unseen provider returns zeros."""
    daily = usage_tracker.get_daily_usage("nonexistent_provider")
    assert daily["calls_used"] == 0
    assert "date" in daily
    assert daily["provider"] == "nonexistent_provider"


def test_get_daily_usage_corrupt_file(tmp_usage_dir):
    """Corrupt daily file returns defaults."""
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    path = tmp_usage_dir / f"daily_corrupt_daily_{today}.json"
    path.write_text("{broken json")

    daily = usage_tracker.get_daily_usage("corrupt_daily")
    assert daily["calls_used"] == 0
    assert daily["provider"] == "corrupt_daily"


# ---------------------------------------------------------------------------
# Coverage gap: increment_daily errors (lines 117-118, 122-123)
# ---------------------------------------------------------------------------


async def test_increment_daily_corrupt_existing(tmp_usage_dir):
    """increment_daily handles corrupt existing file gracefully."""
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    path = tmp_usage_dir / f"daily_corrupt_inc_{today}.json"
    path.write_text("<<<invalid>>>")

    # Should not raise, resets to default and increments
    await usage_tracker.increment_daily("corrupt_inc")

    daily = usage_tracker.get_daily_usage("corrupt_inc")
    assert daily["calls_used"] == 1


async def test_increment_daily_write_oserror(tmp_usage_dir, monkeypatch):
    """OSError during increment_daily write is silently caught."""
    from pathlib import Path
    from unittest.mock import patch

    # First, do a successful increment so the file exists
    await usage_tracker.increment_daily("write_fail")

    original_write = Path.write_text

    def _fail_write(self, *args, **kwargs):
        if "daily_write_fail_" in str(self):
            raise OSError("disk full")
        return original_write(self, *args, **kwargs)

    with patch.object(Path, "write_text", _fail_write):
        # Should not raise
        await usage_tracker.increment_daily("write_fail")


# ---------------------------------------------------------------------------
# Coverage gap: record_payload errors (lines 135-136, 140-141)
# ---------------------------------------------------------------------------


async def test_record_payload_corrupt_existing(tmp_usage_dir):
    """record_payload_size handles corrupt existing file gracefully."""
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    path = tmp_usage_dir / f"daily_payload_corrupt_{today}.json"
    path.write_text("not json")

    await usage_tracker.record_payload_size("payload_corrupt", 500)

    daily = usage_tracker.get_daily_usage("payload_corrupt")
    assert daily.get("total_bytes", 0) == 500


async def test_record_payload_write_oserror(tmp_usage_dir, monkeypatch):
    """OSError during record_payload_size write is silently caught."""
    from pathlib import Path
    from unittest.mock import patch

    original_write = Path.write_text

    def _fail_write(self, *args, **kwargs):
        if "daily_payload_wfail_" in str(self):
            raise OSError("disk full")
        return original_write(self, *args, **kwargs)

    with patch.object(Path, "write_text", _fail_write):
        # Should not raise
        await usage_tracker.record_payload_size("payload_wfail", 1000)
