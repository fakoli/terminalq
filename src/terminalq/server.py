"""TerminalQ MCP Server — financial data tools for Claude Code."""
import json

from mcp.server.fastmcp import FastMCP

from terminalq.providers import finnhub, portfolio, historical, edgar, fred, technical, screener, coingecko, search
from terminalq.analytics import risk, allocation
from terminalq import charts
from terminalq.logging_config import log

mcp = FastMCP("TerminalQ")


@mcp.tool()
async def terminalq_get_quote(symbol: str) -> str:
    """Get real-time stock/ETF quote with price, change, and volume.

    Args:
        symbol: Ticker symbol (e.g., AAPL, VTI, PINS)
    """
    result = await finnhub.get_quote(symbol.upper())
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_quotes_batch(symbols: str) -> str:
    """Get quotes for multiple symbols at once. More efficient than calling get_quote repeatedly.

    Args:
        symbols: Comma-separated ticker symbols (e.g., "AAPL,VTI,PINS,QUAL")
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    results = await finnhub.get_quotes_batch(symbol_list)
    return json.dumps(results, indent=2)


@mcp.tool()
async def terminalq_get_portfolio() -> str:
    """Get current portfolio holdings across all accounts (Fidelity Joint, Fidelity Roth IRA, Schwab).

    Returns all positions with shares, cost basis, market value, and unrealized gain/loss.
    Data comes from the most recent brokerage statements stored in reference/portfolio-holdings.md.
    """
    holdings = portfolio.load_portfolio()
    if not holdings:
        return json.dumps({"error": "No portfolio data found. Update reference/portfolio-holdings.md"})

    as_of = portfolio.get_portfolio_as_of()

    # Group by account
    accounts: dict[str, list] = {}
    for h in holdings:
        acct = h.get("account", "Unknown")
        accounts.setdefault(acct, []).append(h)

    total_value = sum(h["market_value"] for h in holdings)
    total_cost = sum(h["cost_basis"] for h in holdings)
    total_gl = sum(h["unrealized_gl"] for h in holdings)

    result = {
        "as_of": f"{as_of} (from brokerage statements)" if as_of else "Unknown",
        "total_market_value": round(total_value, 2),
        "total_cost_basis": round(total_cost, 2),
        "total_unrealized_gl": round(total_gl, 2),
        "accounts": {
            acct: {
                "holdings": acct_holdings,
                "account_value": round(sum(h["market_value"] for h in acct_holdings), 2),
            }
            for acct, acct_holdings in accounts.items()
        },
        "unique_symbols": portfolio.get_unique_symbols(),
    }
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_portfolio_live() -> str:
    """Get portfolio holdings with LIVE prices from Finnhub.

    Combines static holdings data with real-time quotes to show current values and daily P&L.
    """
    holdings = portfolio.load_portfolio()
    if not holdings:
        return json.dumps({"error": "No portfolio data found."})

    symbols = portfolio.get_unique_symbols()
    # Filter out non-equity symbols (CASH, money market funds)
    equity_symbols = [s for s in symbols if s not in ("CASH", "FDRXX")]
    quotes = await finnhub.get_quotes_batch(equity_symbols)
    quote_map = {q["symbol"]: q for q in quotes if "error" not in q}

    live_holdings = []
    total_live_value = 0
    total_daily_change = 0

    for h in holdings:
        sym = h["symbol"]
        q = quote_map.get(sym, {})
        live_price = q.get("current_price")
        if live_price and h["shares"]:
            live_value = live_price * h["shares"]
            daily_change = (q.get("change") or 0) * h["shares"]
            price_source = "live"
        else:
            live_value = h["market_value"]
            daily_change = 0
            price_source = "stale_reference"

        live_holdings.append({
            **h,
            "live_price": live_price,
            "live_value": round(live_value, 2),
            "daily_change": round(daily_change, 2),
            "daily_pct": q.get("percent_change"),
            "price_source": price_source,
        })
        total_live_value += live_value
        total_daily_change += daily_change

    stale_count = sum(1 for lh in live_holdings if lh["price_source"] == "stale_reference")

    result = {
        "total_live_value": round(total_live_value, 2),
        "total_daily_change": round(total_daily_change, 2),
        "holdings": live_holdings,
        "stale_holdings_count": stale_count,
        "source": "finnhub (live) + portfolio-holdings.md (static)",
    }
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_company_profile(symbol: str) -> str:
    """Get company profile including name, industry, market cap, and key info.

    Args:
        symbol: Ticker symbol (e.g., AAPL, PINS)
    """
    result = await finnhub.get_company_profile(symbol.upper())
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_news(symbol: str, days: int = 7) -> str:
    """Get recent news articles for a company.

    Args:
        symbol: Ticker symbol (e.g., AAPL, PINS)
        days: Number of days to look back (default 7)
    """
    results = await finnhub.get_company_news(symbol.upper(), days)
    return json.dumps(results, indent=2)


@mcp.tool()
async def terminalq_get_rsu_schedule() -> str:
    """Get Pinterest RSU vesting schedule for 2026-2028."""
    schedule = portfolio.load_rsu_schedule()
    if not schedule:
        return json.dumps({"error": "No RSU schedule found. Update reference/rsu-schedule.md"})
    return json.dumps({"rsu_schedule": schedule}, indent=2)


@mcp.tool()
async def terminalq_get_earnings(symbol: str) -> str:
    """Get earnings history and estimates for a company.

    Args:
        symbol: Ticker symbol (e.g., AAPL, PINS)
    """
    result = await finnhub.get_earnings(symbol.upper())
    return json.dumps(result, indent=2)


# ---- Phase 1: New tools ----


@mcp.tool()
async def terminalq_get_historical(symbol: str, period: str = "1y", interval: str = "1d") -> str:
    """Get historical OHLCV price data for a symbol.

    Args:
        symbol: Ticker symbol (e.g., AAPL, VTI)
        period: Lookback period — 1mo, 3mo, 6mo, 1y, 2y, 5y, max (default 1y)
        interval: Data interval — 1d, 1wk, 1mo (default 1d)
    """
    result = await historical.get_historical(symbol.upper(), period, interval)
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_dividends(symbol: str, years: int = 5) -> str:
    """Get dividend payment history and current yield.

    Args:
        symbol: Ticker symbol (e.g., AAPL, VTI)
        years: Years of history to fetch (default 5)
    """
    result = await historical.get_dividends(symbol.upper(), years)
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_financials(symbol: str, statement: str = "income", periods: int = 4) -> str:
    """Get financial statements from SEC filings (income statement, balance sheet, cash flow).

    Args:
        symbol: Ticker symbol (e.g., AAPL, PINS)
        statement: Type — income, balance_sheet, or cash_flow (default income)
        periods: Number of annual reporting periods to return (default 4)
    """
    result = await edgar.get_financials(symbol.upper(), statement, periods)
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_filings(symbol: str, filing_type: str = "", limit: int = 10) -> str:
    """Search SEC filings for a company (10-K, 10-Q, 8-K, etc.).

    Args:
        symbol: Ticker symbol (e.g., AAPL, PINS)
        filing_type: Filter by type — 10-K, 10-Q, 8-K, DEF 14A, etc. (empty = all)
        limit: Maximum results (default 10)
    """
    result = await edgar.get_filings(symbol.upper(), filing_type, limit)
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_economic_indicator(indicator: str, limit: int = 12) -> str:
    """Get economic indicator data from FRED (Federal Reserve).

    Args:
        indicator: Indicator name or FRED series ID. Names: gdp, cpi, core_cpi, ppi,
                   unemployment, fed_funds, 10y_yield, 2y_yield, 30y_yield, initial_claims,
                   nonfarm_payrolls, pce, housing_starts, consumer_sentiment, yield_spread
        limit: Number of recent observations (default 12)
    """
    result = await fred.get_series(indicator, limit)
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_macro_dashboard() -> str:
    """Get a dashboard of key economic indicators (GDP, CPI, unemployment, Fed funds, yields, etc.).

    Returns latest and previous values with change for each indicator.
    """
    result = await fred.get_economic_dashboard()
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_technicals(symbol: str) -> str:
    """Get technical analysis indicators for a symbol (SMA, EMA, RSI, MACD, Bollinger Bands, ATR).

    Args:
        symbol: Ticker symbol (e.g., AAPL, PINS)
    """
    result = await technical.get_full_technicals(symbol.upper())
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_screen_stocks(
    sector: str = "",
    min_market_cap: float = 0,
    max_market_cap: float = 0,
    limit: int = 20,
) -> str:
    """Screen S&P 500 stocks by criteria.

    Args:
        sector: Sector filter (e.g., Technology, Healthcare, Financials). Partial match supported.
        min_market_cap: Minimum market cap in millions (0 = no minimum)
        max_market_cap: Maximum market cap in millions (0 = no maximum)
        limit: Maximum results to return (default 20)
    """
    result = await screener.screen_stocks(
        sector=sector,
        min_market_cap=min_market_cap,
        max_market_cap=max_market_cap,
        limit=limit,
    )
    return json.dumps(result, indent=2)


# ---- Phase 2: Charts & Visualization ----


@mcp.tool()
async def terminalq_chart_price(symbol: str, period: str = "6mo", chart_type: str = "line") -> str:
    """Generate a price chart for a symbol.

    Args:
        symbol: Ticker symbol (e.g., AAPL, VTI)
        period: Lookback period — 1mo, 3mo, 6mo, 1y, 2y, 5y (default 6mo)
        chart_type: Chart type — "line" or "candlestick" (default line)
    """
    hist = await historical.get_historical(symbol.upper(), period, "1d")
    if "error" in hist:
        return json.dumps(hist, indent=2)

    prices = hist.get("prices", [])
    if not prices:
        return json.dumps({"error": "No price data", "symbol": symbol})

    title = f"{symbol.upper()} ({period})"
    if chart_type == "candlestick":
        chart = charts.candlestick_chart(prices, title=title)
    else:
        closes = [p["close"] for p in prices]
        labels = [p["date"][5:] for p in prices]  # MM-DD
        chart = charts.line_chart(closes, labels=labels, title=title)

    first, last = prices[0]["close"], prices[-1]["close"]
    pct_return = round((last / first - 1) * 100, 2) if first else 0
    high = max(p["high"] for p in prices)
    low = min(p["low"] for p in prices)

    summary = f"{symbol.upper()} — ${last:.2f} ({'+' if pct_return >= 0 else ''}{pct_return}% over {period})  High: ${high:.2f}  Low: ${low:.2f}"
    return f"{summary}\n\n```\n{chart}\n```"


@mcp.tool()
async def terminalq_chart_comparison(symbols: str, period: str = "1y") -> str:
    """Compare price performance of multiple symbols on one chart (% return normalized).

    Args:
        symbols: Comma-separated ticker symbols (e.g., "AAPL,MSFT,GOOGL")
        period: Lookback period — 1mo, 3mo, 6mo, 1y, 2y (default 1y)
    """
    import asyncio as _asyncio
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if len(symbol_list) < 2:
        return json.dumps({"error": "Provide at least 2 symbols separated by commas"})

    results = await _asyncio.gather(
        *[historical.get_historical(sym, period, "1d") for sym in symbol_list],
        return_exceptions=True,
    )

    series = {}
    for sym, result in zip(symbol_list, results):
        if isinstance(result, Exception) or (isinstance(result, dict) and "error" in result):
            continue
        prices = result.get("prices", [])
        if prices:
            series[sym] = [p["close"] for p in prices]

    if len(series) < 2:
        return json.dumps({"error": "Need at least 2 symbols with data"})

    title = f"{' vs '.join(series.keys())} — {period} % Return"
    chart = charts.comparison_chart(series, title=title)
    return f"```\n{chart}\n```"


@mcp.tool()
async def terminalq_chart_allocation() -> str:
    """Visualize portfolio allocation by asset class."""
    alloc = allocation.compute_allocation()
    if "error" in alloc:
        return json.dumps(alloc, indent=2)

    by_class = alloc.get("by_asset_class", {})
    categories = {k: v.get("value", 0) for k, v in by_class.items()}
    chart = charts.allocation_pie(categories, title="Portfolio Allocation by Asset Class")
    return f"```\n{chart}\n```"


@mcp.tool()
async def terminalq_chart_yield_curve() -> str:
    """Plot the current US Treasury yield curve from FRED data."""
    import asyncio as _asyncio
    maturity_series = {
        "1mo": "DGS1MO", "3mo": "DGS3MO", "6mo": "DGS6MO",
        "1Y": "DGS1", "2Y": "DGS2", "5Y": "DGS5",
        "10Y": "DGS10", "20Y": "DGS20", "30Y": "DGS30",
    }

    results = await _asyncio.gather(
        *[fred.get_series(sid, limit=1) for sid in maturity_series.values()],
        return_exceptions=True,
    )

    maturities = []
    yields_list = []
    for label, result in zip(maturity_series.keys(), results):
        if isinstance(result, BaseException) or (isinstance(result, dict) and "error" in result):
            continue
        val = result.get("latest_value")
        if val is not None:
            maturities.append(label)
            yields_list.append(val)

    if len(yields_list) < 3:
        return json.dumps({"error": "Insufficient yield curve data from FRED"})

    chart = charts.yield_curve_chart(maturities, yields_list)
    return f"```\n{chart}\n```"


@mcp.tool()
async def terminalq_chart_sector_heatmap() -> str:
    """Show S&P 500 sector performance as a heatmap."""
    import asyncio as _asyncio
    sector_etfs = {
        "Technology": "XLK", "Healthcare": "XLV", "Financials": "XLF",
        "Cons. Disc.": "XLY", "Industrials": "XLI", "Comm. Svcs": "XLC",
        "Cons. Staples": "XLP", "Energy": "XLE", "Utilities": "XLU",
        "Real Estate": "XLRE", "Materials": "XLB",
    }

    results = await _asyncio.gather(
        *[historical.get_historical(etf, "1mo", "1d") for etf in sector_etfs.values()],
        return_exceptions=True,
    )

    sector_returns = {}
    for (sector, _), result in zip(sector_etfs.items(), results):
        if isinstance(result, BaseException) or (isinstance(result, dict) and "error" in result):
            continue
        prices = result.get("prices", [])
        if len(prices) >= 2:
            ret = round((prices[-1]["close"] / prices[0]["close"] - 1) * 100, 2)
            sector_returns[sector] = ret

    if not sector_returns:
        return json.dumps({"error": "Could not fetch sector data"})

    chart = charts.heatmap(sector_returns, title="S&P 500 Sector Performance (1mo)")
    return f"```\n{chart}\n```"


# ---- Phase 2: Bloomberg Features ----


@mcp.tool()
async def terminalq_get_analyst_ratings(symbol: str) -> str:
    """Get analyst ratings consensus and price targets for a stock.

    Args:
        symbol: Ticker symbol (e.g., AAPL, PINS)
    """
    result = await finnhub.get_analyst_ratings(symbol.upper())
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_watchlist() -> str:
    """Get watchlist symbols with live quotes and daily changes."""
    items = portfolio.load_watchlist()
    if not items:
        return json.dumps({"error": "No watchlist found. Create reference/watchlist.md"})

    symbols = [item["symbol"] for item in items]
    quotes = await finnhub.get_quotes_batch(symbols)
    quote_map = {q["symbol"]: q for q in quotes}

    watchlist = []
    for item in items:
        sym = item["symbol"]
        q = quote_map.get(sym, {})
        watchlist.append({
            **item,
            "current_price": q.get("current_price"),
            "change": q.get("change"),
            "percent_change": q.get("percent_change"),
        })

    return json.dumps({"watchlist": watchlist, "source": "finnhub + watchlist.md"}, indent=2)


@mcp.tool()
async def terminalq_get_forex(pair: str = "") -> str:
    """Get forex exchange rates from FRED.

    Args:
        pair: Currency pair alias (e.g., eurusd, usdjpy, gbpusd). Leave blank for all major pairs.
    """
    if pair:
        result = await fred.get_forex(pair)
        return json.dumps(result, indent=2)

    # Dashboard: fetch all pairs
    import asyncio as _asyncio
    pairs = list(fred.FOREX_SERIES_MAP.keys())
    results = await _asyncio.gather(
        *[fred.get_forex(p, limit=2) for p in pairs],
        return_exceptions=True,
    )
    dashboard = {}
    for p, r in zip(pairs, results):
        if isinstance(r, BaseException) or (isinstance(r, dict) and "error" in r):
            dashboard[p.upper()] = {"error": str(r) if isinstance(r, BaseException) else r.get("error")}
        else:
            dashboard[p.upper()] = {
                "rate": r.get("latest_rate"),
                "change": r.get("change"),
                "change_pct": r.get("change_pct"),
                "date": r.get("latest_date"),
            }
    return json.dumps({"forex_rates": dashboard, "source": "fred"}, indent=2)


@mcp.tool()
async def terminalq_get_crypto(symbol: str) -> str:
    """Get current cryptocurrency price, market cap, and 24h change.

    Args:
        symbol: Crypto ticker (BTC, ETH, SOL) or CoinGecko ID (bitcoin, ethereum)
    """
    result = await coingecko.get_crypto_quote(symbol)
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_crypto_batch(symbols: str) -> str:
    """Get prices for multiple cryptocurrencies at once.

    Args:
        symbols: Comma-separated crypto tickers (e.g., "BTC,ETH,SOL,XRP")
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    results = await coingecko.get_crypto_batch(symbol_list)
    return json.dumps(results, indent=2)


