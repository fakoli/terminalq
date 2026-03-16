"""Portfolio allocation analytics — classify holdings and compute breakdown.

Parses reference/etf-classifications.md to map ETFs to asset class, region,
and sub-class, then loads portfolio holdings to compute allocation percentages.
"""

import re

from terminalq import cache
from terminalq.config import CACHE_TTL_ALLOCATION, PORTFOLIO_DIR
from terminalq.logging_config import log
from terminalq.providers import portfolio


def _parse_etf_classifications() -> dict[str, dict]:
    """Parse etf-classifications.md into a symbol → classification mapping.

    Returns:
        Dict mapping symbol to {asset_class, region, sub_class}.
    """
    path = PORTFOLIO_DIR / "etf-classifications.md"
    if not path.exists():
        log.warning("ETF classifications file not found: %s", path)
        return {}

    text = path.read_text()
    classifications: dict[str, dict] = {}
    column_map: dict[int, str] = {}

    for line in text.splitlines():
        stripped = line.strip()

        # Skip non-table lines
        if not stripped.startswith("|"):
            continue

        # Skip separator rows
        if re.match(r"^\|[\s\-|]+\|$", stripped):
            continue

        parts = [p.strip() for p in stripped.split("|")[1:-1]]

        # Detect header row
        if not column_map:
            for i, col_name in enumerate(parts):
                lower = col_name.lower()
                if lower in ("symbol", "ticker"):
                    column_map[i] = "symbol"
                elif lower in ("asset class", "asset_class", "class"):
                    column_map[i] = "asset_class"
                elif lower in ("region",):
                    column_map[i] = "region"
                elif lower in ("sub-class", "sub_class", "subclass", "sub class"):
                    column_map[i] = "sub_class"
                elif lower in ("name",):
                    column_map[i] = "name"
            continue

        if not column_map:
            continue

        row: dict = {}
        for i, value in enumerate(parts):
            canonical = column_map.get(i)
            if canonical:
                row[canonical] = value

        symbol = row.get("symbol", "").strip()
        if symbol:
            classifications[symbol] = {
                "asset_class": row.get("asset_class", "Unknown"),
                "region": row.get("region", "Unknown"),
                "sub_class": row.get("sub_class", ""),
                "name": row.get("name", ""),
            }

    log.info("Loaded %d ETF classifications", len(classifications))
    return classifications


def compute_allocation() -> dict:
    """Compute portfolio allocation breakdown by asset class and region.

    Returns:
        Dict with breakdowns by asset_class, region, sub_class, and per-holding details.
    """
    cache_key = "allocation_analysis"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    holdings = portfolio.load_portfolio()
    if not holdings:
        return {"error": "No portfolio holdings found", "source": "analytics"}

    classifications = _parse_etf_classifications()

    # Aggregate by symbol across accounts
    symbol_values: dict[str, float] = {}
    symbol_names: dict[str, str] = {}
    for h in holdings:
        sym = h["symbol"]
        val = h.get("market_value", 0)
        symbol_values[sym] = symbol_values.get(sym, 0) + val
        if not symbol_names.get(sym):
            symbol_names[sym] = h.get("name", "")

    total_value = sum(symbol_values.values())
    if total_value <= 0:
        return {"error": "Portfolio has no value", "source": "analytics"}

    # Classify each holding
    by_asset_class: dict[str, float] = {}
    by_region: dict[str, float] = {}
    by_sub_class: dict[str, float] = {}
    unclassified: list[str] = []
    holding_details = []

    for sym, value in sorted(symbol_values.items(), key=lambda x: -x[1]):
        pct = round(value / total_value * 100, 2)
        classification = classifications.get(sym, {})
        asset_class = classification.get("asset_class", "Unclassified")
        region = classification.get("region", "Unknown")
        sub_class = classification.get("sub_class", "")

        if not classification:
            unclassified.append(sym)

        by_asset_class[asset_class] = round(by_asset_class.get(asset_class, 0) + pct, 2)
        by_region[region] = round(by_region.get(region, 0) + pct, 2)
        if sub_class:
            by_sub_class[sub_class] = round(by_sub_class.get(sub_class, 0) + pct, 2)

        holding_details.append(
            {
                "symbol": sym,
                "name": symbol_names.get(sym, ""),
                "market_value": round(value, 2),
                "weight_pct": pct,
                "asset_class": asset_class,
                "region": region,
                "sub_class": sub_class,
            }
        )

    # Sort breakdowns by weight descending
    by_asset_class_sorted = dict(sorted(by_asset_class.items(), key=lambda x: -x[1]))
    by_region_sorted = dict(sorted(by_region.items(), key=lambda x: -x[1]))
    by_sub_class_sorted = dict(sorted(by_sub_class.items(), key=lambda x: -x[1]))

    result = {
        "total_value": round(total_value, 2),
        "num_holdings": len(symbol_values),
        "by_asset_class": by_asset_class_sorted,
        "by_region": by_region_sorted,
        "by_sub_class": by_sub_class_sorted,
        "holdings": holding_details,
        "unclassified": unclassified,
        "source": "analytics",
    }
    cache.set(cache_key, result, CACHE_TTL_ALLOCATION)
    return result
