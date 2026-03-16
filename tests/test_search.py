"""Tests for terminalq.providers.search — Brave Search web search."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from terminalq.providers import search


@pytest.fixture(autouse=True)
def clear_caches(tmp_cache_dir):
    """Ensure every test starts with empty cache."""
    pass


@pytest.fixture(autouse=True)
def reset_usage(tmp_path, monkeypatch):
    """Isolate usage tracking to a temp dir."""
    monkeypatch.setattr("terminalq.usage_tracker._USAGE_DIR", tmp_path / "usage")
    return tmp_path / "usage"


def _mock_brave_response():
    """Mock a successful Brave Search API response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.json.return_value = {
        "web": {
            "results": [
                {
                    "title": "Apple Inc Stock",
                    "url": "https://example.com/aapl",
                    "description": "Latest AAPL info",
                    "age": "2 hours ago",
                },
                {
                    "title": "AAPL News",
                    "url": "https://example.com/aapl-news",
                    "description": "Breaking news about Apple",
                    "age": "1 hour ago",
                },
            ]
        },
        "news": {
            "results": [
                {
                    "title": "Apple Earnings",
                    "url": "https://news.example.com/aapl",
                    "description": "Q4 earnings report",
                    "age": "30 minutes ago",
                    "meta_url": {"hostname": "news.example.com"},
                }
            ]
        },
    }
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


@patch("terminalq.providers.search.BRAVE_API_KEY", "test_brave_key")
async def test_web_search_success():
    """Successful search returns results and news."""
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_brave_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.search.httpx.AsyncClient", return_value=mock_client):
        result = await search.web_search("AAPL stock")

    assert result["query"] == "AAPL stock"
    assert result["total_results"] == 2
    assert len(result["results"]) == 2
    assert result["results"][0]["title"] == "Apple Inc Stock"
    assert len(result["news"]) == 1
    assert result["source"] == "brave_search"
    assert "usage" in result


# ---------------------------------------------------------------------------
# No API key
# ---------------------------------------------------------------------------


@patch("terminalq.providers.search.BRAVE_API_KEY", "")
async def test_web_search_no_api_key():
    """Returns error when BRAVE_API_KEY is not configured."""
    result = await search.web_search("test query")
    assert "error" in result
    assert "BRAVE_API_KEY" in result["error"]
    assert result["source"] == "brave_search"


# ---------------------------------------------------------------------------
# Cache hit
# ---------------------------------------------------------------------------


@patch("terminalq.providers.search.BRAVE_API_KEY", "test_brave_key")
async def test_web_search_cache_hit():
    """Second call uses cached result."""
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_brave_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.search.httpx.AsyncClient", return_value=mock_client):
        result1 = await search.web_search("cached query", count=5)
        result2 = await search.web_search("cached query", count=5)

    assert result1["query"] == "cached query"
    assert result2["query"] == "cached query"
    # httpx client should only have been called once (second is cached)
    assert mock_client.get.call_count == 1


# ---------------------------------------------------------------------------
# Budget exceeded
# ---------------------------------------------------------------------------


@patch("terminalq.providers.search.BRAVE_API_KEY", "test_brave_key")
async def test_web_search_budget_exceeded():
    """Returns error when monthly budget is exceeded."""
    with patch("terminalq.providers.search.usage_tracker.check_budget", return_value=False):
        with patch(
            "terminalq.providers.search.usage_tracker.get_monthly_usage",
            return_value={"calls_used": 2000, "calls_limit": 2000, "remaining": 0},
        ):
            result = await search.web_search("over budget query")

    assert "error" in result
    assert "monthly limit" in result["error"].lower() or "limit reached" in result["error"]
    assert result["source"] == "brave_search"


# ---------------------------------------------------------------------------
# HTTP errors
# ---------------------------------------------------------------------------


@patch("terminalq.providers.search.BRAVE_API_KEY", "test_brave_key")
async def test_web_search_timeout():
    """Timeout returns error dict."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.TimeoutException("timed out")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.search.httpx.AsyncClient", return_value=mock_client):
        result = await search.web_search("timeout query")

    assert "error" in result
    assert "timed out" in result["error"]
    assert result["source"] == "brave_search"


@patch("terminalq.providers.search.BRAVE_API_KEY", "test_brave_key")
async def test_web_search_http_error():
    """HTTP status error returns error dict."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Rate limited", request=MagicMock(), response=mock_resp
    )

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.search.httpx.AsyncClient", return_value=mock_client):
        result = await search.web_search("rate limited query")

    assert "error" in result
    assert "429" in result["error"]
    assert result["source"] == "brave_search"


@patch("terminalq.providers.search.BRAVE_API_KEY", "test_brave_key")
async def test_web_search_connect_error():
    """Connection error returns error dict."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.ConnectError("Connection refused")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.search.httpx.AsyncClient", return_value=mock_client):
        result = await search.web_search("connect fail query")

    assert "error" in result
    assert "Connection failed" in result["error"]
    assert result["source"] == "brave_search"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@patch("terminalq.providers.search.BRAVE_API_KEY", "test_brave_key")
async def test_web_search_empty_results():
    """Empty search results return zero total."""
    empty_resp = MagicMock(spec=httpx.Response)
    empty_resp.status_code = 200
    empty_resp.json.return_value = {"web": {"results": []}, "news": {"results": []}}
    empty_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = empty_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.search.httpx.AsyncClient", return_value=mock_client):
        result = await search.web_search("obscure query nobody searches")

    assert result["total_results"] == 0
    assert result["results"] == []
    assert result["news"] == []


@patch("terminalq.providers.search.BRAVE_API_KEY", "test_brave_key")
async def test_web_search_count_clamped():
    """Count is clamped to max 20."""
    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_brave_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.search.httpx.AsyncClient", return_value=mock_client):
        result = await search.web_search("clamped query", count=50)

    # Should still succeed (count is clamped internally)
    assert result["source"] == "brave_search"
    # Verify the API was called with count=20 (clamped from 50)
    call_kwargs = mock_client.get.call_args
    assert call_kwargs[1]["params"]["count"] == 20