@mcp.tool()
async def terminalq_get_economic_calendar(days: int = 7) -> str:
    """Get upcoming economic events and data releases (CPI, FOMC, NFP, etc.).

    Args:
        days: Number of days to look ahead (default 7)
    """
    result = await finnhub.get_economic_calendar(days)
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_web_search(query: str, count: int = 5) -> str:
    """Search the web for financial news, company info, or market analysis.

    Args:
        query: Search query (e.g., "Pinterest Q4 earnings", "Fed rate decision March 2026")
        count: Number of results to return (default 5, max 20)
    """
    result = await search.web_search(query, min(count, 20))
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_risk_metrics(period: str = "1y") -> str:
    """Get portfolio risk analytics (Sharpe, Sortino, max drawdown, VaR, beta vs SPY).

    Args:
        period: Analysis period — 3mo, 6mo, 1y, 2y (default 1y)
    """
    result = await risk.compute_portfolio_risk(period)
    return json.dumps(result, indent=2)


@mcp.tool()
async def terminalq_get_allocation() -> str:
    """Get portfolio allocation analysis by asset class, region, and sub-class.

    Shows concentration risk, top holdings, and single-stock exposure.
    """
    result = allocation.compute_allocation()
    return json.dumps(result, indent=2)


def main():
    """Run the TerminalQ MCP server."""
    log.info("Starting TerminalQ MCP server")
    mcp.run(transport="stdio")
