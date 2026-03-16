"""Tests for terminalq.providers.portfolio — holdings parsing."""
import pytest
from pathlib import Path
from unittest.mock import patch

from terminalq.providers.portfolio import (
    _parse_holdings_md,
    _parse_dollar,
    load_rsu_schedule,
    get_unique_symbols,
)


@pytest.fixture
def holdings_md(tmp_path):
    """Create a sample portfolio-holdings.md file."""
    content = """\
# Portfolio Holdings (as of Feb 28, 2026)

## Brokerage Account

| Symbol | Name | Shares | Cost Basis | Market Value | Unrealized G/L |
|--------|------|--------|------------|--------------|----------------|
| AAPL | Apple Inc | 100 | $15,000.00 | $17,500.00 | $2,500.00 |
| MSFT | Microsoft Corp | 50 | $10,000.00 | $12,000.00 | $2,000.00 |
| GOOG | Alphabet Inc | 25 | $3,500.00 | $4,000.00 | $500.00 |

## Retirement Account

| Symbol | Name | Shares | Cost Basis | Market Value | Unrealized G/L |
|--------|------|--------|------------|--------------|----------------|
| VTI | Vanguard Total Stock | 200 | $40,000.00 | $50,000.00 | $10,000.00 |
| AAPL | Apple Inc | 30 | $4,500.00 | $5,250.00 | $750.00 |
"""
    path = tmp_path / "portfolio-holdings.md"
    path.write_text(content)
    return path


@pytest.fixture
def rsu_md(tmp_path):
    """Create a sample rsu-schedule.md file."""
    content = """\
# RSU Schedule

| Date | Grant | Pct of Grant | Est Value |
|------|-------|--------------|-----------|
| 2026-06-20 | 2026 Grant | 16.67% | $125,000 |
| 2026-09-20 | 2026 Grant | 16.67% | $125,000 |
"""
    path = tmp_path / "rsu-schedule.md"
    path.write_text(content)
    return path


def test_parse_valid_holdings(holdings_md):
    """Parse a valid holdings markdown file."""
    holdings, as_of = _parse_holdings_md(holdings_md)
    assert len(holdings) == 5
    assert as_of == "Feb 28, 2026"

    # Check first holding
    aapl = holdings[0]
    assert aapl["symbol"] == "AAPL"
    assert aapl["shares"] == 100.0
    assert aapl["market_value"] == 17500.00
    assert aapl["account"] == "Brokerage Account"

    # Check retirement account holding
    vti = holdings[3]
    assert vti["symbol"] == "VTI"
    assert vti["account"] == "Retirement Account"


def test_parse_dollar_amounts():
    """Dollar parsing handles various formats."""
    assert _parse_dollar("$1,234.56") == 1234.56
    assert _parse_dollar("-$500") == -500.0
    assert _parse_dollar("n/a") == 0.0
    assert _parse_dollar("N/A") == 0.0
    assert _parse_dollar("") == 0.0
    assert _parse_dollar("-") == 0.0
    assert _parse_dollar("$0") == 0.0


def test_missing_columns(tmp_path):
    """Tables missing required columns are warned but parsing continues."""
    content = """\
# Portfolio Holdings (as of Jan 1, 2026)

## Incomplete Account

| Symbol | Name |
|--------|------|
| AAPL | Apple |
"""
    path = tmp_path / "portfolio-holdings.md"
    path.write_text(content)
    holdings, as_of = _parse_holdings_md(path)
    # Missing "shares" and "market value" — column_map won't include required cols
    # but header row is consumed; data rows would try to parse but lack fields.
    # In practice, the data row should be skipped or parsed with defaults.
    assert as_of == "Jan 1, 2026"


def test_header_column_mapping(tmp_path):
    """Column aliases (Ticker, Quantity, Value) map to canonical names."""
    content = """\
# Portfolio Holdings (as of Mar 1, 2026)

## Alt Headers

| Ticker | Company | Quantity | Value |
|--------|---------|----------|-------|
| TSLA | Tesla Inc | 10 | $5,000.00 |
"""
    path = tmp_path / "portfolio-holdings.md"
    path.write_text(content)
    holdings, as_of = _parse_holdings_md(path)
    # "Ticker" -> "symbol", "Company" -> "name", "Quantity" -> "shares", "Value" -> "market_value"
    assert len(holdings) == 1
    assert holdings[0]["symbol"] == "TSLA"
    assert holdings[0]["shares"] == 10.0
    assert holdings[0]["market_value"] == 5000.00


def test_as_of_date(holdings_md):
    """The as_of date is extracted from the header."""
    _, as_of = _parse_holdings_md(holdings_md)
    assert as_of == "Feb 28, 2026"


def test_rsu_schedule(rsu_md):
    """RSU schedule parsing returns correct entries."""
    with patch("terminalq.providers.portfolio.PORTFOLIO_DIR", rsu_md.parent):
        schedule = load_rsu_schedule()
    assert len(schedule) == 2
    assert schedule[0]["date"] == "2026-06-20"
    assert schedule[0]["grant"] == "2026 Grant"
    assert schedule[0]["pct_of_grant"] == "16.67%"
    assert schedule[0]["est_value"] == "$125,000"


def test_unique_symbols(holdings_md):
    """Unique symbols are sorted and deduplicated across accounts."""
    with patch("terminalq.providers.portfolio.PORTFOLIO_DIR", holdings_md.parent):
        with patch(
            "terminalq.providers.portfolio.load_portfolio"
        ) as mock_load:
            mock_load.return_value = [
                {"symbol": "AAPL"}, {"symbol": "MSFT"}, {"symbol": "AAPL"},
                {"symbol": "GOOG"}, {"symbol": "VTI"},
            ]
            symbols = get_unique_symbols()
    assert symbols == ["AAPL", "GOOG", "MSFT", "VTI"]
