"""S&P 500 stock screener provider — cached component list with sector/metric filtering."""
import asyncio
import csv
import io
import httpx

from terminalq import cache
from terminalq.config import CACHE_TTL_SP500_LIST
from terminalq.logging_config import log
from terminalq.providers import finnhub

_SP500_CSV_URL = (
    "https://raw.githubusercontent.com/datasets/"
    "s-and-p-500-companies/main/data/constituents.csv"
)

# Maximum number of symbols to fetch profiles for in one screen call
_PROFILE_FETCH_THRESHOLD = 50


async def get_sp500_components() -> list[dict]:
    """Return the S&P 500 component list (symbol, name, sector).

    Fetches from the datahub CSV and caches for CACHE_TTL_SP500_LIST (7 days).
    """
    cache_key = "screener_sp500_list"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    log.info("Fetching S&P 500 component list from datahub CSV")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(_SP500_CSV_URL, timeout=15)
            resp.raise_for_status()
            text = resp.text
    except httpx.TimeoutException:
        log.warning("Timeout fetching S&P 500 list")
        return []
    except httpx.HTTPStatusError as e:
        log.warning("HTTP %d fetching S&P 500 list", e.response.status_code)
        return []
    except httpx.ConnectError:
        log.error("Connection failed fetching S&P 500 list")
        return []

    components: list[dict] = []
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        symbol = row.get("Symbol", "").strip()
        name = row.get("Name", "").strip()
        sector = row.get("Sector", "").strip()
        if symbol:
            components.append({
                "symbol": symbol,
                "name": name,
                "sector": sector,
            })

    log.info("Parsed %d S&P 500 components", len(components))
    cache.set(cache_key, components, CACHE_TTL_SP500_LIST)
    return components


async def screen_stocks(
    sector: str = "",
    min_market_cap: float = 0,
    max_market_cap: float = 0,
    min_dividend_yield: float = 0,
    max_pe_ratio: float = 0,
    limit: int = 20,
) -> dict:
    """Screen S&P 500 stocks by sector and optional numeric filters.

    Sector filtering is local (fast, no API calls).  Numeric filters
    (market_cap, dividend_yield, pe_ratio) require Finnhub company profiles
    and are only applied when the sector-filtered set is small enough
    (<= 50 symbols) to avoid rate-limit issues.

    Returns a dict with match counts, applied filters, and result rows.
    """
    components = await get_sp500_components()
    total_universe = len(components)

    if not components:
        return {
            "total_universe": 0,
            "matches_after_sector": 0,
            "matches_after_all_filters": 0,
            "results": [],
            "filters_applied": {},
            "source": "screener (S&P 500)",
            "error": "Could not fetch S&P 500 component list",
        }

    # --- Sector filter (local, case-insensitive partial match) ---
    if sector:
        sector_lower = sector.lower()
        filtered = [
            c for c in components
            if sector_lower in c.get("sector", "").lower()
        ]
    else:
        filtered = list(components)

    matches_after_sector = len(filtered)

    # Track which filters are applied
    filters_applied: dict = {}
    if sector:
        filters_applied["sector"] = sector

    has_numeric_filters = any([
        min_market_cap > 0,
        max_market_cap > 0,
        min_dividend_yield > 0,
        max_pe_ratio > 0,
    ])

    if has_numeric_filters:
        if min_market_cap > 0:
            filters_applied["min_market_cap"] = min_market_cap
        if max_market_cap > 0:
            filters_applied["max_market_cap"] = max_market_cap
        if min_dividend_yield > 0:
            filters_applied["min_dividend_yield"] = min_dividend_yield
        if max_pe_ratio > 0:
            filters_applied["max_pe_ratio"] = max_pe_ratio

    # --- Numeric filters (require Finnhub profiles) ---
    results: list[dict] = []
    note = ""

    if has_numeric_filters and matches_after_sector <= _PROFILE_FETCH_THRESHOLD:
        # Fetch profiles for the filtered symbols (uses cache internally)
        profiles = await _fetch_profiles([c["symbol"] for c in filtered])

        for comp in filtered:
            sym = comp["symbol"]
            profile = profiles.get(sym, {})
            if "error" in profile:
                continue

            market_cap = profile.get("market_cap") or 0
            # Finnhub profile doesn't include PE/dividend directly; skip those
            # filters if profile data doesn't have them.

            if min_market_cap > 0 and market_cap < min_market_cap:
                continue
            if max_market_cap > 0 and market_cap > max_market_cap:
                continue

            results.append({
                "symbol": sym,
                "name": comp.get("name", profile.get("name", "")),
                "sector": comp.get("sector", ""),
                "market_cap": market_cap,
                "industry": profile.get("industry", ""),
            })

    elif has_numeric_filters and matches_after_sector > _PROFILE_FETCH_THRESHOLD:
        # Too many symbols to fetch profiles — apply only cached profiles
        note = (
            f"Numeric filters partially applied: sector matched {matches_after_sector} "
            f"symbols (>{_PROFILE_FETCH_THRESHOLD}). Only symbols with cached "
            "profiles were checked; narrow your sector filter for full coverage."
        )
        for comp in filtered:
            sym = comp["symbol"]
            cached_profile = cache.get(f"finnhub_profile_{sym}")
            if cached_profile:
                market_cap = cached_profile.get("market_cap") or 0
                if min_market_cap > 0 and market_cap < min_market_cap:
                    continue
                if max_market_cap > 0 and market_cap > max_market_cap:
                    continue
                results.append({
                    "symbol": sym,
                    "name": comp.get("name", cached_profile.get("name", "")),
                    "sector": comp.get("sector", ""),
                    "market_cap": market_cap,
                    "industry": cached_profile.get("industry", ""),
                })
            else:
                # Include without numeric data so the list is still useful
                results.append({
                    "symbol": sym,
                    "name": comp.get("name", ""),
                    "sector": comp.get("sector", ""),
                    "market_cap": None,
                    "industry": "",
                })
    else:
        # No numeric filters — return sector-filtered list directly
        for comp in filtered:
            cached_profile = cache.get(f"finnhub_profile_{comp['symbol']}")
            results.append({
                "symbol": comp["symbol"],
                "name": comp.get("name", ""),
                "sector": comp.get("sector", ""),
                "market_cap": (
                    cached_profile.get("market_cap")
                    if cached_profile else None
                ),
                "industry": (
                    cached_profile.get("industry", "")
                    if cached_profile else ""
                ),
            })

    matches_after_all = len(results)

    # Sort by market_cap descending (nulls last)
    results.sort(
        key=lambda r: (r.get("market_cap") is None, -(r.get("market_cap") or 0)),
    )

    # Apply limit
    results = results[:limit]

    response: dict = {
        "total_universe": total_universe,
        "matches_after_sector": matches_after_sector,
        "matches_after_all_filters": matches_after_all,
        "results": results,
        "filters_applied": filters_applied,
        "source": "screener (S&P 500)",
    }
    if note:
        response["note"] = note

    return response


async def _fetch_profiles(symbols: list[str]) -> dict[str, dict]:
    """Fetch Finnhub company profiles for a list of symbols.

    Uses the Finnhub provider (which handles caching internally).
    Returns a dict mapping symbol -> profile.
    """
    profiles: dict[str, dict] = {}

    async def _get_one(sym: str) -> None:
        try:
            profile = await finnhub.get_company_profile(sym)
            profiles[sym] = profile
        except Exception as e:
            log.warning("Failed to fetch profile for %s: %s", sym, e)
            profiles[sym] = {"error": str(e)}

    tasks = [_get_one(sym) for sym in symbols]
    await asyncio.gather(*tasks)
    return profiles
