# TerminalQ Configuration

All configuration lives in `src/terminalq/config.py`. Environment variables are loaded from `~/.env` via python-dotenv.

---

## Environment Variables

### API Keys

| Variable | Required | Description | Where to Get |
|----------|----------|-------------|-------------|
| `FINNHUB_API_KEY` | Yes | Finnhub API key (free tier, 60 calls/min) | [finnhub.io/register](https://finnhub.io/register) |
| `FRED_API_KEY` | Yes | FRED API key (free, 120 calls/min) | [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html) |
| `BRAVE_API_KEY` | No | Brave Search API key (reserved for Phase 2) | [brave.com/search/api](https://brave.com/search/api/) |

### SEC EDGAR

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SEC_USER_AGENT` | No | `"TerminalQ user@example.com"` | User-Agent header for SEC requests (SEC requires identification) |

### Directories

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CACHE_DIR` | No | `<project_root>/data/cache` | Directory for file-based cache |
| `PORTFOLIO_DIR` | No | `<project_root>/reference` | Directory containing portfolio reference files |

---

## How dotenv Works

The config module loads environment variables at import time:

```python
from dotenv import load_dotenv
load_dotenv(Path.home() / ".env", override=True)
```

This reads `~/.env` and sets any variables found there into `os.environ`. The `override=True` flag means `.env` values take precedence over existing environment variables.

You can set API keys in any of these places (checked in order):
1. `~/.env` file (recommended -- loaded by python-dotenv with override)
2. Shell environment (`export FINNHUB_API_KEY=...` in `~/.zshrc`)
3. Claude Code MCP plugin env block (in `.mcp.json`)

---

## Rate Limits

| Provider | Rate Limit | Implementation |
|----------|-----------|----------------|
| Finnhub | 60 requests/min | Token bucket `RateLimiter` |
| FRED | 120 requests/min | No explicit limiter (low call volume from dashboard) |
| SEC EDGAR | 10 requests/sec (600/min) | Lock-based 0.1s minimum between requests |
| Yahoo Finance | None enforced | Handled by yfinance library |
| S&P 500 CSV | None | Fetched once, cached 7 days |

---

## Cache TTLs

All TTL constants are defined in `config.py` as seconds:

| Constant | Value | Human-Readable | Used By |
|----------|-------|----------------|---------|
| `CACHE_TTL_QUOTES` | 60 | 1 minute | Finnhub quotes |
| `CACHE_TTL_FUNDAMENTALS` | 86400 | 24 hours | Company profiles |
| `CACHE_TTL_NEWS` | 900 | 15 minutes | Company news |
| `CACHE_TTL_EARNINGS` | 3600 | 1 hour | Earnings data |
| `CACHE_TTL_HISTORY` | 21600 | 6 hours | Historical prices, technicals |
| `CACHE_TTL_DIVIDENDS` | 86400 | 24 hours | Dividend data |
| `CACHE_TTL_FINANCIALS` | 86400 | 24 hours | SEC financial statements |
| `CACHE_TTL_FILINGS` | 3600 | 1 hour | SEC filings list |
| `CACHE_TTL_CIK` | 604800 | 7 days | CIK ticker-to-ID lookups |
| `CACHE_TTL_ECONOMIC` | 3600 | 1 hour | FRED economic indicators |
| `CACHE_TTL_ECONOMIC_INTRADAY` | 300 | 5 minutes | Intraday rates (yields, fed funds) |
| `CACHE_TTL_SCREENER` | 86400 | 24 hours | Screener data |
| `CACHE_TTL_SP500_LIST` | 604800 | 7 days | S&P 500 component list |

### Phase 2 TTLs (reserved, not yet in use)

| Constant | Value | Human-Readable | Planned Use |
|----------|-------|----------------|-------------|
| `CACHE_TTL_CRYPTO` | 120 | 2 minutes | Crypto quotes |
| `CACHE_TTL_SEARCH` | 1800 | 30 minutes | Web search results |
| `CACHE_TTL_CALENDAR` | 3600 | 1 hour | Economic calendar |
| `CACHE_TTL_RATINGS` | 86400 | 24 hours | Analyst ratings |
| `CACHE_TTL_RISK` | 21600 | 6 hours | Risk metrics |
| `CACHE_TTL_ALLOCATION` | 86400 | 24 hours | Allocation analysis |

---

## Cache Mechanics

The cache is file-based, stored in `data/cache/`. Each cache entry is a JSON file:

```json
{
  "value": { ... },
  "cached_at": 1710500000.0,
  "expires_at": 1710500060.0
}
```

- **Key sanitization**: `/` and `:` in cache keys are replaced with `_`
- **Expiry**: Checked on read; expired files are deleted automatically
- **Corruption**: Malformed JSON files are deleted on read
- **Directory**: Created automatically on first write

To clear the cache manually:

```bash
rm -rf ~/terminalq/data/cache/*.json
```

---

## Reference Files

Portfolio and RSU data are stored as markdown in `reference/`:

| File | Description | Format |
|------|-------------|--------|
| `portfolio-holdings.md` | All brokerage holdings | Markdown tables with `## Account` headers |
| `rsu-schedule.md` | RSU vesting schedule | Markdown table with date, grant, percentage, value |
| `accounts.md` | Account metadata | Reference info |

Update `portfolio-holdings.md` when new brokerage statements arrive. The portfolio provider parses the markdown tables directly.

---

## Dependencies

From `pyproject.toml`:

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp[cli]` | >=1.0.0 | MCP server framework (FastMCP) |
| `httpx` | >=0.27.0 | Async HTTP client for API calls |
| `python-dotenv` | >=1.0.0 | Environment variable loading from .env |
| `yfinance` | >=0.2.0 | Yahoo Finance data (historical prices, dividends) |

Dev dependencies: `pytest>=8.0`, `pytest-asyncio>=0.23.0`

Python requirement: `>=3.11`

Build system: Hatchling
