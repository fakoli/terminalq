"""Tests for terminalq.providers.technical — pure computation indicators."""
import pytest

from terminalq.providers.technical import (
    compute_sma,
    compute_ema,
    compute_rsi,
    compute_macd,
    compute_bollinger_bands,
    compute_atr,
)


def test_sma_basic():
    """SMA of [1,2,3,4,5] with period=3 should be 4.0 (avg of last 3)."""
    closes = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = compute_sma(closes, periods=[3])
    assert result["sma_3"] == 4.0  # (3+4+5)/3


def test_sma_signals():
    """Price above SMA signals True, below signals False."""
    # Current price (last element) is 10, SMA of 5 values centered around 5
    closes = [1.0, 2.0, 3.0, 4.0, 10.0]
    result = compute_sma(closes, periods=[5])
    # SMA_5 = (1+2+3+4+10)/5 = 4.0, current=10 > 4 => above_sma_5 = True
    assert result["signals"]["above_sma_5"] is True

    # Current price below SMA
    closes_low = [10.0, 9.0, 8.0, 7.0, 1.0]
    result_low = compute_sma(closes_low, periods=[5])
    # SMA_5 = (10+9+8+7+1)/5 = 7.0, current=1 < 7 => above_sma_5 = False
    assert result_low["signals"]["above_sma_5"] is False


def test_ema_basic():
    """EMA calculation matches expected formula."""
    closes = [22.0, 22.5, 23.0, 22.8, 23.2, 23.5, 23.8, 24.0, 24.2, 24.5]
    result = compute_ema(closes, periods=[5])
    # EMA_5: initial SMA = (22+22.5+23+22.8+23.2)/5 = 22.7
    # multiplier = 2/(5+1) = 0.333...
    # Then apply for closes[5:] = [23.5, 23.8, 24.0, 24.2, 24.5]
    # Step by step:
    sma = sum(closes[:5]) / 5  # 22.7
    mult = 2 / 6
    ema = sma
    for price in closes[5:]:
        ema = (price - ema) * mult + ema
    expected = round(ema, 2)
    assert result["ema_5"] == expected


def test_rsi_overbought():
    """Monotonically rising prices produce RSI near 100 (overbought)."""
    # 30 points of strictly rising prices
    closes = [float(i) for i in range(1, 31)]
    result = compute_rsi(closes, period=14)
    assert result["rsi"] is not None
    assert result["rsi"] >= 90
    assert result["signal"] == "overbought"


def test_rsi_oversold():
    """Monotonically falling prices produce RSI near 0 (oversold)."""
    closes = [float(100 - i) for i in range(30)]
    result = compute_rsi(closes, period=14)
    assert result["rsi"] is not None
    assert result["rsi"] <= 10
    assert result["signal"] == "oversold"


def test_rsi_neutral():
    """Mixed up-and-down data should produce RSI between 30 and 70."""
    # Alternating up/down pattern
    closes = []
    price = 100.0
    for i in range(30):
        if i % 2 == 0:
            price += 1.0
        else:
            price -= 0.8
        closes.append(price)

    result = compute_rsi(closes, period=14)
    assert result["rsi"] is not None
    assert 30 <= result["rsi"] <= 70
    assert result["signal"] == "neutral"


def test_macd_bullish():
    """Accelerating uptrend produces positive MACD histogram (bullish)."""
    # Flat then sharply rising — fast EMA reacts quicker than slow EMA
    closes = [100.0] * 30 + [100.0 + (i ** 1.5) for i in range(1, 21)]
    result = compute_macd(closes)
    assert result["histogram"] is not None
    assert result["histogram"] > 0
    assert result["signal"] == "bullish"


def test_macd_insufficient():
    """Fewer than 35 data points returns insufficient_data."""
    closes = [100.0 + i for i in range(20)]
    result = compute_macd(closes)
    assert result["signal"] == "insufficient_data"
    assert result["macd_line"] is None


def test_bollinger_within_bands():
    """For data with moderate variance, %B should be between 0 and 1."""
    # 30 points with slight variation around 100
    closes = [100.0 + (i % 5) * 0.5 - 1.0 for i in range(30)]
    result = compute_bollinger_bands(closes, period=20)
    assert result["percent_b"] is not None
    assert 0 <= result["percent_b"] <= 1
    assert result["signal"] == "neutral"
    assert result["upper_band"] > result["middle_band"] > result["lower_band"]


def test_atr_constant():
    """When high-low range is constant and close equals previous close, ATR equals that range."""
    # Build OHLCV where every bar has range of exactly 2.0
    # and close equals the same value each day
    prices = []
    for i in range(20):
        prices.append({
            "date": f"2026-01-{i + 1:02d}",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.0,
            "volume": 1000000,
        })

    result = compute_atr(prices, period=14)
    assert result["atr"] is not None
    # True range each day: max(101-99, |101-100|, |99-100|) = max(2, 1, 1) = 2.0
    assert abs(result["atr"] - 2.0) < 0.01
