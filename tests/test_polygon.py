"""Tests for terminalq.providers.polygon — Polygon.io fallback provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from terminalq.providers import polygon


@pytest.fixture(autouse=True)
def clear_caches(tmp_cache_dir):
    """Ensure every test starts with empty cache."""
    pass


def _mock_aggs_response():
    """Mock Polygon aggregates response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = {
        "results": [
            {"t": 1704067200000, "o": 185.0, "h": 186.0, "l": 184.0, "c": 185.5, "v": 50000000},
            {"t": 1704153600000, "o": 185.5, "h": 187.0, "l": 185.0, "c": 186.5, "v": 45000000},
        ],
        "resultsCount": 2,
    }
    resp.raise_for_status = MagicMock()
    return resp


def _mock_dividends_response():
    """Mock Polygon dividends response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = {
        "results": [
            {"ex_dividend_date": "2025-11-01", "cash_amount": 0.25},
            {"ex_dividend_date": "2025-08-01", "cash_amount": 0.25},
            {"ex_dividend_date": "2025-05-01", "cash_amount": 0.24},
            {"ex_dividend_date": "2025-02-01", "cash_amount": 0.24},
        ]
    }
    resp.raise_for_status = MagicMock()
    return resp


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_get_historical_success():
    """Successful historical data fetch returns prices."""
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_aggs_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_historical("AAPL", "1y", "1d")

    assert result["symbol"] == "AAPL"
    assert result["data_points"] == 2
    assert len(result["prices"]) == 2
    assert result["source"] == "polygon.io"


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "")
async def test_no_api_key():
    """Returns error when no API key configured."""
    result = await polygon.get_historical("AAPL")
    assert "error" in result
    assert "POLYGON_API_KEY" in result["error"]


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_get_dividends_success():
    """Successful dividend data fetch."""
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_dividends_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_dividends("AAPL", years=5)

    assert result["symbol"] == "AAPL"
    assert len(result["dividends"]) == 4
    assert result["annual_dividend"] == 0.98
    assert result["source"] == "polygon.io"


# ---------------------------------------------------------------------------
# Coverage gap: HTTP errors for get_historical (lines 63-71)
# ---------------------------------------------------------------------------


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_get_historical_timeout():
    """Timeout returns error dict."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.TimeoutException("timed out")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_historical("AAPL")

    assert "error" in result
    assert "timed out" in result["error"]
    assert result["source"] == "polygon.io"


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_get_historical_http_error():
    """HTTP status error returns error dict."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 403
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("Forbidden", request=MagicMock(), response=mock_resp)

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_historical("AAPL")

    assert "error" in result
    assert "403" in result["error"]


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_get_historical_connect_error():
    """Connection error returns error dict."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_historical("AAPL")

    assert "error" in result
    assert "Connection failed" in result["error"]


# ---------------------------------------------------------------------------
# Coverage gap: Dividend HTTP errors (lines 124-132)
# ---------------------------------------------------------------------------


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_get_dividends_timeout():
    """Dividend timeout returns error dict."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.TimeoutException("timed out")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_dividends("AAPL")

    assert "error" in result
    assert "timed out" in result["error"]


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_get_dividends_http_error():
    """Dividend HTTP status error returns error dict."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 500
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=MagicMock(), response=mock_resp
    )

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_dividends("AAPL")

    assert "error" in result
    assert "500" in result["error"]


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_get_dividends_connect_error():
    """Dividend connection error returns error dict."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_dividends("AAPL")

    assert "error" in result
    assert "Connection failed" in result["error"]


# ---------------------------------------------------------------------------
# Coverage gap: No API key for dividends (line 106)
# ---------------------------------------------------------------------------


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "")
async def test_get_dividends_no_api_key():
    """Returns error when no API key configured for dividends."""
    result = await polygon.get_dividends("AAPL")
    assert "error" in result
    assert "POLYGON_API_KEY" in result["error"]


# ---------------------------------------------------------------------------
# Coverage gap: Empty results from Polygon (line 74-75)
# ---------------------------------------------------------------------------


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_get_historical_empty_results():
    """Empty results array returns error."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": [], "resultsCount": 0}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_historical("AAPL")

    assert "error" in result
    assert "No data" in result["error"]


# ---------------------------------------------------------------------------
# Coverage gap: Dividend edge cases — payout frequency branches (lines 159-167)
# ---------------------------------------------------------------------------


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_dividends_payout_monthly():
    """Monthly payout frequency when >= 11 payments per year."""
    from datetime import datetime, timedelta

    # Generate 12 monthly dividends over 1 year
    base = datetime.now()
    divs = []
    for i in range(12):
        d = base - timedelta(days=30 * i)
        divs.append({"ex_dividend_date": d.strftime("%Y-%m-%d"), "cash_amount": 0.10})

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": divs}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_dividends("REALTY", years=1)

    assert result["payout_frequency"] == "monthly"


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_dividends_payout_semi_annual():
    """Semi-annual frequency when 1.5 <= payments_per_year < 3.5."""
    from datetime import datetime, timedelta

    base = datetime.now()
    divs = [
        {"ex_dividend_date": (base - timedelta(days=30)).strftime("%Y-%m-%d"), "cash_amount": 0.50},
        {"ex_dividend_date": (base - timedelta(days=210)).strftime("%Y-%m-%d"), "cash_amount": 0.50},
    ]

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": divs}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_dividends("SEMI", years=1)

    assert result["payout_frequency"] == "semi-annual"


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_dividends_payout_annual():
    """Annual frequency when 0.5 <= payments_per_year < 1.5."""
    from datetime import datetime, timedelta

    divs = [
        {"ex_dividend_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"), "cash_amount": 1.00},
    ]

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": divs}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_dividends("ANNUAL", years=1)

    assert result["payout_frequency"] == "annual"


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_dividends_payout_irregular():
    """Irregular frequency when payments_per_year < 0.5 but dividends exist."""
    from datetime import datetime, timedelta

    # 1 dividend in 5 years = 0.2 payments_per_year
    divs = [
        {"ex_dividend_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"), "cash_amount": 1.00},
    ]

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": divs}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_dividends("IRREG", years=5)

    assert result["payout_frequency"] == "irregular"


@patch("terminalq.providers.polygon.POLYGON_API_KEY", "test_key")
async def test_dividends_payout_none():
    """'none' frequency when no dividends found."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"results": []}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.polygon.httpx.AsyncClient", return_value=mock_client):
        with patch.object(polygon._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await polygon.get_dividends("NODIV", years=5)

    assert result["payout_frequency"] == "none"
    assert result["dividends"] == []
