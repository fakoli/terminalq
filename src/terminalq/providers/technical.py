"""Technical analysis indicators — pure computation from historical price data."""
from terminalq import cache
from terminalq.config import CACHE_TTL_HISTORY
from terminalq.providers import historical


def _closes(prices: list[dict]) -> list[float]:
    """Extract closing prices from OHLCV dicts (oldest first)."""
    return [p["close"] for p in prices]


def compute_sma(closes: list[float], periods: list[int] | None = None) -> dict:
    """Compute Simple Moving Averages."""
    if periods is None:
        periods = [20, 50, 200]
    result = {}
    current = closes[-1] if closes else None
    for p in periods:
        if len(closes) >= p:
            sma = round(sum(closes[-p:]) / p, 2)
            result[f"sma_{p}"] = sma
        else:
            result[f"sma_{p}"] = None

    signals = {}
    for p in periods:
        key = f"sma_{p}"
        if result[key] is not None and current is not None:
            signals[f"above_sma_{p}"] = current > result[key]
        else:
            signals[f"above_sma_{p}"] = None

    # Golden/death cross (SMA50 vs SMA200)
    if result.get("sma_50") is not None and result.get("sma_200") is not None:
        signals["golden_cross"] = result["sma_50"] > result["sma_200"]
    else:
        signals["golden_cross"] = None

    result["current_price"] = current
    result["signals"] = signals
    return result


def compute_ema(closes: list[float], periods: list[int] | None = None) -> dict:
    """Compute Exponential Moving Averages."""
    if periods is None:
        periods = [12, 26, 50]
    result = {}
    for p in periods:
        if len(closes) < p:
            result[f"ema_{p}"] = None
            continue
        multiplier = 2 / (p + 1)
        ema = sum(closes[:p]) / p  # Start with SMA for first period
        for price in closes[p:]:
            ema = (price - ema) * multiplier + ema
        result[f"ema_{p}"] = round(ema, 2)
    return result


def compute_rsi(closes: list[float], period: int = 14) -> dict:
    """Compute Relative Strength Index."""
    if len(closes) < period + 1:
        return {"rsi": None, "signal": "insufficient_data", "period": period}

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    # Initial averages
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    # Smoothed averages
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        rsi = round(100 - (100 / (1 + rs)), 2)

    if rsi >= 70:
        signal = "overbought"
    elif rsi <= 30:
        signal = "oversold"
    else:
        signal = "neutral"

    return {"rsi": rsi, "signal": signal, "period": period}


def compute_macd(
    closes: list[float], fast: int = 12, slow: int = 26, signal_period: int = 9
) -> dict:
    """Compute MACD (Moving Average Convergence Divergence)."""
    if len(closes) < slow + signal_period:
        return {
            "macd_line": None, "signal_line": None, "histogram": None,
            "signal": "insufficient_data",
            "parameters": {"fast": fast, "slow": slow, "signal": signal_period},
        }

    def _ema_series(data: list[float], period: int) -> list[float]:
        multiplier = 2 / (period + 1)
        ema_val = sum(data[:period]) / period
        result = [ema_val]
        for price in data[period:]:
            ema_val = (price - ema_val) * multiplier + ema_val
            result.append(ema_val)
        return result

    fast_ema = _ema_series(closes, fast)
    slow_ema = _ema_series(closes, slow)

    # Align: slow_ema starts later
    offset = slow - fast
    macd_line_series = [
        fast_ema[i + offset] - slow_ema[i]
        for i in range(len(slow_ema))
    ]

    if len(macd_line_series) < signal_period:
        return {
            "macd_line": None, "signal_line": None, "histogram": None,
            "signal": "insufficient_data",
            "parameters": {"fast": fast, "slow": slow, "signal": signal_period},
        }

    signal_line_series = _ema_series(macd_line_series, signal_period)

    macd_line = round(macd_line_series[-1], 4)
    signal_line = round(signal_line_series[-1], 4)
    histogram = round(macd_line - signal_line, 4)

    sig = "bullish" if histogram > 0 else "bearish"

    return {
        "macd_line": macd_line,
        "signal_line": signal_line,
        "histogram": histogram,
        "signal": sig,
        "parameters": {"fast": fast, "slow": slow, "signal": signal_period},
    }


