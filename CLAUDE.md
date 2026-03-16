# TerminalQ

Bloomberg-style financial terminal for portfolio intelligence, built as a Claude Code MCP plugin.

## Quick Start

```bash
./setup.sh          # Install dependencies + get API key instructions
uv run python -m terminalq  # Start MCP server
```

## Architecture

- **MCP Server**: `src/terminalq/server.py` -- 16 FastMCP tools, JSON over stdio
- **Providers** (`src/terminalq/providers/`):
  - `finnhub.py` -- Quotes, company profiles, news, earnings (Finnhub API, 60 req/min)
  - `historical.py` -- Historical OHLCV prices, dividends (Yahoo Finance via yfinance)
  - `edgar.py` -- Financial statements, SEC filings (SEC EDGAR XBRL, 10 req/sec)
  - `fred.py` -- Economic indicators, macro dashboard (FRED API, 120 req/min)
  - `technical.py` -- SMA, EMA, RSI, MACD, Bollinger, ATR (computed from historical data)
  - `screener.py` -- S&P 500 stock screener (cached component list + Finnhub profiles)
  - `portfolio.py` -- Portfolio holdings parser (from `reference/` markdown files)
- **Infrastructure**:
  - `cache.py` -- File-based cache with configurable TTLs (`data/cache/`)
  - `rate_limiter.py` -- Token bucket rate limiter for API providers
  - `logging_config.py` -- Structured logging to stderr
  - `config.py` -- All env vars, TTLs, rate limits; loads `~/.env` via python-dotenv
- **Reference Data**: `reference/` -- `portfolio-holdings.md`, `rsu-schedule.md`, `accounts.md`
- **Commands**: `commands/` -- 12 slash commands (see below)
- **Docs**: `docs/` -- `api-reference.md`, `providers.md`, `commands.md`, `configuration.md`

## API Keys

| Key | Required | Free Tier | Env Variable |
|-----|----------|-----------|-------------|
| Finnhub | Yes | 60 calls/min | `FINNHUB_API_KEY` |
| FRED | Yes | 120 calls/min | `FRED_API_KEY` |
| SEC EDGAR | No key | Uses User-Agent header | `SEC_USER_AGENT` |
| Yahoo Finance | No key | Via yfinance library | -- |

Keys are loaded from `~/.env` (python-dotenv with `override=True`).

## MCP Tools (16)

**Quotes & Market Data:**
- `terminalq_get_quote(symbol)` -- Real-time quote (Finnhub, 1 min cache)
- `terminalq_get_quotes_batch(symbols)` -- Parallel batch quotes (Finnhub, 1 min cache)
- `terminalq_get_historical(symbol, period, interval)` -- OHLCV data (Yahoo Finance, 6 hr cache)
- `terminalq_get_dividends(symbol, years)` -- Dividend history + yield (Yahoo Finance, 24 hr cache)

**Portfolio:**
- `terminalq_get_portfolio()` -- Static holdings from `reference/portfolio-holdings.md`
- `terminalq_get_portfolio_live()` -- Holdings with live Finnhub prices + daily P&L
- `terminalq_get_rsu_schedule()` -- Pinterest RSU vesting from `reference/rsu-schedule.md`

**Research & Fundamentals:**
- `terminalq_get_company_profile(symbol)` -- Company overview (Finnhub, 24 hr cache)
- `terminalq_get_news(symbol, days)` -- Company news, up to 20 articles (Finnhub, 15 min cache)
- `terminalq_get_earnings(symbol)` -- EPS history, 8 quarters (Finnhub, 1 hr cache)
- `terminalq_get_financials(symbol, statement, periods)` -- Income/balance/cash flow from 10-K filings (SEC EDGAR, 24 hr cache)
- `terminalq_get_filings(symbol, filing_type, limit)` -- SEC filing search (EDGAR, 1 hr cache)
- `terminalq_get_technicals(symbol)` -- SMA/EMA/RSI/MACD/Bollinger/ATR (computed, 6 hr cache)

**Economics & Screening:**
- `terminalq_get_economic_indicator(indicator, limit)` -- FRED data; supports aliases: gdp, cpi, core_cpi, ppi, unemployment, fed_funds, 10y_yield, 2y_yield, 30y_yield, yield_spread, initial_claims, nonfarm_payrolls, pce, housing_starts, consumer_sentiment (1 hr cache; 5 min for intraday series)
- `terminalq_get_macro_dashboard()` -- 11 key indicators in parallel (FRED, 1 hr cache)
- `terminalq_screen_stocks(sector, min_market_cap, max_market_cap, limit)` -- S&P 500 screener by sector/market cap (7 day list cache)

## Slash Commands (12)

| Command | Description |
|---------|-------------|
| `/quote SYMBOL` | Real-time quote with portfolio context |
| `/portfolio` | All holdings with live prices, grouped by account |
| `/news [SYMBOL]` | News for a ticker or top 5 portfolio holdings |
| `/rsu` | Pinterest RSU vesting schedule + current PINS price |
| `/dividends SYMBOL` | Dividend history, yield, projected income |
| `/earnings SYMBOL` | Earnings history, beat rate, EPS trend |
| `/historical SYMBOL [PERIOD]` | Historical price data with performance summary |
| `/financials SYMBOL [STATEMENT]` | SEC financial statements (income/balance/cash flow) |
| `/filings SYMBOL [TYPE]` | SEC filing search (10-K, 10-Q, 8-K, etc.) |
| `/technicals SYMBOL` | Technical analysis report with overall signal |
| `/economy [INDICATOR]` | Single indicator or full macro dashboard |
| `/screen [CRITERIA]` | S&P 500 stock screener by sector/cap |

## Key File Paths

```
src/terminalq/
  server.py           # MCP tool definitions (16 tools)
  config.py           # Env vars, TTLs, rate limits
  cache.py            # File-based cache
  rate_limiter.py     # Token bucket rate limiter
  providers/          # Data source adapters (7 providers)
commands/             # Slash command definitions (12 commands)
reference/            # Portfolio holdings, RSU schedule
data/cache/           # Cache files (auto-created, gitignored)
docs/                 # Detailed documentation
tests/                # pytest test suite
setup.sh              # Setup script
pyproject.toml        # Dependencies and build config
```

## Portfolio Data

Holdings are maintained in `reference/portfolio-holdings.md`. Update this file when new brokerage statements arrive. The portfolio provider parses the markdown tables (with `## Account` headers) into structured data. See `reference/portfolio-holdings.example.md` for the expected format.

## Error Convention

All tools return errors as `{"error": "message", "symbol": "SYM", "source": "provider_name"}`. Providers never raise exceptions -- they catch and return error dicts.
