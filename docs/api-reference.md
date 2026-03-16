# TerminalQ API Reference

All 16 MCP tools exposed by the TerminalQ server. Each tool returns a JSON string.

---

## Quotes & Market Data

### terminalq_get_quote

Get a real-time stock/ETF quote with price, change, and volume.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbol` | str | yes | -- | Ticker symbol (e.g., AAPL, VTI, PINS) |

**Return JSON:**

```json
{
  "symbol": "AAPL",
  "current_price": 178.50,
  "change": 2.35,
  "percent_change": 1.33,
  "high": 179.10,
  "low": 175.80,
  "open": 176.00,
  "previous_close": 176.15,
  "timestamp": 1710500000,
  "source": "finnhub"
}
```

**Data source:** Finnhub `/quote` endpoint
**Cache TTL:** 60 seconds (CACHE_TTL_QUOTES)

---

### terminalq_get_quotes_batch

Get quotes for multiple symbols at once. More efficient than calling get_quote repeatedly. Fetches uncached symbols in parallel, respecting rate limits.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbols` | str | yes | -- | Comma-separated ticker symbols (e.g., "AAPL,VTI,PINS,QUAL") |

**Return JSON:** Array of quote objects (same structure as `get_quote`).

```json
[
  { "symbol": "AAPL", "current_price": 178.50, "change": 2.35, ... },
  { "symbol": "VTI", "current_price": 265.20, "change": -0.80, ... }
]
```

**Data source:** Finnhub `/quote` endpoint (parallel requests)
**Cache TTL:** 60 seconds per symbol (CACHE_TTL_QUOTES)

---

### terminalq_get_historical

Get historical OHLCV (Open, High, Low, Close, Volume) price data.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbol` | str | yes | -- | Ticker symbol (e.g., AAPL, VTI) |
| `period` | str | no | `"1y"` | Lookback period: 1mo, 3mo, 6mo, 1y, 2y, 5y, max |
| `interval` | str | no | `"1d"` | Data interval: 1d, 1wk, 1mo |

**Return JSON:**

```json
{
  "symbol": "AAPL",
  "period": "1y",
  "interval": "1d",
  "data_points": 252,
  "prices": [
    { "date": "2025-03-15", "open": 175.00, "high": 178.50, "low": 174.80, "close": 178.10, "volume": 52340000 }
  ],
  "source": "yahoo_finance"
}
```

**Data source:** Yahoo Finance via yfinance library
**Cache TTL:** 21600 seconds / 6 hours (CACHE_TTL_HISTORY)

---

### terminalq_get_dividends

Get dividend payment history and current yield.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbol` | str | yes | -- | Ticker symbol (e.g., AAPL, VTI) |
| `years` | int | no | `5` | Years of dividend history to fetch |

**Return JSON:**

```json
{
  "symbol": "AAPL",
  "dividends": [
    { "date": "2025-02-14", "amount": 0.25 }
  ],
  "annual_dividend": 1.00,
  "dividend_yield": 0.0056,
  "payout_frequency": "quarterly",
  "source": "yahoo_finance"
}
```

**Data source:** Yahoo Finance via yfinance library
**Cache TTL:** 86400 seconds / 24 hours (CACHE_TTL_DIVIDENDS)

---

## Portfolio

### terminalq_get_portfolio

Get current portfolio holdings across all accounts (static data from reference files).

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| *(none)* | -- | -- | -- | -- |

**Return JSON:**

```json
{
  "as_of": "Feb 28, 2026 (from brokerage statements)",
  "total_market_value": 250000.00,
  "total_cost_basis": 200000.00,
  "total_unrealized_gl": 50000.00,
  "accounts": {
    "Brokerage Account (1234)": {
      "holdings": [
        { "symbol": "VTI", "name": "Vanguard Total Stock", "shares": 100.0, "cost_basis": 20000.00, "market_value": 26500.00, "unrealized_gl": 6500.00, "account": "..." }
      ],
      "account_value": 150000.00
    }
  },
  "unique_symbols": ["AAPL", "PINS", "VTI", ...]
}
```

**Data source:** Local file `reference/portfolio-holdings.md`
**Cache TTL:** None (reads file on every call)

