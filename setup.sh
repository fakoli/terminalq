#!/bin/bash
# TerminalQ Setup Script

set -e

echo "=== TerminalQ Setup ==="
echo ""

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "1. Installing Python dependencies..."
uv sync
echo "   Done."
echo ""

# Check for API key
if [ -z "$FINNHUB_API_KEY" ] && [ ! -f .env ]; then
    echo "2. Finnhub API Key Required"
    echo "   Sign up for a FREE API key at: https://finnhub.io/register"
    echo "   (60 API calls/minute — more than enough for personal use)"
    echo ""
    echo "   After signing up, set your key:"
    echo "   Option A: Create a .env file:"
    echo "     echo 'FINNHUB_API_KEY=your_key_here' > .env"
    echo ""
    echo "   Option B: Set in your .mcp.json env block"
    echo ""
    echo "   Option C: Export in your shell:"
    echo "     export FINNHUB_API_KEY=your_key_here"
    echo ""
else
    echo "2. Finnhub API key found."
fi

echo ""
echo "3. To test the MCP server:"
echo "   uv run python -m terminalq"
echo ""
echo "4. To install as a Claude Code plugin:"
echo "   claude plugin install ."
echo ""
echo "=== Setup Complete ==="
