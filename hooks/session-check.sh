#!/usr/bin/env bash
# TerminalQ SessionStart hook — verify environment
# Checks that required API keys are available and tools are installed.

set -euo pipefail

ERRORS=()
WARNINGS=()

# --- Required keys ---
if [[ -z "${FINNHUB_API_KEY:-}" ]]; then
    ERRORS+=("FINNHUB_API_KEY is not set — quotes, news, earnings, and ratings will fail")
fi

if [[ -z "${FRED_API_KEY:-}" ]]; then
    ERRORS+=("FRED_API_KEY is not set — macro dashboard, yield curve, and economic data will fail")
fi

# --- Optional keys ---
if [[ -z "${POLYGON_API_KEY:-}" ]]; then
    WARNINGS+=("POLYGON_API_KEY not set — Polygon.io fallback unavailable (not required)")
fi

if [[ -z "${BRAVE_API_KEY:-}" ]]; then
    WARNINGS+=("BRAVE_API_KEY not set — web search unavailable (not required)")
fi

# --- Tool checks ---
if ! command -v uv &>/dev/null; then
    WARNINGS+=("uv not found — install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
fi

if ! command -v jq &>/dev/null; then
    WARNINGS+=("jq not found — some hooks may not work. Install with: brew install jq")
fi

# --- Auto-discover components ---
PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_COUNT=$(find "$PLUGIN_ROOT/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
COMMAND_COUNT=$(find "$PLUGIN_ROOT/commands" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
TEST_COUNT=$(find "$PLUGIN_ROOT/tests" -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')

# --- Output ---
echo "TerminalQ v0.5 — session check"
echo "  Components: ${SKILL_COUNT} skills, ${COMMAND_COUNT} commands, ${TEST_COUNT} test files"

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo ""
    echo "  ERRORS:"
    for err in "${ERRORS[@]}"; do
        echo "    ✗ $err"
    done
fi

if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo ""
    echo "  Warnings:"
    for warn in "${WARNINGS[@]}"; do
        echo "    ⚠ $warn"
    done
fi

if [[ ${#ERRORS[@]} -eq 0 ]]; then
    echo "  Status: ready"
else
    echo ""
    echo "  Status: degraded — run /setup for guided API key configuration"
fi
