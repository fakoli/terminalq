"""Portfolio risk analytics — Sharpe, Sortino, max drawdown, VaR, beta.

Uses only stdlib math/statistics for calculations. Fetches historical data
via the historical provider and portfolio holdings from the portfolio provider.
"""
import asyncio
import math
import statistics
from datetime import datetime, timedelta

from terminalq import cache
from terminalq.config import CACHE_TTL_RISK
from terminalq.logging_config import log
from terminalq.providers import portfolio, historical


# Risk-free rate assumption (annualized, approx current T-bill rate)
RISK_FREE_RATE = 0.045

# Trading days per year
TRADING_DAYS = 252


def _daily_returns(prices: list[float]) -> list[float]:
    """Compute daily returns from a list of closing prices (oldest first)."""
    if len(prices) < 2:
        return []
    return [(prices[i] / prices[i - 1]) - 1.0 for i in range(1, len(prices))]


def _sharpe_ratio(returns: list[float], risk_free_daily: float) -> float | None:
    """Annualized Sharpe ratio."""
    if len(returns) < 2:
        return None
    excess = [r - risk_free_daily for r in returns]
    avg = statistics.mean(excess)
    std = statistics.stdev(excess)
    if std == 0:
        return None
    return round((avg / std) * math.sqrt(TRADING_DAYS), 4)


def _sortino_ratio(returns: list[float], risk_free_daily: float) -> float | None:
    """Annualized Sortino ratio (downside deviation only)."""
    if len(returns) < 2:
        return None
    excess = [r - risk_free_daily for r in returns]
    avg = statistics.mean(excess)
    downside = [r for r in excess if r < 0]
    if len(downside) < 2:
        return None
    downside_std = math.sqrt(sum(d ** 2 for d in downside) / len(downside))
    if downside_std == 0:
        return None
    return round((avg / downside_std) * math.sqrt(TRADING_DAYS), 4)


def _max_drawdown(prices: list[float]) -> float | None:
    """Maximum drawdown from peak (oldest to newest prices)."""
    if len(prices) < 2:
        return None
    peak = prices[0]
    max_dd = 0.0
    for price in prices:
        if price > peak:
            peak = price
        dd = (peak - price) / peak
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 4)


def _var_95(returns: list[float]) -> float | None:
    """Value at Risk at 95% confidence (historical method)."""
    if len(returns) < 20:
        return None
    sorted_returns = sorted(returns)
    idx = int(len(sorted_returns) * 0.05)
    return round(sorted_returns[idx], 4)


def _beta(portfolio_returns: list[float], benchmark_returns: list[float]) -> float | None:
    """Beta of portfolio vs benchmark."""
    n = min(len(portfolio_returns), len(benchmark_returns))
    if n < 20:
        return None
    pr = portfolio_returns[:n]
    br = benchmark_returns[:n]
    mean_pr = statistics.mean(pr)
    mean_br = statistics.mean(br)
    cov = sum((pr[i] - mean_pr) * (br[i] - mean_br) for i in range(n)) / (n - 1)
    var_br = statistics.variance(br)
    if var_br == 0:
        return None
    return round(cov / var_br, 4)


