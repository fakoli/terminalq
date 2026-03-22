# TerminalQ

Bloomberg-style financial terminal for portfolio intelligence, built as a Claude Code MCP plugin.

## Quick Start

```bash
./setup.sh                  # Install deps, create ~/.terminalq/, check API keys
/tq-setup                   # Interactive onboarding — obtain and configure API keys
```

**First time?** Run `./setup.sh` first to install dependencies, then run `/tq-setup` inside Claude Code for guided API key configuration.

## Private Data Storage

**Your personal financial data is stored in `~/.terminalq/` — outside the git repo and never committed.**

```
~/.terminalq/                          <-- YOUR private data (gitignored, local only)
  portfolio-holdings.md                   Portfolio positions by account
  rsu-schedule.md                         RSU vesting schedule
  accounts.md                             Account inventory
  watchlist.md                            Symbols you track
  etf-classifications.md                  ETF-to-asset-class mapping
```

- Run `./setup.sh` to create `~/.terminalq/` with starter templates
- Run `/tq-ingest holdings` to import brokerage data interactively
- The repo's `reference/` directory contains only `.example.md` templates
- `PORTFOLIO_DIR` env var can override the data location if needed

## Architecture

- **MCP Server**: `src/terminalq/server.py` — 30 FastMCP tools, JSON over stdio
- **Providers** (`src/terminalq/providers/`):
  - `finnhub.py` — Quotes, profiles, news, earnings, analyst ratings, economic calendar (60 req/min)
  - `historical.py` — Historical OHLCV, dividends (Yahoo Finance via yfinance)
  - `edgar.py` — Financial statements, SEC filings (EDGAR XBRL, 10 req/sec)
  - `fred.py` — Economic indicators, macro dashboard, forex rates (FRED API, 120 req/min)
  - `technical.py` — SMA, EMA, RSI, MACD, Bollinger, ATR (computed)
  - `screener.py` — S&P 500 stock screener (cached CSV + profiles)
  - `coingecko.py` — Cryptocurrency prices (CoinGecko, free, 30 req/min)
  - `search.py` — Web search (Brave Search API)
  - `portfolio.py` — Portfolio/watchlist parser (reads from `~/.terminalq/`)
- **Analytics** (`src/terminalq/analytics/`):
  - `risk.py` — Sharpe, Sortino, max drawdown, VaR, beta vs SPY
  - `allocation.py` — Asset class breakdown, concentration risk
- **Charts**: `src/terminalq/charts.py` — Sparklines, line/candlestick charts, heatmaps, allocation bars
- **Infrastructure**: `cache.py`, `rate_limiter.py`, `logging_config.py`, `config.py`
- **Commands**: `commands/` — 30 slash commands
- **Tests**: `tests/` — 48 tests (pytest)
- **Docs**: `docs/` — API reference, provider/command guides, config reference

## API Keys

| Key | Required | Free Tier | Env Variable |
|-----|----------|-----------|-------------|
| Finnhub | Yes | 60 calls/min | `FINNHUB_API_KEY` |
| FRED | Yes | 120 calls/min | `FRED_API_KEY` |
| Brave Search | Optional | 2000 calls/mo | `BRAVE_API_KEY` |
| SEC EDGAR | No key needed | User-Agent header | `SEC_USER_AGENT` |
| Yahoo Finance | No key needed | Via yfinance | -- |
| CoinGecko | No key needed | 30 calls/min | -- |

Keys are loaded from `~/.env` via python-dotenv (`override=True`).

## MCP Tools (30)

**Quotes & Market Data:**
- `terminalq_get_quote(symbol)` — Real-time quote
- `terminalq_get_quotes_batch(symbols)` — Parallel batch quotes
- `terminalq_get_historical(symbol, period, interval)` — OHLCV price data
- `terminalq_get_dividends(symbol, years)` — Dividend history + yield

**Portfolio:**
- `terminalq_get_portfolio()` — Static holdings from `~/.terminalq/portfolio-holdings.md`
- `terminalq_get_portfolio_live()` — Holdings with live prices + daily P&L
- `terminalq_get_rsu_schedule()` — RSU vesting schedule from `~/.terminalq/rsu-schedule.md`
- `terminalq_get_watchlist()` — Watchlist with live quotes
- `terminalq_get_risk_metrics(period)` — Sharpe, Sortino, VaR, beta, max drawdown
- `terminalq_get_allocation()` — Asset class breakdown + concentration risk

**Research & Fundamentals:**
- `terminalq_get_company_profile(symbol)` — Company overview
- `terminalq_get_news(symbol, days)` — Company news
- `terminalq_get_earnings(symbol)` — EPS history + estimates
- `terminalq_get_analyst_ratings(symbol)` — Buy/Hold/Sell consensus + price targets
- `terminalq_get_financials(symbol, statement, periods)` — SEC financial statements
- `terminalq_get_filings(symbol, filing_type, limit)` — SEC filing search
- `terminalq_get_technicals(symbol)` — SMA/EMA/RSI/MACD/Bollinger/ATR

