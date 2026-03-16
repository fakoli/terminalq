"""Tests for terminalq.providers.edgar — SEC EDGAR with mocked HTTP."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from terminalq.providers import edgar


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


async def test_resolve_cik():
    """CIK resolution finds the correct zero-padded CIK for a ticker."""
    tickers_json = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc"},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    }

    mock_client = AsyncMock()
    mock_client.get.return_value = _mock_response(tickers_json)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.edgar.httpx.AsyncClient", return_value=mock_client):
        cik = await edgar._resolve_cik("AAPL")

    assert cik == "0000320193"


async def test_get_financials():
    """get_financials returns structured income statement data."""
    tickers_json = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc"},
    }
    company_facts = {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {
                        "USD": [
                            {"end": "2025-09-30", "val": 394000000000, "form": "10-K", "fy": 2025, "filed": "2025-10-30"},
                            {"end": "2024-09-30", "val": 383000000000, "form": "10-K", "fy": 2024, "filed": "2024-10-30"},
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {"end": "2025-09-30", "val": 97000000000, "form": "10-K", "fy": 2025, "filed": "2025-10-30"},
                            {"end": "2024-09-30", "val": 94000000000, "form": "10-K", "fy": 2024, "filed": "2024-10-30"},
                        ]
                    }
                },
            }
        }
    }

    call_count = 0

    async def mock_get(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if "company_tickers" in url:
            return _mock_response(tickers_json)
        else:
            return _mock_response(company_facts)

    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.edgar.httpx.AsyncClient", return_value=mock_client):
        result = await edgar.get_financials("AAPL", statement="income", periods=2)

    assert result["symbol"] == "AAPL"
    assert result["statement"] == "income"
    assert len(result["periods"]) == 2
    assert result["periods"][0]["revenue"] == 394000000000
    assert result["source"] == "sec_edgar"


async def test_get_filings():
    """get_filings returns structured filing list."""
    tickers_json = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc"},
    }
    submissions_data = {
        "name": "Apple Inc",
        "filings": {
            "recent": {
                "form": ["10-K", "10-Q", "8-K"],
                "filingDate": ["2025-10-30", "2025-07-30", "2025-06-15"],
                "primaryDocDescription": ["Annual Report", "Quarterly Report", "Current Report"],
                "accessionNumber": ["0001-23-456789", "0001-23-456790", "0001-23-456791"],
                "primaryDocument": ["doc1.htm", "doc2.htm", "doc3.htm"],
            }
        },
    }

    async def mock_get(url, **kwargs):
        if "company_tickers" in url:
            return _mock_response(tickers_json)
        else:
            return _mock_response(submissions_data)

    mock_client = AsyncMock()
    mock_client.get = mock_get
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("terminalq.providers.edgar.httpx.AsyncClient", return_value=mock_client):
        result = await edgar.get_filings("AAPL", filing_type="10-K", limit=5)

    assert result["symbol"] == "AAPL"
    assert result["company_name"] == "Apple Inc"
    assert len(result["filings"]) == 1  # Only the 10-K
    assert result["filings"][0]["type"] == "10-K"


async def test_unknown_statement_type():
    """Unknown statement type returns error without making HTTP calls."""
    result = await edgar.get_financials("AAPL", statement="unknown_type")
    assert "error" in result
    assert "Unknown statement type" in result["error"]