async def compute_portfolio_risk(period: str = "1y") -> dict:
    """Compute portfolio risk metrics.

    Loads portfolio holdings, fetches historical prices for all equity symbols,
    computes weighted daily portfolio returns, then calculates risk metrics.

    Args:
        period: Historical period for analysis (default "1y").

    Returns:
        Dict with Sharpe, Sortino, max drawdown, VaR(95%), beta vs SPY.
    """
    cache_key = f"risk_metrics_{period}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    holdings = portfolio.load_portfolio()
    if not holdings:
        return {"error": "No portfolio holdings found", "source": "analytics"}

    # Aggregate holdings by symbol and compute weights
    symbol_values: dict[str, float] = {}
    for h in holdings:
        sym = h["symbol"]
        val = h.get("market_value", 0)
        if sym in ("CASH", "FDRXX") or val <= 0:
            continue
        symbol_values[sym] = symbol_values.get(sym, 0) + val

    total_value = sum(symbol_values.values())
    if total_value <= 0:
        return {"error": "Portfolio has no equity value", "source": "analytics"}

    weights = {sym: val / total_value for sym, val in symbol_values.items()}
    equity_symbols = list(symbol_values.keys())

    # Fetch historical data for all equity symbols + SPY (benchmark)
    all_symbols = equity_symbols + ["SPY"]
    log.info("Fetching historical data for %d symbols for risk analysis", len(all_symbols))

    hist_results = await asyncio.gather(
        *[historical.get_historical(sym, period=period, interval="1d") for sym in all_symbols],
        return_exceptions=True,
    )

    # Extract closing prices per symbol (oldest first)
    symbol_prices: dict[str, list[float]] = {}
    for sym, result in zip(all_symbols, hist_results):
        if isinstance(result, BaseException):
            log.warning("Failed to fetch historical for %s: %s", sym, result)
            continue
        if isinstance(result, dict) and "error" not in result:
            prices_list = result.get("prices", [])
            if prices_list:
                # prices are returned newest first in some providers; ensure oldest first
                closes = [p["close"] for p in prices_list]
                # Check if oldest first (first date < last date)
                dates = [p["date"] for p in prices_list]
                if dates and dates[0] > dates[-1]:
                    closes = list(reversed(closes))
                symbol_prices[sym] = closes

    if not symbol_prices:
        return {"error": "Could not fetch historical data for any holdings", "source": "analytics"}

    # Compute daily returns per symbol
    symbol_returns: dict[str, list[float]] = {}
    for sym, prices in symbol_prices.items():
        rets = _daily_returns(prices)
        if rets:
            symbol_returns[sym] = rets

    # Find minimum return series length across portfolio symbols
    portfolio_symbols_with_data = [s for s in equity_symbols if s in symbol_returns]
    if not portfolio_symbols_with_data:
        return {"error": "No historical return data for portfolio symbols", "source": "analytics"}

    min_len = min(len(symbol_returns[s]) for s in portfolio_symbols_with_data)

    # Compute weighted portfolio daily returns
    portfolio_daily_returns = []
    for i in range(min_len):
        day_return = 0.0
        total_weight = 0.0
        for sym in portfolio_symbols_with_data:
            w = weights.get(sym, 0)
            if i < len(symbol_returns[sym]):
                day_return += w * symbol_returns[sym][i]
                total_weight += w
        if total_weight > 0:
            portfolio_daily_returns.append(day_return / total_weight)

    if len(portfolio_daily_returns) < 20:
        return {"error": "Insufficient data points for risk calculation", "source": "analytics"}

    risk_free_daily = RISK_FREE_RATE / TRADING_DAYS

    # Compute cumulative portfolio prices for drawdown
    portfolio_prices = [1.0]
    for r in portfolio_daily_returns:
        portfolio_prices.append(portfolio_prices[-1] * (1.0 + r))

    # Benchmark returns (SPY)
    spy_returns = symbol_returns.get("SPY", [])

    # Annual return
    total_return = portfolio_prices[-1] / portfolio_prices[0] - 1.0
    days = len(portfolio_daily_returns)
    annual_return = (1.0 + total_return) ** (TRADING_DAYS / days) - 1.0

    # Volatility (annualized)
    annual_volatility = statistics.stdev(portfolio_daily_returns) * math.sqrt(TRADING_DAYS)

    result = {
        "period": period,
        "data_points": len(portfolio_daily_returns),
        "symbols_analyzed": len(portfolio_symbols_with_data),
        "total_symbols": len(equity_symbols),
        "annual_return": round(annual_return, 4),
        "annual_volatility": round(annual_volatility, 4),
        "sharpe_ratio": _sharpe_ratio(portfolio_daily_returns, risk_free_daily),
        "sortino_ratio": _sortino_ratio(portfolio_daily_returns, risk_free_daily),
        "max_drawdown": _max_drawdown(portfolio_prices),
        "var_95": _var_95(portfolio_daily_returns),
        "beta_vs_spy": _beta(portfolio_daily_returns, spy_returns[:min_len]) if spy_returns else None,
        "risk_free_rate": RISK_FREE_RATE,
        "source": "analytics",
    }
    cache.set(cache_key, result, CACHE_TTL_RISK)
    return result