---

### terminalq_get_portfolio_live

Get portfolio holdings with live prices from Finnhub. Combines static holdings data with real-time quotes to show current values and daily P&L.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| *(none)* | -- | -- | -- | -- |

**Return JSON:**

```json
{
  "total_live_value": 255000.00,
  "total_daily_change": 1250.00,
  "holdings": [
    {
      "symbol": "VTI", "shares": 100.0, "cost_basis": 20000.00,
      "live_price": 265.20, "live_value": 26520.00,
      "daily_change": 80.00, "daily_pct": 0.30,
      "price_source": "live"
    }
  ],
  "stale_holdings_count": 1,
  "source": "finnhub (live) + portfolio-holdings.md (static)"
}
```

**Data source:** Finnhub (live prices) + `reference/portfolio-holdings.md` (positions)
**Cache TTL:** 60 seconds for quote data (CACHE_TTL_QUOTES)

---

### terminalq_get_rsu_schedule

Get RSU vesting schedule from ~/.terminalq/rsu-schedule.md.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| *(none)* | -- | -- | -- | -- |

**Return JSON:**

```json
{
  "rsu_schedule": [
    { "date": "May 15, 2026", "grant": "Grant A", "pct_of_grant": "25%", "est_value": "$15,000" }
  ]
}
```

**Data source:** Local file `reference/rsu-schedule.md`
**Cache TTL:** None (reads file on every call)

---

## Research & Fundamentals

### terminalq_get_company_profile

Get company overview including name, industry, market cap, and key info.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbol` | str | yes | -- | Ticker symbol (e.g., AAPL, PINS) |

**Return JSON:**

```json
{
  "symbol": "MSFT",
  "name": "Microsoft Corporation",
  "exchange": "NASDAQ",
  "industry": "Technology",
  "market_cap": 3200000,
  "shares_outstanding": 7430,
  "logo": "https://...",
  "weburl": "https://www.microsoft.com",
  "ipo": "1986-03-13",
  "country": "US",
  "currency": "USD",
  "source": "finnhub"
}
```

**Data source:** Finnhub `/stock/profile2` endpoint
**Cache TTL:** 86400 seconds / 24 hours (CACHE_TTL_FUNDAMENTALS)

---

### terminalq_get_news

Get recent news articles for a company.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbol` | str | yes | -- | Ticker symbol (e.g., AAPL, PINS) |
| `days` | int | no | `7` | Number of days to look back |

**Return JSON:**

```json
[
  {
    "headline": "Apple Reports Q4 Earnings Beat",
    "summary": "Apple Inc reported...",
    "source": "Reuters",
    "url": "https://...",
    "datetime": 1710400000,
    "category": "company",
    "related": "AAPL"
  }
]
```

Returns up to 20 articles. Summaries are truncated to 200 characters.

**Data source:** Finnhub `/company-news` endpoint
**Cache TTL:** 900 seconds / 15 minutes (CACHE_TTL_NEWS)

---

### terminalq_get_earnings

Get earnings history and estimates for a company (last 8 quarters).

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbol` | str | yes | -- | Ticker symbol (e.g., AAPL, PINS) |

**Return JSON:**

```json
{
  "symbol": "AAPL",
  "earnings_history": [
    {
      "period": "2025-12-31",
      "actual_eps": 2.18,
      "estimate_eps": 2.10,
      "surprise": 0.08,
      "surprise_percent": 3.81
    }
  ],
  "source": "finnhub"
}
```

**Data source:** Finnhub `/stock/earnings` endpoint
**Cache TTL:** 3600 seconds / 1 hour (CACHE_TTL_EARNINGS)

---

### terminalq_get_financials

Get financial statements from SEC filings (income statement, balance sheet, or cash flow). Returns annual (10-K) data from XBRL company facts.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbol` | str | yes | -- | Ticker symbol (e.g., AAPL, PINS) |
| `statement` | str | no | `"income"` | Type: `income`, `balance_sheet`, or `cash_flow` |
| `periods` | int | no | `4` | Number of annual reporting periods to return |

**Return JSON (income statement example):**