**Charts & Visualization:**
- `terminalq_chart_price(symbol, period, chart_type)` — Line or candlestick chart
- `terminalq_chart_comparison(symbols, period)` — Multi-symbol % return overlay
- `terminalq_chart_allocation()` — Portfolio allocation bar chart
- `terminalq_chart_yield_curve()` — US Treasury yield curve
- `terminalq_chart_sector_heatmap()` — S&P 500 sector performance

**Economics, Crypto & Search:**
- `terminalq_get_economic_indicator(indicator, limit)` — FRED data (gdp, cpi, fed_funds, etc.)
- `terminalq_get_macro_dashboard()` — 11 key economic indicators
- `terminalq_get_forex(pair)` — Currency exchange rates (FRED)
- `terminalq_get_crypto(symbol)` — Cryptocurrency quote (CoinGecko)
- `terminalq_get_crypto_batch(symbols)` — Batch crypto quotes
- `terminalq_get_economic_calendar(days)` — Upcoming economic events
- `terminalq_screen_stocks(sector, min_market_cap, max_market_cap, limit)` — S&P 500 screener
- `terminalq_web_search(query, count)` — Brave web search

## Slash Commands (30)

| Command | Description |
|---------|-------------|
| `/tq-setup` | Interactive onboarding — configure API keys and data directory |
| `/tq-quote SYMBOL` | Real-time quote with portfolio context |
| `/tq-portfolio` | All holdings with live prices, grouped by account |
| `/tq-news [SYMBOL]` | News for a ticker or top portfolio holdings |
| `/tq-rsu` | RSU vesting schedule + current employer stock price |
| `/tq-dividends SYMBOL` | Dividend history, yield, projected income |
| `/tq-earnings SYMBOL` | Earnings history, beat rate, EPS trend |
| `/tq-historical SYMBOL [PERIOD]` | Historical price data |
| `/tq-financials SYMBOL [TYPE]` | SEC financial statements |
| `/tq-filings SYMBOL [TYPE]` | SEC filing search |
| `/tq-technicals SYMBOL` | Technical analysis report |
| `/tq-economy [INDICATOR]` | Economic indicator or full macro dashboard |
| `/tq-screen [CRITERIA]` | S&P 500 stock screener |
| `/tq-chart SYMBOL [PERIOD] [TYPE]` | Price chart (line or candlestick) |
| `/tq-compare SYM1,SYM2,SYM3` | Multi-symbol performance comparison |
| `/tq-allocation` | Portfolio allocation visualization |
| `/tq-yield-curve` | US Treasury yield curve |
| `/tq-ratings SYMBOL` | Analyst ratings + price targets |
| `/tq-watchlist` | Watchlist with live quotes |
| `/tq-forex [PAIR]` | Forex rates (e.g., eurusd) |
| `/tq-crypto [SYMBOL]` | Crypto prices (BTC, ETH, SOL...) |
| `/tq-events` | Upcoming economic events calendar |
| `/tq-search QUERY` | Web search for financial research |
| `/tq-risk` | Portfolio risk metrics |
| `/tq-ingest [TYPE]` | Import brokerage data into `~/.terminalq/` |

## Error Convention

All tools return errors as `{"error": "message", "symbol": "SYM", "source": "provider_name"}`. Providers never raise exceptions — they catch and return error dicts.

## Code Conventions

These conventions were established from code review feedback and must be followed:

- **No magic constants.** API limits, budgets, and thresholds go in `config.py` (e.g., `BRAVE_MONTHLY_LIMIT`). Never duplicate a constant across files.
- **UTC for all timestamps from external APIs.** Use `datetime.fromtimestamp(ts, tz=timezone.utc)`, not naive `datetime.fromtimestamp(ts)` which uses local timezone and shifts dates.
- **Introspection tools must not audit themselves.** `terminalq_get_audit_log` and `terminalq_get_usage_stats` must NOT use the `@audited` decorator — it creates self-referential log pollution.
- **Async locks for shared state.** `usage_tracker.py` uses `asyncio.Lock` per provider for all read-modify-write operations (`increment_daily`, `record_payload_size`, `increment_and_check`). Never do separate check-then-act on usage files — use `increment_and_check()` for atomic budget enforcement.
- **Audit decorator captures all args.** The `@audited` wrapper uses `inspect.signature` + `bind()` to log both positional and keyword arguments. Do not rely on `kwargs` alone.
- **Hooks must exit non-zero to block.** Claude Code Stop hooks only enforce when the script exits non-zero. Use `exit 2` for quality gate failures.
- **Output contracts.** All 6 skills reference `docs/output-contracts.md`. Every financial skill output must include a **Data Freshness** table and **Disclaimer**. See the contracts doc for required sections per skill.
- **Screener completeness.** `is_complete` in screener results compares `matches_after_all` against `matches_after_sector` (not `len(results)`) to correctly flag when the profile fetch threshold caused partial results.
