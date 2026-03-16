"""Tests for terminalq.audit — audit trail logging."""

import pytest

from terminalq import audit


@pytest.fixture(autouse=True)
def tmp_audit_dir(tmp_path, monkeypatch):
    """Use a temporary directory for audit logs."""
    monkeypatch.setattr("terminalq.audit.AUDIT_DIR", tmp_path)
    return tmp_path


def test_log_and_read():
    """A logged tool call can be read back."""
    audit.log_tool_call(
        "terminalq_get_quote",
        {"symbol": "AAPL"},
        {"current_price": 185.50, "source": "finnhub"},
        42.5,
    )

    entries = audit.get_audit_log()
    assert len(entries) == 1
    assert entries[0]["tool"] == "terminalq_get_quote"
    assert entries[0]["args"] == {"symbol": "AAPL"}
    assert entries[0]["duration_ms"] == 42.5
    assert "finnhub" in entries[0]["data_sources"]


def test_multiple_entries():
    """Multiple tool calls are appended to the same log file."""
    audit.log_tool_call("tool_a", {}, {"source": "a"}, 10.0)
    audit.log_tool_call("tool_b", {}, {"source": "b"}, 20.0)
    audit.log_tool_call("tool_a", {}, {"source": "a"}, 15.0)

    entries = audit.get_audit_log()
    assert len(entries) == 3


def test_summary():
    """Summary aggregates call counts and durations."""
    audit.log_tool_call("tool_a", {}, {}, 10.0)
    audit.log_tool_call("tool_b", {}, {}, 20.0)
    audit.log_tool_call("tool_a", {}, {}, 15.0)

    summary = audit.get_audit_summary()
    assert summary["total_calls"] == 3
    assert summary["tools"]["tool_a"]["calls"] == 2
    assert summary["tools"]["tool_b"]["calls"] == 1


def test_empty_log():
    """Reading a non-existent date returns empty list."""
    entries = audit.get_audit_log("2020-01-01")
    assert entries == []


def test_sanitize_args():
    """Sensitive args are redacted."""
    audit.log_tool_call("test_tool", {"symbol": "AAPL", "api_key": "secret123"}, {}, 5.0)
    entries = audit.get_audit_log()
    assert entries[0]["args"]["api_key"] == "***"
    assert entries[0]["args"]["symbol"] == "AAPL"


def test_result_truncation():
    """Large results are truncated in the summary."""
    big_result = {"data": "x" * 1000, "source": "test"}
    audit.log_tool_call("test_tool", {}, big_result, 5.0)
    entries = audit.get_audit_log()
    assert len(entries[0]["result_summary"]) <= 500


# ---------------------------------------------------------------------------
# Coverage gap: list result branch (lines 42-48)
# ---------------------------------------------------------------------------


def test_log_tool_call_list_result():
    """A list result extracts data_sources from contained dicts."""
    result = [
        {"value": 1, "source": "src_a"},
        {"value": 2, "source": "src_b"},
    ]
    audit.log_tool_call("list_tool", {}, result, 10.0)
    entries = audit.get_audit_log()
    assert len(entries) == 1
    assert set(entries[0]["data_sources"]) == {"src_a", "src_b"}


def test_log_tool_call_list_result_deduplicates_sources():
    """Duplicate sources within list items are deduplicated."""
    result = [
        {"source": "same"},
        {"source": "same"},
    ]
    audit.log_tool_call("dedup_tool", {}, result, 5.0)
    entries = audit.get_audit_log()
    assert entries[0]["data_sources"] == ["same"]


def test_log_tool_call_list_non_dict_items():
    """List items that are not dicts don't produce sources."""
    result = ["hello", 123, None]
    audit.log_tool_call("mixed_list", {}, result, 3.0)
    entries = audit.get_audit_log()
    assert entries[0]["data_sources"] == []


# ---------------------------------------------------------------------------
# Coverage gap: else branch for non-dict/list/str (lines 49-52)
# ---------------------------------------------------------------------------


def test_log_tool_call_non_standard_result():
    """Non-dict/list/str result types are coerced to str."""
    audit.log_tool_call("int_tool", {}, 42, 1.0)
    entries = audit.get_audit_log()
    assert entries[0]["result_summary"] == "42"
    assert entries[0]["result_size_bytes"] == 2  # len("42")
    assert entries[0]["data_sources"] == []


def test_log_tool_call_float_result():
    """Float result handled by the else branch."""
    audit.log_tool_call("float_tool", {}, 3.14, 1.0)
    entries = audit.get_audit_log()
    assert entries[0]["result_summary"] == "3.14"


# ---------------------------------------------------------------------------
# Coverage gap: OSError writing audit log (lines 70-71)
# ---------------------------------------------------------------------------


def test_log_tool_call_oserror_write(tmp_path, monkeypatch):
    """OSError during write is caught and logged, not raised."""
    import builtins
    from unittest.mock import patch

    monkeypatch.setattr("terminalq.audit.AUDIT_DIR", tmp_path)

    original_open = builtins.open

    def _fail_open(path, *args, **kwargs):
        if "audit_" in str(path):
            raise OSError("disk full")
        return original_open(path, *args, **kwargs)

    with patch("builtins.open", side_effect=_fail_open):
        # Should not raise
        audit.log_tool_call("fail_tool", {}, "ok", 1.0)

    # No entries written
    entries = audit.get_audit_log()
    assert entries == []


# ---------------------------------------------------------------------------
# Coverage gap: OSError reading audit log (lines 97-100)
# ---------------------------------------------------------------------------


def test_get_audit_log_oserror_read(tmp_path, monkeypatch):
    """OSError during read is caught and returns empty list."""
    from unittest.mock import patch

    monkeypatch.setattr("terminalq.audit.AUDIT_DIR", tmp_path)
    # Write a valid entry first
    audit.log_tool_call("tool", {}, "result", 1.0)

    # Now make reading fail
    with patch.object(type(next(tmp_path.iterdir())), "read_text", side_effect=OSError("permission denied")):
        entries = audit.get_audit_log()
    assert entries == []


# ---------------------------------------------------------------------------
# Coverage gap: empty entries summary (line 112)
# ---------------------------------------------------------------------------


def test_get_audit_summary_empty():
    """Summary for a date with no entries returns zero totals."""
    summary = audit.get_audit_summary("1999-01-01")
    assert summary["total_calls"] == 0
    assert summary["tools"] == {}
    assert summary["date"] == "1999-01-01"


# ---------------------------------------------------------------------------
# Coverage gap: data_sources from list items (line 151)
# ---------------------------------------------------------------------------


def test_extract_sources_with_data_sources_key():
    """_extract_sources picks up 'data_sources' list from result dict."""
    result = {"data_sources": ["yahoo", "polygon"], "source": "merged"}
    audit.log_tool_call("merged_tool", {}, result, 1.0)
    entries = audit.get_audit_log()
    sources = set(entries[0]["data_sources"])
    assert "yahoo" in sources
    assert "polygon" in sources
    assert "merged" in sources


def test_string_result():
    """String result produces correct summary and empty data_sources."""
    audit.log_tool_call("str_tool", {}, "simple string result", 1.0)
    entries = audit.get_audit_log()
    assert entries[0]["result_summary"] == "simple string result"
    assert entries[0]["data_sources"] == []
    assert entries[0]["result_size_bytes"] == len("simple string result")