def compute_bollinger_bands(closes: list[float], period: int = 20, std_dev: float = 2.0) -> dict:
    """Compute Bollinger Bands."""
    if len(closes) < period:
        return {
            "upper_band": None, "middle_band": None, "lower_band": None,
            "current_price": closes[-1] if closes else None,
            "bandwidth": None, "percent_b": None, "signal": "insufficient_data",
        }

    window = closes[-period:]
    middle = sum(window) / period
    variance = sum((x - middle) ** 2 for x in window) / period
    std = variance ** 0.5

    upper = round(middle + std_dev * std, 2)
    lower = round(middle - std_dev * std, 2)
    middle = round(middle, 2)
    current = closes[-1]

    bandwidth = round(upper - lower, 2)
    percent_b = round((current - lower) / (upper - lower), 4) if upper != lower else 0.5

    if current > upper:
        signal = "overbought"
    elif current < lower:
        signal = "oversold"
    else:
        signal = "neutral"

    return {
        "upper_band": upper,
        "middle_band": middle,
        "lower_band": lower,
        "current_price": round(current, 2),
        "bandwidth": bandwidth,
        "percent_b": percent_b,
        "signal": signal,
    }


def compute_atr(prices: list[dict], period: int = 14) -> dict:
    """Compute Average True Range from OHLCV data."""
    if len(prices) < period + 1:
        return {"atr": None, "period": period}

    true_ranges = []
    for i in range(1, len(prices)):
        high = prices[i]["high"]
        low = prices[i]["low"]
        prev_close = prices[i - 1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)

    # Initial ATR is simple average
    atr = sum(true_ranges[:period]) / period
    # Smoothed ATR
    for tr in true_ranges[period:]:
        atr = (atr * (period - 1) + tr) / period

    return {"atr": round(atr, 4), "period": period}


async def get_full_technicals(symbol: str) -> dict:
    """Fetch historical data and compute all technical indicators.

    Returns a comprehensive technical analysis summary with signals.
    """
    cache_key = f"technical_{symbol}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    hist = await historical.get_historical(symbol, period="1y", interval="1d")
    if "error" in hist:
        return {"symbol": symbol, "error": hist["error"], "source": "technical_analysis"}

    prices = hist.get("prices", [])
    if len(prices) < 30:
        return {
            "symbol": symbol,
            "error": f"Insufficient data ({len(prices)} points, need at least 30)",
            "source": "technical_analysis",
        }

    closes = _closes(prices)
    current_price = closes[-1]

    sma = compute_sma(closes)
    ema = compute_ema(closes)
    rsi = compute_rsi(closes)
    macd = compute_macd(closes)
    bollinger = compute_bollinger_bands(closes)
    atr = compute_atr(prices)

    # Aggregate signal
    signals = []
    if rsi.get("signal") == "overbought":
        signals.append("bearish")
    elif rsi.get("signal") == "oversold":
        signals.append("bullish")
    if macd.get("signal") == "bullish":
        signals.append("bullish")
    elif macd.get("signal") == "bearish":
        signals.append("bearish")
    if sma.get("signals", {}).get("golden_cross"):
        signals.append("bullish")
    elif sma.get("signals", {}).get("golden_cross") is False:
        signals.append("bearish")

    bullish = signals.count("bullish")
    bearish = signals.count("bearish")
    if bullish > bearish:
        overall = "bullish"
    elif bearish > bullish:
        overall = "bearish"
    else:
        overall = "neutral"

    result = {
        "symbol": symbol,
        "price": round(current_price, 2),
        "sma": sma,
        "ema": ema,
        "rsi": rsi,
        "macd": macd,
        "bollinger": bollinger,
        "atr": atr,
        "overall_signal": overall,
        "source": "computed from yahoo_finance data",
    }
    cache.set(cache_key, result, CACHE_TTL_HISTORY)
    return result
