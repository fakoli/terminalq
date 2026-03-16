#!/usr/bin/env bash
# TerminalQ component auto-discovery.
# Lists all skills, commands, agents, hooks, and tests.

set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== TerminalQ Components ==="
echo ""

echo "Skills:"
for skill_dir in "$PLUGIN_ROOT"/skills/*/; do
    if [[ -f "$skill_dir/SKILL.md" ]]; then
        name=$(basename "$skill_dir")
        desc=$(grep -m1 "^description:" "$skill_dir/SKILL.md" | sed 's/^description: //')
        echo "  - $name: $desc"
    fi
done

echo ""
echo "Commands:"
for cmd in "$PLUGIN_ROOT"/commands/*.md; do
    name=$(basename "$cmd" .md)
    desc=$(grep -m1 "^description:" "$cmd" | sed 's/^description: //')
    echo "  - /$name: $desc"
done

echo ""
echo "Hooks:"
if [[ -f "$PLUGIN_ROOT/hooks/hooks.json" ]]; then
    if command -v jq &>/dev/null; then
        jq -r '.hooks[] | "  - \(.event): \(.name) — \(.description)"' "$PLUGIN_ROOT/hooks/hooks.json"
    else
        echo "  (install jq to list hooks)"
    fi
else
    echo "  (none)"
fi

echo ""
echo "Tests:"
TEST_COUNT=$(find "$PLUGIN_ROOT/tests" -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
CONTRACT_COUNT=$(find "$PLUGIN_ROOT/tests/contracts" -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
echo "  - Unit/integration: $((TEST_COUNT - CONTRACT_COUNT)) files"
echo "  - Contract tests: ${CONTRACT_COUNT} files"

echo ""
VERSION=$(grep -o '"version": "[^"]*"' "$PLUGIN_ROOT/.claude-plugin/plugin.json" | cut -d'"' -f4)
echo "Version: $VERSION"
