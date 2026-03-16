#!/usr/bin/env bash
# TerminalQ Stop hook — quality gate for financial analysis outputs.
#
# When a financial skill was invoked, checks that the assistant's last
# response includes a disclaimer and data freshness note.
#
# Reads the assistant's last message from stdin (Claude Code passes it).

set -euo pipefail

# Read the assistant's last output from stdin
OUTPUT=$(cat)

# Only enforce when the output looks like a skill invocation (has structured sections)
# Check for telltale section headers from output contracts
SKILL_MARKERS=(
    "Market Mood"
    "Index Snapshot"
    "Company Overview"
    "Financial Health"
    "Portfolio Scorecard"
    "Risk Assessment"
    "Business Cycle"
    "Investment Thesis"
    "Earnings Calendar"
    "Decision Summary"
)

IS_SKILL_OUTPUT=false
for marker in "${SKILL_MARKERS[@]}"; do
    if echo "$OUTPUT" | grep -qi "$marker"; then
        IS_SKILL_OUTPUT=true
        break
    fi
done

# If this doesn't look like a skill output, skip checks
if [[ "$IS_SKILL_OUTPUT" = false ]]; then
    exit 0
fi

MISSING=()

# Check for disclaimer
if ! echo "$OUTPUT" | grep -qi "not financial advice\|informational.*purposes\|educational.*purposes\|do your own due diligence"; then
    MISSING+=("disclaimer (must include 'not financial advice' or equivalent)")
fi

# Check for data freshness section
if ! echo "$OUTPUT" | grep -qi "data freshness\|data age\|data sources"; then
    MISSING+=("Data Freshness section (see docs/output-contracts.md)")
fi

if [[ ${#MISSING[@]} -gt 0 ]]; then
    echo ""
    echo "⚠ TerminalQ quality gate — missing required elements:"
    for item in "${MISSING[@]}"; do
        echo "  • $item"
    done
    echo ""
    echo "All financial analysis outputs must include a disclaimer and data freshness notes."
    echo "See: docs/output-contracts.md"
fi
