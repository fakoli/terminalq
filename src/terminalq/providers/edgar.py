"""SEC EDGAR data provider — financial statements and filings."""

import asyncio
import time

import httpx

from terminalq import cache
from terminalq.config import (
    CACHE_TTL_CIK,
    CACHE_TTL_FILINGS,
    CACHE_TTL_FINANCIALS,
    SEC_USER_AGENT,
)
from terminalq.logging_config import log

# SEC fair-use rate limit: 10 requests/second.
_rate_lock = asyncio.Lock()
_last_request_time = 0.0

# ---------------------------------------------------------------------------
# XBRL concept aliases per statement type.  For each logical metric we list
# several XBRL concept names that different filers may use.
# ---------------------------------------------------------------------------

_INCOME_CONCEPTS: dict[str, list[str]] = {
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ],
    "cost_of_revenue": [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
        "CostOfGoodsSold",
    ],
    "gross_profit": ["GrossProfit"],
    "operating_income": [
        "OperatingIncomeLoss",
        "OperatingIncome",
    ],
    "net_income": [
        "NetIncomeLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
    ],
    "eps_basic": ["EarningsPerShareBasic"],
    "eps_diluted": ["EarningsPerShareDiluted"],
}

_BALANCE_SHEET_CONCEPTS: dict[str, list[str]] = {
    "total_assets": ["Assets"],
    "total_liabilities": ["Liabilities"],
    "stockholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "cash_and_equivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",
    ],
    "long_term_debt": [
        "LongTermDebt",
        "LongTermDebtNoncurrent",
    ],
    "current_assets": ["AssetsCurrent"],
    "current_liabilities": ["LiabilitiesCurrent"],
}

_CASH_FLOW_CONCEPTS: dict[str, list[str]] = {
    "operating_cash_flow": [
        "NetCashProvidedByOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivities",
    ],
    "investing_cash_flow": [
        "NetCashProvidedByInvestingActivities",
        "NetCashProvidedByUsedInInvestingActivities",
        "PaymentsToAcquirePropertyPlantAndEquipment",
    ],
    "financing_cash_flow": [
        "NetCashProvidedByFinancingActivities",
        "NetCashProvidedByUsedInFinancingActivities",
    ],
    "capital_expenditure": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "CapitalExpenditure",
        "PaymentsToAcquireProductiveAssets",
    ],
}

_STATEMENT_MAP: dict[str, dict[str, list[str]]] = {
    "income": _INCOME_CONCEPTS,
    "balance_sheet": _BALANCE_SHEET_CONCEPTS,
    "cash_flow": _CASH_FLOW_CONCEPTS,
}


def _error(symbol: str, msg: str) -> dict:
    return {"error": msg, "symbol": symbol, "source": "sec_edgar"}


