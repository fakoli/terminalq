"""Tests for terminalq.providers.finnhub — quote & profile with mocked HTTP."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from terminalq.providers import finnhub


@pytest.fixture(autouse=True)
def clear_caches(tmp_cache_dir):
    """Ensure every test starts with empty cache."""
    pass


def _mock_response(json_data, status_code=200):
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=MagicMock(), response=resp,
        )
    return resp


async def test_get_quote():
    """get_quote returns structured result from Finnhub API response."""
    api_data = {
        "c": 150.25, "d": 1.5, "dp": 1.01,
        "h": 151.0, "l": 149.0, "o": 149.5, "pc": 148.75, "t": 1700000000,
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_response(api_data)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.finnhub.httpx.AsyncClient", return_value=mock_client):
        with patch.object(finnhub._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await finnhub.get_quote("AAPL")

    assert result["symbol"] == "AAPL"
    assert result["current_price"] == 150.25
    assert result["change"] == 1.5
    assert result["source"] == "finnhub"


async def test_get_quotes_batch_cached_and_uncached(tmp_cache_dir):
    """Batch quotes use cache for known symbols and fetch the rest."""
    from terminalq import cache

    # Pre-cache AAPL
    cache.set("finnhub_quote_AAPL", {
        "symbol": "AAPL", "current_price": 150.0, "source": "finnhub",
    }, ttl=300)

    api_data = {
        "c": 300.0, "d": 2.0, "dp": 0.67,
        "h": 301.0, "l": 299.0, "o": 299.5, "pc": 298.0,
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_response(api_data)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.finnhub.httpx.AsyncClient", return_value=mock_client):
        with patch.object(finnhub._rate_limiter, "acquire", new_callable=AsyncMock):
            results = await finnhub.get_quotes_batch(["AAPL", "MSFT"])

    assert len(results) == 2
    # AAPL should come from cache
    assert results[0]["symbol"] == "AAPL"
    assert results[0]["current_price"] == 150.0
    # MSFT should be fetched
    assert results[1]["symbol"] == "MSFT"
    assert results[1]["current_price"] == 300.0


async def test_get_company_profile():
    """get_company_profile returns structured company data."""
    api_data = {
        "name": "Apple Inc",
        "exchange": "NASDAQ",
        "finnhubIndustry": "Technology",
        "marketCapitalization": 2800000,
        "shareOutstanding": 15000,
        "logo": "https://logo.url",
        "weburl": "https://apple.com",
        "ipo": "1980-12-12",
        "country": "US",
        "currency": "USD",
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_response(api_data)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.finnhub.httpx.AsyncClient", return_value=mock_client):
        with patch.object(finnhub._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await finnhub.get_company_profile("AAPL")

    assert result["symbol"] == "AAPL"
    assert result["name"] == "Apple Inc"
    assert result["market_cap"] == 2800000
    assert result["source"] == "finnhub"


async def test_error_handling():
    """HTTP errors return a dict with error key."""
    mock_client = AsyncMock()
    error_resp = _mock_response({}, status_code=403)
    mock_client.get.return_value = error_resp
    mock_client.get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "403", request=MagicMock(), response=error_resp,
    )
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.finnhub.httpx.AsyncClient", return_value=mock_client):
        with patch.object(finnhub._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await finnhub.get_quote("BAD")

    assert "error" in result
    assert result["source"] == "finnhub"


async def test_timeout_handling():
    """Timeout returns a dict with error key."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.TimeoutException("timed out")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.finnhub.httpx.AsyncClient", return_value=mock_client):
        with patch.object(finnhub._rate_limiter, "acquire", new_callable=AsyncMock):
            result = await finnhub.get_quote("SLOW")

    assert "error" in result
    assert "timed out" in result["error"].lower()


async def test_all_cached_batch(tmp_cache_dir):
    """When all symbols are cached, no HTTP calls are made."""
    from terminalq import cache

    cache.set("finnhub_quote_AAPL", {"symbol": "AAPL", "current_price": 150.0, "source": "finnhub"}, ttl=300)
    cache.set("finnhub_quote_GOOG", {"symbol": "GOOG", "current_price": 140.0, "source": "finnhub"}, ttl=300)

    # No need to mock httpx at all — should never be called
    results = await finnhub.get_quotes_batch(["AAPL", "GOOG"])
    assert len(results) == 2
    assert results[0]["current_price"] == 150.0
    assert results[1]["current_price"] == 140.0
