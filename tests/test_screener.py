"""Tests for terminalq.providers.screener — S&P 500 screener with mocked HTTP."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from terminalq.providers import screener


@pytest.fixture(autouse=True)
def clear_caches(tmp_cache_dir):
    """Ensure every test starts with empty cache."""
    pass


_SAMPLE_CSV = """\
Symbol,Name,Sector
AAPL,Apple Inc,Information Technology
MSFT,Microsoft Corporation,Information Technology
JNJ,Johnson & Johnson,Health Care
UNH,UnitedHealth Group,Health Care
XOM,Exxon Mobil Corporation,Energy
JPM,JPMorgan Chase & Co,Financials
"""


def _mock_csv_response(csv_text=_SAMPLE_CSV, status_code=200):
    """Create a mock httpx.Response for the CSV endpoint."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = csv_text
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    return resp


async def test_component_parsing():
    """CSV is parsed into component dicts with symbol, name, sector."""
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_csv_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.screener.httpx.AsyncClient", return_value=mock_client):
        components = await screener.get_sp500_components()

    assert len(components) == 6
    assert components[0]["symbol"] == "AAPL"
    assert components[0]["name"] == "Apple Inc"
    assert components[0]["sector"] == "Information Technology"


async def test_sector_filter():
    """screen_stocks filters by sector (case-insensitive partial match)."""
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_csv_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.screener.httpx.AsyncClient", return_value=mock_client):
        result = await screener.screen_stocks(sector="Health Care")

    assert result["matches_after_sector"] == 2
    symbols = [r["symbol"] for r in result["results"]]
    assert "JNJ" in symbols
    assert "UNH" in symbols
    assert "AAPL" not in symbols


async def test_case_insensitive_sector():
    """Sector filter works with different casing."""
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_csv_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.screener.httpx.AsyncClient", return_value=mock_client):
        result = await screener.screen_stocks(sector="energy")

    assert result["matches_after_sector"] == 1
    assert result["results"][0]["symbol"] == "XOM"


async def test_market_cap_filter():
    """Numeric market_cap filter applies when sector set is small enough."""
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_csv_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    # Mock finnhub profiles for the filtered symbols
    async def mock_profile(sym):
        profiles = {
            "AAPL": {"market_cap": 3000000, "industry": "Technology"},
            "MSFT": {"market_cap": 2800000, "industry": "Technology"},
        }
        return profiles.get(sym, {"error": "not found"})

    with patch("terminalq.providers.screener.httpx.AsyncClient", return_value=mock_client):
        with patch("terminalq.providers.screener.finnhub.get_company_profile", side_effect=mock_profile):
            result = await screener.screen_stocks(
                sector="Information Technology",
                min_market_cap=2900000,
            )

    # Only AAPL has market_cap >= 2900000
    assert result["matches_after_all_filters"] == 1
    assert result["results"][0]["symbol"] == "AAPL"
    assert result["filters_applied"]["min_market_cap"] == 2900000
