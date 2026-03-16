import pytest
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx


@pytest.fixture
def tmp_cache_dir(tmp_path, monkeypatch):
    """Provide isolated cache directory."""
    monkeypatch.setattr("terminalq.cache.CACHE_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def sample_ohlcv():
    """30 days of sample OHLCV data."""
    return [
        {
            "date": f"2026-01-{i + 1:02d}",
            "open": 100 + i * 0.5,
            "high": 101 + i * 0.5,
            "low": 99.5 + i * 0.5,
            "close": 100.5 + i * 0.5,
            "volume": 1000000,
        }
        for i in range(30)
    ]


@pytest.fixture
def mock_httpx_get():
    """Factory for mocking httpx.AsyncClient.get responses."""

    def _make_response(status_code: int = 200, json_data=None, text_data: str = ""):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status_code
        resp.json.return_value = json_data if json_data is not None else {}
        resp.text = text_data or json.dumps(json_data) if json_data else text_data
        resp.raise_for_status = MagicMock()
        if status_code >= 400:
            resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                f"HTTP {status_code}",
                request=MagicMock(),
                response=resp,
            )
        return resp

    return _make_response