```json
{
  "symbol": "AAPL",
  "statement": "income",
  "periods": [
    {
      "period_end": "2025-09-30",
      "fiscal_year": 2025,
      "revenue": 394328000000,
      "cost_of_revenue": 214137000000,
      "gross_profit": 180191000000,
      "operating_income": 119437000000,
      "net_income": 96995000000,
      "eps_basic": 6.16,
      "eps_diluted": 6.13
    }
  ],
  "source": "sec_edgar"
}
```

**Balance sheet metrics:** total_assets, total_liabilities, stockholders_equity, cash_and_equivalents, long_term_debt, current_assets, current_liabilities

**Cash flow metrics:** operating_cash_flow, investing_cash_flow, financing_cash_flow, capital_expenditure

**Data source:** SEC EDGAR XBRL company facts API
**Cache TTL:** 86400 seconds / 24 hours (CACHE_TTL_FINANCIALS)

---

### terminalq_get_filings

Search SEC filings for a company (10-K, 10-Q, 8-K, etc.).

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbol` | str | yes | -- | Ticker symbol (e.g., AAPL, PINS) |
| `filing_type` | str | no | `""` | Filter by type: 10-K, 10-Q, 8-K, DEF 14A, etc. Empty = all |
| `limit` | int | no | `10` | Maximum number of results |

**Return JSON:**

```json
{
  "symbol": "AAPL",
  "company_name": "APPLE INC",
  "cik": "0000320193",
  "filings": [
    {
      "type": "10-K",
      "filed_date": "2026-02-15",
      "description": "Form 10-K",
      "accession_number": "0001562088-26-000012",
      "url": "https://www.sec.gov/Archives/edgar/data/..."
    }
  ],
  "source": "sec_edgar"
}
```

**Data source:** SEC EDGAR submissions API
**Cache TTL:** 3600 seconds / 1 hour (CACHE_TTL_FILINGS)

---

### terminalq_get_technicals

Get technical analysis indicators: SMA, EMA, RSI, MACD, Bollinger Bands, and ATR. Computed from 1 year of daily historical price data.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `symbol` | str | yes | -- | Ticker symbol (e.g., AAPL, PINS) |

**Return JSON:**

```json
{
  "symbol": "AAPL",
  "price": 178.50,
  "sma": {
    "sma_20": 176.30, "sma_50": 174.10, "sma_200": 168.50,
    "current_price": 178.50,
    "signals": { "above_sma_20": true, "above_sma_50": true, "above_sma_200": true, "golden_cross": true }
  },
  "ema": { "ema_12": 177.80, "ema_26": 175.90, "ema_50": 174.20 },
  "rsi": { "rsi": 62.5, "signal": "neutral", "period": 14 },
  "macd": {
    "macd_line": 1.95, "signal_line": 1.50, "histogram": 0.45,
    "signal": "bullish",
    "parameters": { "fast": 12, "slow": 26, "signal": 9 }
  },
  "bollinger": {
    "upper_band": 182.40, "middle_band": 176.30, "lower_band": 170.20,
    "current_price": 178.50, "bandwidth": 12.20, "percent_b": 0.68, "signal": "neutral"
  },
  "atr": { "atr": 3.25, "period": 14 },
  "overall_signal": "bullish",
  "source": "computed from yahoo_finance data"
}
```

**Data source:** Computed from Yahoo Finance historical data
**Cache TTL:** 21600 seconds / 6 hours (CACHE_TTL_HISTORY)

---

## Economics & Screening

### terminalq_get_economic_indicator

Get economic indicator data from FRED (Federal Reserve Economic Data).

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `indicator` | str | yes | -- | Indicator name or FRED series ID (see aliases below) |
| `limit` | int | no | `12` | Number of recent observations |

**Supported indicator aliases:**

| Alias | FRED Series ID | Description |
|-------|---------------|-------------|
| `gdp` | GDP | Gross Domestic Product |
| `real_gdp` | GDPC1 | Real GDP |
| `cpi` | CPIAUCSL | Consumer Price Index |
| `core_cpi` | CPILFESL | Core CPI (ex. food & energy) |
| `ppi` | PPIACO | Producer Price Index |
| `unemployment` | UNRATE | Unemployment Rate |
| `fed_funds` | DFF | Federal Funds Rate |
| `10y_yield` | DGS10 | 10-Year Treasury Yield |
| `2y_yield` | DGS2 | 2-Year Treasury Yield |
| `30y_yield` | DGS30 | 30-Year Treasury Yield |
| `yield_spread` | T10Y2Y | 10Y-2Y Yield Spread |
| `initial_claims` | ICSA | Initial Jobless Claims |
| `nonfarm_payrolls` | PAYEMS | Nonfarm Payrolls |
| `pce` | PCE | Personal Consumption Expenditures |
| `housing_starts` | HOUST | Housing Starts |
| `consumer_sentiment` | UMCSENT | Consumer Sentiment |

You can also pass any FRED series ID directly (e.g., `"M2SL"` for M2 money supply).

**Return JSON:**

```json
{
  "series_id": "UNRATE",
  "title": "Unemployment Rate",
  "frequency": "Monthly",
  "units": "Percent",
  "latest_value": 3.7,
  "latest_date": "2026-02-01",
  "observations": [
    { "date": "2026-02-01", "value": 3.7 },
    { "date": "2026-01-01", "value": 3.8 }
  ],
  "source": "fred"
}
```

**Data source:** FRED API (`api.stlouisfed.org`)
**Cache TTL:** 3600 seconds / 1 hour (CACHE_TTL_ECONOMIC), or 300 seconds / 5 minutes for intraday series like yields and fed funds (CACHE_TTL_ECONOMIC_INTRADAY)

---

### terminalq_get_macro_dashboard

Get a dashboard of key economic indicators with latest and previous values. Fetches 11 indicators in parallel: GDP, CPI, core CPI, unemployment, fed funds, 10Y yield, 2Y yield, yield spread, initial claims, nonfarm payrolls, and consumer sentiment.

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| *(none)* | -- | -- | -- | -- |

**Return JSON:**

```json
{
  "indicators": {
    "gdp": { "latest_value": 28200.0, "latest_date": "2025-10-01", "previous_value": 27800.0, "change": 400.0 },
    "cpi": { "latest_value": 315.2, "latest_date": "2026-02-01", "previous_value": 314.8, "change": 0.4 },
    "unemployment": { "latest_value": 3.7, "latest_date": "2026-02-01", "previous_value": 3.8, "change": -0.1 }
  },
  "source": "fred"
}
```

**Data source:** FRED API (11 parallel requests)
**Cache TTL:** 3600 seconds / 1 hour (CACHE_TTL_ECONOMIC)

---

### terminalq_screen_stocks

Screen S&P 500 stocks by sector and market cap. Sector filtering is local and fast. Numeric filters (market cap) require Finnhub profile fetches and are only applied when the sector-filtered set is small enough (<=50 symbols).

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `sector` | str | no | `""` | Sector filter (e.g., Technology, Healthcare, Financials). Partial match, case-insensitive. |
| `min_market_cap` | float | no | `0` | Minimum market cap in millions (0 = no minimum) |
| `max_market_cap` | float | no | `0` | Maximum market cap in millions (0 = no maximum) |
| `limit` | int | no | `20` | Maximum results to return |

**Return JSON:**

```json
{
  "total_universe": 503,
  "matches_after_sector": 75,
  "matches_after_all_filters": 20,
  "results": [
    { "symbol": "AAPL", "name": "Apple Inc.", "sector": "Information Technology", "market_cap": 2800000, "industry": "Technology" }
  ],
  "filters_applied": { "sector": "Technology", "min_market_cap": 50000 },
  "source": "screener (S&P 500)"
}
```

Results are sorted by market cap descending.

**Data source:** S&P 500 component list from datahub CSV + Finnhub profiles for numeric filtering
**Cache TTL:** 604800 seconds / 7 days for S&P 500 list (CACHE_TTL_SP500_LIST); 86400 seconds / 24 hours for screener data (CACHE_TTL_SCREENER)

---

## Error Format

All tools return errors in a consistent format:

```json
{
  "error": "Human-readable error message",
  "symbol": "AAPL",
  "source": "finnhub"
}
```

The `source` field identifies which provider produced the error (finnhub, yahoo_finance, sec_edgar, fred, technical_analysis, or screener).
