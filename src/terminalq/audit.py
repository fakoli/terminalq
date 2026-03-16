"""Audit trail for all MCP tool invocations.

Records tool calls, arguments, result summaries, data sources, and timing
for regulatory compliance and usage analysis.
"""

import json
from datetime import datetime

from terminalq.config import CACHE_DIR
from terminalq.logging_config import log

AUDIT_DIR = CACHE_DIR.parent / "audit"


def log_tool_call(
    tool_name: str,
    args: dict,
    result: dict | list | str,
    duration_ms: float,
) -> None:
    """Write an audit log entry for a tool invocation.

    Args:
        tool_name: Name of the MCP tool called.
        args: Arguments passed to the tool.
        result: Result returned by the tool (will be truncated).
        duration_ms: Execution time in milliseconds.
    """
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    # Build a truncated summary of the result
    if isinstance(result, str):
        result_summary = result[:500]
        data_sources = []
        result_size = len(result)
    elif isinstance(result, dict):
        result_summary = json.dumps(result, default=str)[:500]
        data_sources = _extract_sources(result)
        result_size = len(json.dumps(result, default=str))
    elif isinstance(result, list):
        result_summary = json.dumps(result, default=str)[:500]
        data_sources = []
        for item in result:
            if isinstance(item, dict):
                data_sources.extend(_extract_sources(item))
        data_sources = list(set(data_sources))
        result_size = len(json.dumps(result, default=str))
    else:
        result_summary = str(result)[:500]
        data_sources = []
        result_size = len(str(result))

    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "args": _sanitize_args(args),
        "result_summary": result_summary,
        "data_sources": data_sources,
        "duration_ms": round(duration_ms, 1),
        "result_size_bytes": result_size,
    }

    today = datetime.now().strftime("%Y-%m-%d")
    audit_file = AUDIT_DIR / f"audit_{today}.jsonl"

    try:
        with open(audit_file, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except OSError as e:
        log.warning("Failed to write audit log: %s", e)


def get_audit_log(date: str = "") -> list[dict]:
    """Read audit log entries for a given date.

    Args:
        date: Date string in YYYY-MM-DD format. Defaults to today.

    Returns:
        List of audit log entry dicts.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    audit_file = AUDIT_DIR / f"audit_{date}.jsonl"
    if not audit_file.exists():
        return []

    entries = []
    try:
        for line in audit_file.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError as e:
        log.warning("Failed to read audit log for %s: %s", date, e)

    return entries


def get_audit_summary(date: str = "") -> dict:
    """Get a summary of audit log entries for a given date.

    Returns tool call counts, total duration, and top tools.
    """
    entries = get_audit_log(date)
    if not entries:
        return {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "total_calls": 0,
            "tools": {},
        }

    tool_counts: dict[str, int] = {}
    tool_durations: dict[str, float] = {}
    total_bytes = 0

    for entry in entries:
        tool = entry.get("tool", "unknown")
        tool_counts[tool] = tool_counts.get(tool, 0) + 1
        tool_durations[tool] = tool_durations.get(tool, 0) + entry.get("duration_ms", 0)
        total_bytes += entry.get("result_size_bytes", 0)

    # Sort by call count descending
    sorted_tools = sorted(tool_counts.items(), key=lambda x: -x[1])

    return {
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "total_calls": len(entries),
        "total_duration_ms": round(sum(tool_durations.values()), 1),
        "total_payload_bytes": total_bytes,
        "tools": {
            tool: {"calls": count, "total_duration_ms": round(tool_durations.get(tool, 0), 1)}
            for tool, count in sorted_tools
        },
        "first_call": entries[0].get("timestamp") if entries else None,
        "last_call": entries[-1].get("timestamp") if entries else None,
    }


def _extract_sources(d: dict) -> list[str]:
    """Extract data source identifiers from a result dict."""
    sources = []
    if "source" in d:
        sources.append(str(d["source"]))
    if "data_sources" in d:
        sources.extend(d["data_sources"])
    return list(set(sources))


def _sanitize_args(args: dict) -> dict:
    """Remove any sensitive data from args before logging."""
    sanitized = {}
    sensitive_keys = {"api_key", "apikey", "api_secret", "token", "password", "secret", "key", "subscription_token"}
    for k, v in args.items():
        if k.lower() in sensitive_keys:
            sanitized[k] = "***"
        else:
            sanitized[k] = v
    return sanitized