async def _rate_limited_get(
    client: httpx.AsyncClient,
    url: str,
) -> httpx.Response:
    """Perform a GET that respects SEC's 10 req/sec fair-use policy."""
    global _last_request_time
    async with _rate_lock:
        now = time.monotonic()
        elapsed = now - _last_request_time
        if elapsed < 0.1:
            await asyncio.sleep(0.1 - elapsed)
        _last_request_time = time.monotonic()

    headers = {"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    log.debug("EDGAR request: %s", url)
    return await client.get(url, headers=headers, timeout=15)


# ---------------------------------------------------------------------------
# CIK resolution
# ---------------------------------------------------------------------------


async def _resolve_cik(symbol: str) -> str:
    """Resolve a ticker symbol to a zero-padded 10-digit CIK string.

    Uses the SEC company_tickers.json file (cached for CACHE_TTL_CIK).
    """
    symbol_upper = symbol.upper()

    # Check if we already have this specific CIK cached.
    cik_cache_key = f"edgar_cik_{symbol_upper}"
    cached_cik = cache.get(cik_cache_key)
    if cached_cik:
        log.debug("CIK cache hit for %s", symbol_upper)
        return cached_cik

    # Fetch or use cached tickers JSON.
    tickers_cache_key = "edgar_company_tickers"
    tickers_data = cache.get(tickers_cache_key)

    if not tickers_data:
        async with httpx.AsyncClient() as client:
            resp = await _rate_limited_get(
                client,
                "https://www.sec.gov/files/company_tickers.json",
            )
            resp.raise_for_status()
            tickers_data = resp.json()
        cache.set(tickers_cache_key, tickers_data, CACHE_TTL_CIK)

    # Search for the ticker in the JSON.
    for entry in tickers_data.values():
        if entry.get("ticker", "").upper() == symbol_upper:
            cik = str(entry["cik_str"]).zfill(10)
            cache.set(cik_cache_key, cik, CACHE_TTL_CIK)
            return cik

    raise ValueError(f"CIK not found for symbol: {symbol_upper}")


# ---------------------------------------------------------------------------
# Financial statements
# ---------------------------------------------------------------------------


def _extract_annual_values(
    facts: dict,
    concept: str,
    periods: int,
) -> list[dict]:
    """Return the latest *periods* 10-K entries for a us-gaap concept.

    Each entry is ``{"period_end": str, "fiscal_year": int, "value": ...}``.
    The function looks for annual (10-K) filings by checking ``form == "10-K"``
    in the ``units/USD`` array (or ``units/USD/share`` for EPS concepts).
    """
    us_gaap = facts.get("us-gaap", {})
    concept_data = us_gaap.get(concept)
    if concept_data is None:
        return []

    units = concept_data.get("units", {})
    # EPS items are reported in USD/shares; most others in USD.
    values_list = units.get("USD") or units.get("USD/shares") or []

    # Keep only 10-K entries (annual filings).
    annual = [v for v in values_list if v.get("form") == "10-K" and v.get("end") and v.get("val") is not None]

    # De-duplicate by period end (keep the latest filing per period).
    seen: dict[str, dict] = {}
    for v in annual:
        end = v["end"]
        if end not in seen or v.get("filed", "") > seen[end].get("filed", ""):
            seen[end] = v

    sorted_entries = sorted(seen.values(), key=lambda x: x["end"], reverse=True)
    return [
        {
            "period_end": e["end"],
            "fiscal_year": int(e.get("fy", 0)),
            "value": e["val"],
        }
        for e in sorted_entries[:periods]
    ]


async def get_financials(
    symbol: str,
    statement: str = "income",
    periods: int = 4,
) -> dict:
    """Fetch financial statement data from SEC EDGAR XBRL company facts.

    Parameters
    ----------
    symbol:
        Stock ticker (e.g. ``"AAPL"``).
    statement:
        One of ``"income"``, ``"balance_sheet"``, ``"cash_flow"``.
    periods:
        Number of most-recent annual (10-K) periods to return.
    """
    symbol = symbol.upper()
    cache_key = f"edgar_financials_{symbol}_{statement}_{periods}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    concepts = _STATEMENT_MAP.get(statement)
    if concepts is None:
        return _error(
            symbol,
            f"Unknown statement type '{statement}'. Use 'income', 'balance_sheet', or 'cash_flow'.",
        )

    # Resolve CIK.
    try:
        cik = await _resolve_cik(symbol)
    except (ValueError, httpx.HTTPError) as exc:
        return _error(symbol, str(exc))

    # Fetch company facts.
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    try:
        async with httpx.AsyncClient() as client:
            resp = await _rate_limited_get(client, url)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        log.warning("EDGAR HTTP %d for %s", exc.response.status_code, url)
        return _error(symbol, f"HTTP {exc.response.status_code}")
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        log.error("EDGAR connection error: %s", exc)
        return _error(symbol, "Connection to SEC EDGAR failed")

    facts = data.get("facts", {})

    # Determine period end dates from the first metric that has data.
    # This ensures all metrics align on the same reporting periods.
    period_ends: list[str] | None = None
    for metric_name, aliases in concepts.items():
        for alias in aliases:
            entries = _extract_annual_values(facts, alias, periods)
            if entries:
                period_ends = [e["period_end"] for e in entries]
                break
        if period_ends:
            break

    if not period_ends:
        return _error(symbol, f"No annual {statement} data found in EDGAR")

    # Build period rows.
    period_rows: list[dict] = []
    for pe in period_ends:
        row: dict = {"period_end": pe}
        # Try to grab fiscal_year from any available entry.
        row["fiscal_year"] = None
        for metric_name, aliases in concepts.items():
            for alias in aliases:
                entries = _extract_annual_values(facts, alias, periods)
                match = [e for e in entries if e["period_end"] == pe]
                if match:
                    row[metric_name] = match[0]["value"]
                    if row["fiscal_year"] is None and match[0]["fiscal_year"]:
                        row["fiscal_year"] = match[0]["fiscal_year"]
                    break  # found the alias that works for this metric
            else:
                # No alias had data for this metric — leave it absent.
                pass
        period_rows.append(row)

    result = {
        "symbol": symbol,
        "statement": statement,
        "periods": period_rows,
        "source": "sec_edgar",
    }
    cache.set(cache_key, result, CACHE_TTL_FINANCIALS)
    return result


# ---------------------------------------------------------------------------
# Filings
# ---------------------------------------------------------------------------


async def get_filings(
    symbol: str,
    filing_type: str = "",
    limit: int = 10,
) -> dict:
    """Fetch recent SEC filings for a company.

    Parameters
    ----------
    symbol:
        Stock ticker.
    filing_type:
        Optional filter (e.g. ``"10-K"``, ``"10-Q"``, ``"8-K"``).
    limit:
        Max number of filings to return.
    """
    symbol = symbol.upper()
    cache_key = f"edgar_filings_{symbol}_{filing_type}_{limit}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    try:
        cik = await _resolve_cik(symbol)
    except (ValueError, httpx.HTTPError) as exc:
        return _error(symbol, str(exc))

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        async with httpx.AsyncClient() as client:
            resp = await _rate_limited_get(client, url)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        log.warning("EDGAR HTTP %d for %s", exc.response.status_code, url)
        return _error(symbol, f"HTTP {exc.response.status_code}")
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        log.error("EDGAR connection error: %s", exc)
        return _error(symbol, "Connection to SEC EDGAR failed")

    company_name = data.get("name", "")
    recent = data.get("filings", {}).get("recent", {})

    forms = recent.get("form", [])
    filed_dates = recent.get("filingDate", [])
    descriptions = recent.get("primaryDocDescription", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    filings: list[dict] = []
    for i in range(len(forms)):
        form = forms[i] if i < len(forms) else ""
        if filing_type and form != filing_type:
            continue

        accession = accession_numbers[i] if i < len(accession_numbers) else ""
        accession_path = accession.replace("-", "")
        primary_doc = primary_docs[i] if i < len(primary_docs) else ""
        doc_url = (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_path}/{primary_doc}"
            if accession and primary_doc
            else ""
        )

        filings.append(
            {
                "type": form,
                "filed_date": filed_dates[i] if i < len(filed_dates) else "",
                "description": descriptions[i] if i < len(descriptions) else "",
                "accession_number": accession,
                "url": doc_url,
            }
        )

        if len(filings) >= limit:
            break

    result = {
        "symbol": symbol,
        "company_name": company_name,
        "cik": cik,
        "filings": filings,
        "source": "sec_edgar",
    }
    cache.set(cache_key, result, CACHE_TTL_FILINGS)
    return result
