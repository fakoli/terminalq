#!/bin/bash
# TerminalQ Setup Script

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$HOME/.terminalq"

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

# Set up private data directory
echo "2. Setting up private data directory: $DATA_DIR"
mkdir -p "$DATA_DIR"

# Copy example files if real files don't exist yet
for example in "$SCRIPT_DIR"/reference/*.example.md; do
    base=$(basename "$example" .example.md)
    target="$DATA_DIR/$base.md"
    if [ ! -f "$target" ]; then
        cp "$example" "$target"
        echo "   Created $target (from template — edit with your data)"
    else
        echo "   $target already exists (skipped)"
    fi
done
echo ""

# Check for API keys
echo "3. API Keys (stored in ~/.env)"
if [ -z "$FINNHUB_API_KEY" ] && ! grep -q FINNHUB_API_KEY ~/.env 2>/dev/null; then
    echo "   FINNHUB_API_KEY: NOT SET"
    echo "     Sign up free at: https://finnhub.io/register"
else
    echo "   FINNHUB_API_KEY: found"
fi

if [ -z "$FRED_API_KEY" ] && ! grep -q FRED_API_KEY ~/.env 2>/dev/null; then
    echo "   FRED_API_KEY: NOT SET"
    echo "     Sign up free at: https://fred.stlouisfed.org/docs/api/api_key.html"
else
    echo "   FRED_API_KEY: found"
fi

echo ""
echo "   Add keys to ~/.env:"
echo "     FINNHUB_API_KEY=\"your_key\""
echo "     FRED_API_KEY=\"your_key\""
echo ""

echo "4. Next steps:"
echo "   - Edit your data:     $DATA_DIR/portfolio-holdings.md"
echo "   - Or use ingestion:   /ingest holdings"
echo "   - Test the server:    uv run python -m terminalq"
echo "   - Install as plugin:  claude plugin install ."
echo ""
echo "=== Setup Complete ==="
