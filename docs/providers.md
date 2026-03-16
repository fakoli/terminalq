# TerminalQ Providers Guide

Providers are data source adapters in `src/terminalq/providers/`. Each provider encapsulates API access, caching, rate limiting, and data transformation for a specific data source.

## Existing Providers

| File | Data Source | API Key Required | Rate Limit |
|------|-----------|-----------------|------------|
| `finnhub.py` | Finnhub API | Yes (`FINNHUB_API_KEY`) | 60/min |
| `historical.py` | Yahoo Finance (yfinance) | No | None (library-managed) |
| `edgar.py` | SEC EDGAR XBRL | No (uses User-Agent) | 10/sec (600/min) |
| `fred.py` | FRED API | Yes (`FRED_API_KEY`) | 120/min |
| `technical.py` | Computed from historical data | No | N/A |
| `screener.py` | Datahub CSV + Finnhub | Inherits Finnhub | Inherits Finnhub |
| `portfolio.py` | Local markdown files | No | N/A |

---

## How to Add a New Provider

### Step 1: Create the provider file

Create `src/terminalq/providers/your_provider.py`:

```python
"""YourSource data provider -- description of what it provides."""
import asyncio
import httpx

from terminalq import cache
from terminalq.config import YOUR_API_KEY, CACHE_TTL_YOUR_DATA
from terminalq.logging_config import log
from terminalq.rate_limiter import RateLimiter

BASE_URL = "https://api.yoursource.com/v1"
_rate_limiter = RateLimiter(calls_per_minute=60)


async def get_data(symbol: str) -> dict:
    """Get data for a symbol from YourSource."""
    # 1. Check cache
    cache_key = f"yoursource_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    # 2. Fetch from API (with rate limiting)
    await _rate_limiter.acquire()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/endpoint",
                params={"symbol": symbol, "apikey": YOUR_API_KEY},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        log.warning("YourSource timeout for %s", symbol)
        return {"error": "Request timed out", "symbol": symbol, "source": "yoursource"}
    except httpx.HTTPStatusError as e:
        log.warning("YourSource HTTP %d for %s", e.response.status_code, symbol)
        return {"error": f"HTTP {e.response.status_code}", "symbol": symbol, "source": "yoursource"}
    except httpx.ConnectError:
        log.error("YourSource connection failed for %s", symbol)
        return {"error": "Connection failed", "symbol": symbol, "source": "yoursource"}

    # 3. Transform raw API response into clean structure
    result = {
        "symbol": symbol,
        "metric": data.get("raw_field"),
        "source": "yoursource",
    }

    # 4. Cache and return
    cache.set(cache_key, result, CACHE_TTL_YOUR_DATA)
    return result
```

### Step 2: Add configuration to `config.py`

```python
# --- API Keys ---
YOUR_API_KEY = os.environ.get("YOUR_API_KEY", "")

# --- Rate limits ---
YOUR_RATE_LIMIT = 60  # requests per minute

# --- Cache TTLs ---
CACHE_TTL_YOUR_DATA = 3600  # 1 hour
```

### Step 3: Register the tool in `server.py`

```python
from terminalq.providers import your_provider

@mcp.tool()
async def terminalq_get_your_data(symbol: str) -> str:
    """Description shown to Claude when deciding which tool to use.

    Args:
        symbol: Ticker symbol (e.g., AAPL, PINS)
    """
    result = await your_provider.get_data(symbol.upper())
    return json.dumps(result, indent=2)
```

### Step 4 (optional): Create a slash command

Create `commands/your_data.md`:

```markdown
---
name: your_data
description: Get your data for a symbol
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, PINS)
    required: true
---

Use the `terminalq_get_your_data` MCP tool to get data for "$ARGUMENTS".

Present the results showing:
- Key metric 1
- Key metric 2
- Context and interpretation
```

---

## Provider Patterns

### Caching Pattern

Every provider follows the same cache-first pattern:

1. Build a unique cache key (e.g., `provider_function_symbol_params`)
2. Check `cache.get(key)` -- return immediately on hit
3. Fetch from external source on miss
4. Transform the response
5. Call `cache.set(key, result, TTL)` before returning

The cache is file-based (JSON files in `data/cache/`). See `src/terminalq/cache.py`.

### Rate Limiting Pattern

For API-based providers, use the `RateLimiter` class:

```python
from terminalq.rate_limiter import RateLimiter

_rate_limiter = RateLimiter(calls_per_minute=60)

async def fetch_something():
    await _rate_limiter.acquire()  # blocks until a token is available
    # ... make API call
```

The rate limiter uses a token bucket algorithm. It allows bursting up to the full bucket size, then throttles to the configured rate.

SEC EDGAR uses a simpler lock-based approach (0.1s minimum between requests) to comply with their 10 req/sec fair-use policy.

### Error Format

All providers return errors in a consistent structure:

```python
{"error": "Human-readable message", "symbol": symbol, "source": "provider_name"}
```

Never raise exceptions from provider functions. Catch all exceptions and return error dicts so the MCP tool can serialize them as JSON for Claude.

### Async Pattern

All provider functions that do I/O must be `async`. For libraries that are synchronous (like yfinance), wrap blocking calls with `asyncio.to_thread`:

```python
df = await asyncio.to_thread(ticker.history, period="1y", interval="1d")
```

### Batch Fetching Pattern

For batch operations (like `get_quotes_batch`):

1. Check cache for each item
2. Collect uncached items
3. Fetch uncached items in parallel with `asyncio.gather`
4. Cache each result individually
5. Return combined results in the original order
