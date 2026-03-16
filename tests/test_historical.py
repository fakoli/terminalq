"""Tests for terminalq.providers.historical — Yahoo Finance mocked."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from terminalq.providers import historical


@pytest.fixture(autouse=True)
def clear_caches(tmp_cache_dir):
    """Ensure every test starts with empty cache."""
    pass


def _make_price_df(rows: list[dict]) -> pd.DataFrame:
    """Create a DataFrame mimicking yfinance Ticker.history() output."""
    dates = pd.to_datetime([r["date"] for r in rows])
    df = pd.DataFrame(
        {
            "Open": [r["open"] for r in rows],
            "High": [r["high"] for r in rows],
            "Low": [r["low"] for r in rows],
            "Close": [r["close"] for r in rows],
            "Volume": [r["volume"] for r in rows],
        },
        index=dates,
    )
    return df


async def test_get_historical_success():
    """Successful historical fetch returns prices list."""
    raw_rows = [
        {"date": "2026-01-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1000000},
        {"date": "2026-01-02", "open": 100.5, "high": 102.0, "low": 100.0, "close": 101.5, "volume": 1200000},
    ]
    df = _make_price_df(raw_rows)

    mock_ticker = MagicMock()
    mock_ticker.history.return_value = df

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        result = await historical.get_historical("AAPL", period="1mo", interval="1d")

    assert result["symbol"] == "AAPL"
    assert result["data_points"] == 2
    assert len(result["prices"]) == 2
    assert result["prices"][0]["close"] == 100.5
    assert result["source"] == "yahoo_finance"


async def test_get_historical_empty():
    """Empty DataFrame returns an error dict."""
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        result = await historical.get_historical("INVALID")

    assert "error" in result
    assert result["symbol"] == "INVALID"


async def test_get_dividends_with_data():
    """Dividend data is parsed and metrics computed."""
    dates = pd.to_datetime(["2025-03-01", "2025-06-01", "2025-09-01", "2025-12-01"])
    div_series = pd.Series([0.24, 0.24, 0.24, 0.24], index=dates)

    mock_ticker = MagicMock()
    mock_ticker.dividends = div_series

    fast_info = {"lastPrice": 150.0}
    mock_ticker.fast_info = fast_info

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        result = await historical.get_dividends("AAPL", years=5)

    assert result["symbol"] == "AAPL"
    assert result["annual_dividend"] == 0.96
    assert len(result["dividends"]) == 4
    assert result["payout_frequency"] == "annual"  # 4 payments / 5 years = 0.8 >= 0.5
    assert result["source"] == "yahoo_finance"


async def test_get_dividends_no_data():
    """Symbol with no dividends returns empty list and zero annual."""
    mock_ticker = MagicMock()
    mock_ticker.dividends = pd.Series(dtype=float)

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        result = await historical.get_dividends("TSLA")

    assert result["symbol"] == "TSLA"
    assert result["dividends"] == []
    assert result["annual_dividend"] == 0.0
    assert result["payout_frequency"] == "none"


# ---------------------------------------------------------------------------
# Coverage gap: yfinance fails, Polygon fallback succeeds (historical)
# ---------------------------------------------------------------------------


@patch("terminalq.providers.historical.POLYGON_API_KEY", "test_key")
async def test_get_historical_yfinance_exception_polygon_fallback():
    """When yfinance raises an exception, Polygon fallback is used."""
    from unittest.mock import AsyncMock

    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = Exception("yfinance crashed")

    polygon_result = {
        "symbol": "AAPL",
        "period": "1y",
        "interval": "1d",
        "data_points": 1,
        "prices": [{"date": "2026-01-01", "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000000}],
        "source": "polygon.io",
    }

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        with patch(
            "terminalq.providers.polygon.get_historical",
            new_callable=AsyncMock,
            return_value=polygon_result,
        ):
            result = await historical.get_historical("AAPL", period="1y", interval="1d")

    assert result["source"] == "polygon.io (fallback)"
    assert result["data_points"] == 1
    assert result["symbol"] == "AAPL"


@patch("terminalq.providers.historical.POLYGON_API_KEY", "test_key")
async def test_get_historical_yfinance_empty_polygon_fallback():
    """When yfinance returns empty data, Polygon fallback is used."""
    from unittest.mock import AsyncMock

    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame()

    polygon_result = {
        "symbol": "AAPL",
        "period": "1y",
        "interval": "1d",
        "data_points": 2,
        "prices": [
            {"date": "2026-01-01", "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000000},
            {"date": "2026-01-02", "open": 101, "high": 102, "low": 100, "close": 101.5, "volume": 1100000},
        ],
        "source": "polygon.io",
    }

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        with patch(
            "terminalq.providers.polygon.get_historical",
            new_callable=AsyncMock,
            return_value=polygon_result,
        ):
            result = await historical.get_historical("AAPL")

    assert result["source"] == "polygon.io (fallback)"
    assert result["data_points"] == 2


# ---------------------------------------------------------------------------
# Coverage gap: both yfinance and Polygon fail (historical)
# ---------------------------------------------------------------------------


@patch("terminalq.providers.historical.POLYGON_API_KEY", "test_key")
async def test_get_historical_both_fail():
    """When both yfinance and Polygon fail, 'all_failed' error is returned."""
    from unittest.mock import AsyncMock

    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = Exception("yfinance crash")

    polygon_error = {
        "error": "HTTP 500",
        "symbol": "AAPL",
        "source": "polygon.io",
    }

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        with patch(
            "terminalq.providers.polygon.get_historical",
            new_callable=AsyncMock,
            return_value=polygon_error,
        ):
            result = await historical.get_historical("AAPL")

    assert "error" in result
    assert "All data sources failed" in result["error"]
    assert result["source"] == "all_failed"


@patch("terminalq.providers.historical.POLYGON_API_KEY", "")
async def test_get_historical_yfinance_fails_no_polygon_key():
    """When yfinance fails and no POLYGON_API_KEY, error is returned."""
    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = Exception("yfinance crash")

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        result = await historical.get_historical("AAPL")

    assert "error" in result
    assert "All data sources failed" in result["error"]
    assert result["source"] == "all_failed"


@patch("terminalq.providers.historical.POLYGON_API_KEY", "test_key")
async def test_get_historical_polygon_exception():
    """When Polygon raises an exception, 'all_failed' error is returned."""
    from unittest.mock import AsyncMock

    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = Exception("yfinance crash")

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        with patch(
            "terminalq.providers.polygon.get_historical",
            new_callable=AsyncMock,
            side_effect=Exception("Polygon exploded"),
        ):
            result = await historical.get_historical("AAPL")

    assert "error" in result
    assert "All data sources failed" in result["error"]
    assert result["source"] == "all_failed"


# ---------------------------------------------------------------------------
# Coverage gap: dividends fallback paths
# ---------------------------------------------------------------------------


@patch("terminalq.providers.historical.POLYGON_API_KEY", "test_key")
async def test_get_dividends_yfinance_exception_polygon_fallback():
    """When yfinance dividends raises an exception, Polygon fallback is used."""
    from unittest.mock import AsyncMock

    mock_ticker = MagicMock()
    mock_ticker.dividends = property(lambda self: (_ for _ in ()).throw(Exception("yfinance crash")))
    # Use side_effect on the Ticker to make dividends access raise
    type(mock_ticker).dividends = property(lambda self: (_ for _ in ()).throw(Exception("yfinance crash")))

    polygon_result = {
        "symbol": "AAPL",
        "dividends": [{"date": "2025-11-01", "amount": 0.25}],
        "annual_dividend": 1.00,
        "dividend_yield": None,
        "payout_frequency": "quarterly",
        "source": "polygon.io",
    }

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        with patch(
            "terminalq.providers.polygon.get_dividends",
            new_callable=AsyncMock,
            return_value=polygon_result,
        ):
            result = await historical.get_dividends("AAPL")

    assert result["source"] == "polygon.io (fallback)"
    assert result["annual_dividend"] == 1.00


@patch("terminalq.providers.historical.POLYGON_API_KEY", "test_key")
async def test_get_dividends_both_fail():
    """When both yfinance and Polygon dividends fail, 'all_failed' error."""
    from unittest.mock import AsyncMock

    mock_ticker = MagicMock()
    type(mock_ticker).dividends = property(lambda self: (_ for _ in ()).throw(Exception("yfinance crash")))

    polygon_error = {
        "error": "Connection failed",
        "symbol": "AAPL",
        "source": "polygon.io",
    }

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        with patch(
            "terminalq.providers.polygon.get_dividends",
            new_callable=AsyncMock,
            return_value=polygon_error,
        ):
            result = await historical.get_dividends("AAPL")

    assert "error" in result
    assert "All data sources failed" in result["error"]
    assert result["source"] == "all_failed"


@patch("terminalq.providers.historical.POLYGON_API_KEY", "")
async def test_get_dividends_yfinance_fails_no_polygon_key():
    """When yfinance dividends fails and no POLYGON_API_KEY, error returned."""
    mock_ticker = MagicMock()
    type(mock_ticker).dividends = property(lambda self: (_ for _ in ()).throw(Exception("yfinance crash")))

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        result = await historical.get_dividends("AAPL")

    assert "error" in result
    assert "All data sources failed" in result["error"]
    assert result["source"] == "all_failed"


@patch("terminalq.providers.historical.POLYGON_API_KEY", "test_key")
async def test_get_dividends_polygon_exception():
    """When Polygon dividends raises an exception, 'all_failed' returned."""
    from unittest.mock import AsyncMock

    mock_ticker = MagicMock()
    type(mock_ticker).dividends = property(lambda self: (_ for _ in ()).throw(Exception("yfinance crash")))

    with patch("terminalq.providers.historical.yfinance.Ticker", return_value=mock_ticker):
        with patch(
            "terminalq.providers.polygon.get_dividends",
            new_callable=AsyncMock,
            side_effect=Exception("Polygon exploded"),
        ):
            result = await historical.get_dividends("AAPL")

    assert "error" in result
    assert "All data sources failed" in result["error"]
    assert result["source"] == "all_failed"
