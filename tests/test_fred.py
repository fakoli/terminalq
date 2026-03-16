"""Tests for terminalq.providers.fred — FRED economic data with mocked HTTP."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from terminalq.providers import fred


@pytest.fixture(autouse=True)
def clear_caches(tmp_cache_dir):
    """Ensure every test starts with empty cache."""
    pass


def _mock_response(json_data, status_code=200):
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.text = ""
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    return resp


async def test_get_series(monkeypatch):
    """get_series returns structured observations."""
    monkeypatch.setattr("terminalq.providers.fred.FRED_API_KEY", "test_key_123")

    obs_data = {
        "observations": [
            {"date": "2026-02-01", "value": "3.2"},
            {"date": "2026-01-01", "value": "3.1"},
        ]
    }
    info_data = {"seriess": [{"title": "Consumer Price Index", "frequency": "Monthly", "units": "Index 1982-1984=100"}]}

    async def mock_get(url, **kwargs):
        if "observations" in url:
            return _mock_response(obs_data)
        else:
            return _mock_response(info_data)

    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.fred.httpx.AsyncClient", return_value=mock_client):
        result = await fred.get_series("CPIAUCSL", limit=2)

    assert result["series_id"] == "CPIAUCSL"
    assert result["title"] == "Consumer Price Index"
    assert result["latest_value"] == 3.2
    assert len(result["observations"]) == 2
    assert result["source"] == "fred"


async def test_alias_resolution(monkeypatch):
    """Human-friendly aliases resolve to FRED series IDs."""
    monkeypatch.setattr("terminalq.providers.fred.FRED_API_KEY", "test_key_123")

    obs_data = {"observations": [{"date": "2026-01-01", "value": "27000"}]}
    info_data = {"seriess": [{"title": "GDP", "frequency": "Quarterly", "units": "Billions of Dollars"}]}

    async def mock_get(url, **kwargs):
        if "observations" in url:
            return _mock_response(obs_data)
        return _mock_response(info_data)

    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.fred.httpx.AsyncClient", return_value=mock_client):
        result = await fred.get_series("gdp", limit=1)

    # "gdp" should resolve to "GDP" series ID
    assert result["series_id"] == "GDP"


async def test_missing_key(monkeypatch):
    """Missing FRED_API_KEY returns an error dict."""
    monkeypatch.setattr("terminalq.providers.fred.FRED_API_KEY", "")

    result = await fred.get_series("GDP")
    assert "error" in result
    assert "FRED_API_KEY" in result["error"]


async def test_dashboard(monkeypatch):
    """Dashboard fetches multiple indicators and aggregates them."""
    monkeypatch.setattr("terminalq.providers.fred.FRED_API_KEY", "test_key_123")

    obs_data = {
        "observations": [
            {"date": "2026-02-01", "value": "5.0"},
            {"date": "2026-01-01", "value": "4.5"},
        ]
    }
    info_data = {"seriess": [{"title": "Test", "frequency": "Monthly", "units": "Percent"}]}

    async def mock_get(url, **kwargs):
        if "observations" in url:
            return _mock_response(obs_data)
        return _mock_response(info_data)

    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.fred.httpx.AsyncClient", return_value=mock_client):
        result = await fred.get_economic_dashboard()

    assert "indicators" in result
    assert result["source"] == "fred"
    # Should have entries for each dashboard alias
    assert "gdp" in result["indicators"]
    assert "unemployment" in result["indicators"]
    # Check computed change
    gdp = result["indicators"]["gdp"]
    assert gdp["latest_value"] == 5.0
    assert gdp["previous_value"] == 4.5
    assert gdp["change"] == 0.5


async def test_dot_value_skip(monkeypatch):
    """Observations with value '.' are skipped."""
    monkeypatch.setattr("terminalq.providers.fred.FRED_API_KEY", "test_key_123")

    obs_data = {
        "observations": [
            {"date": "2026-03-01", "value": "."},
            {"date": "2026-02-01", "value": "4.5"},
            {"date": "2026-01-01", "value": "."},
        ]
    }
    info_data = {"seriess": [{"title": "Daily Rate", "frequency": "Daily", "units": "Percent"}]}

    async def mock_get(url, **kwargs):
        if "observations" in url:
            return _mock_response(obs_data)
        return _mock_response(info_data)

    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.fred.httpx.AsyncClient", return_value=mock_client):
        result = await fred.get_series("DFF", limit=3)

    # Only 1 observation should remain (the two "." entries skipped)
    assert len(result["observations"]) == 1
    assert result["observations"][0]["value"] == 4.5
    assert result["latest_value"] == 4.5
