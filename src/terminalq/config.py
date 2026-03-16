"""Configuration and environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path.home() / ".env", override=True)

# --- API Keys ---
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
POLYGON_API_KEY = os.environ.get("POLYGON_API_KEY", "")

# --- SEC EDGAR ---
SEC_USER_AGENT = os.environ.get("SEC_USER_AGENT", "TerminalQ user@example.com")

# --- Directories ---
# Private data lives in ~/.terminalq/ by default (outside the git repo).
# Override with PORTFOLIO_DIR env var or .mcp.json env block.
_DEFAULT_PORTFOLIO_DIR = Path.home() / ".terminalq"
_FALLBACK_PORTFOLIO_DIR = Path(__file__).parent.parent.parent / "reference"

CACHE_DIR = Path(os.environ.get("CACHE_DIR", Path(__file__).parent.parent.parent / "data" / "cache"))
PORTFOLIO_DIR = Path(
    os.environ.get(
        "PORTFOLIO_DIR",
        _DEFAULT_PORTFOLIO_DIR if _DEFAULT_PORTFOLIO_DIR.exists() else _FALLBACK_PORTFOLIO_DIR,
    )
)

# --- Rate limits (requests per minute) ---
FINNHUB_RATE_LIMIT = 60
FRED_RATE_LIMIT = 120
POLYGON_RATE_LIMIT = 5  # free tier: 5/min
SEC_RATE_LIMIT = 600  # 10/sec = 600/min

# --- Cache TTLs in seconds ---
CACHE_TTL_QUOTES = 60  # 1 minute for live quotes
CACHE_TTL_FUNDAMENTALS = 86400  # 24 hours for company profiles
CACHE_TTL_NEWS = 900  # 15 minutes for news

# Phase 1 additions
CACHE_TTL_HISTORY = 21600  # 6 hours for historical price data
CACHE_TTL_DIVIDENDS = 86400  # 24 hours for dividend data
CACHE_TTL_FINANCIALS = 86400  # 24 hours for financial statements
CACHE_TTL_FILINGS = 3600  # 1 hour for SEC filings
CACHE_TTL_CIK = 604800  # 7 days for CIK lookups (permanent)
CACHE_TTL_ECONOMIC = 3600  # 1 hour for economic indicators
CACHE_TTL_ECONOMIC_INTRADAY = 300  # 5 minutes for intraday rates
CACHE_TTL_EARNINGS = 3600  # 1 hour for earnings data
CACHE_TTL_SCREENER = 86400  # 24 hours for screener component data
CACHE_TTL_SP500_LIST = 604800  # 7 days for S&P 500 component list

# Phase 2 additions
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
COINGECKO_RATE_LIMIT = 30
CACHE_TTL_CRYPTO = 120  # 2 minutes for crypto quotes
CACHE_TTL_SEARCH = 1800  # 30 minutes for web search results
CACHE_TTL_CALENDAR = 3600  # 1 hour for economic calendar
CACHE_TTL_RATINGS = 86400  # 24 hours for analyst ratings
CACHE_TTL_RISK = 21600  # 6 hours for risk metrics
CACHE_TTL_ALLOCATION = 86400  # 24 hours for allocation analysis
