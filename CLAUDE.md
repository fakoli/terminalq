# TerminalQ

Bloomberg-style financial terminal for portfolio intelligence, built as a Claude Code MCP plugin.

## Quick Start

```bash
./setup.sh          # Install deps, create ~/.terminalq/, check API keys
uv run python -m terminalq  # Start MCP server
```

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
- Run `/ingest holdings` to import brokerage data interactively
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
- **Commands**: `commands/` — 29 slash commands
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
- `terminalq_get_rsu_schedule()` — RSU vesting from `~/.terminalq/rsu-schedule.md`
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

## Slash Commands (29)

| Command | Description |
|---------|-------------|
| `/quote SYMBOL` | Real-time quote with portfolio context |
| `/portfolio` | All holdings with live prices, grouped by account |
| `/news [SYMBOL]` | News for a ticker or top portfolio holdings |
| `/rsu` | RSU vesting schedule + current stock price |
| `/dividends SYMBOL` | Dividend history, yield, projected income |
| `/earnings SYMBOL` | Earnings history, beat rate, EPS trend |
| `/historical SYMBOL [PERIOD]` | Historical price data |
| `/financials SYMBOL [TYPE]` | SEC financial statements |
| `/filings SYMBOL [TYPE]` | SEC filing search |
| `/technicals SYMBOL` | Technical analysis report |
| `/economy [INDICATOR]` | Economic indicator or full macro dashboard |
| `/screen [CRITERIA]` | S&P 500 stock screener |
| `/chart SYMBOL [PERIOD] [TYPE]` | Price chart (line or candlestick) |
| `/compare SYM1,SYM2,SYM3` | Multi-symbol performance comparison |
| `/allocation` | Portfolio allocation visualization |
| `/yield-curve` | US Treasury yield curve |
| `/ratings SYMBOL` | Analyst ratings + price targets |
| `/watchlist` | Watchlist with live quotes |
| `/forex [PAIR]` | Forex rates (e.g., eurusd) |
| `/crypto [SYMBOL]` | Crypto prices (BTC, ETH, SOL...) |
| `/events` | Upcoming economic events calendar |
| `/search QUERY` | Web search for financial research |
| `/risk` | Portfolio risk metrics |
| `/ingest [TYPE]` | Import brokerage data into `~/.terminalq/` |

## Error Convention

All tools return errors as `{"error": "message", "symbol": "SYM", "source": "provider_name"}`. Providers never raise exceptions — they catch and return error dicts.
