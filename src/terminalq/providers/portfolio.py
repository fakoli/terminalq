"""Portfolio data provider — loads holdings from local reference files."""
import re
from pathlib import Path

from terminalq.config import PORTFOLIO_DIR
from terminalq.logging_config import log

# Required columns for holdings table
REQUIRED_COLUMNS = {"symbol", "shares", "market value"}
# Column name aliases (lowercase → canonical)
COLUMN_ALIASES = {
    "symbol": "symbol",
    "ticker": "symbol",
    "name": "name",
    "company": "name",
    "shares": "shares",
    "quantity": "shares",
    "cost basis": "cost_basis",
    "cost": "cost_basis",
    "market value": "market_value",
    "value": "market_value",
    "unrealized g/l": "unrealized_gl",
    "unrealized gl": "unrealized_gl",
    "gain/loss": "unrealized_gl",
}


def _parse_holdings_md(path: Path) -> tuple[list[dict], str]:
    """Parse portfolio-holdings.md into a list of holdings and an as_of date.

    Returns (holdings, as_of_date_string).
    """
    if not path.exists():
        return [], ""

    text = path.read_text()
    holdings = []
    current_account = ""
    column_map: dict[int, str] = {}
    as_of = ""

    for line in text.splitlines():
        stripped = line.strip()

        # Extract as_of date from header like "# Portfolio Holdings (as of Feb 28, 2026)"
        if stripped.startswith("# ") and "as of" in stripped.lower():
            match = re.search(r"\(as of (.+?)\)", stripped, re.IGNORECASE)
            if match:
                as_of = match.group(1).strip()

        # Detect account headers (## level)
        if stripped.startswith("## "):
            current_account = stripped[3:].strip()
            column_map = {}  # Reset column map for each account section
            continue

        # Skip non-table lines
        if not stripped.startswith("|"):
            continue

        # Skip separator rows (|---|---|...)
        if re.match(r"^\|[\s\-|]+\|$", stripped):
            continue

        parts = [p.strip() for p in stripped.split("|")[1:-1]]

        # Detect header row and build column mapping
        if not column_map:
            for i, col_name in enumerate(parts):
                canonical = COLUMN_ALIASES.get(col_name.lower())
                if canonical:
                    column_map[i] = canonical
            # Validate required columns
            mapped_names = set(column_map.values())
            missing = REQUIRED_COLUMNS - mapped_names
            if missing:
                log.warning(
                    "Missing required columns %s in account '%s'",
                    missing, current_account,
                )
            continue

        # Parse data rows using column map
        if not column_map:
            continue

        row: dict = {"account": current_account}
        for i, value in enumerate(parts):
            canonical = column_map.get(i)
            if canonical:
                row[canonical] = value

        # Skip empty symbol rows
        symbol = row.get("symbol", "").strip()
        if not symbol:
            continue

        try:
            holdings.append({
                "symbol": symbol,
                "name": row.get("name", ""),
                "shares": float(row.get("shares", "0").replace(",", "")),
                "cost_basis": _parse_dollar(row.get("cost_basis", "")),
                "market_value": _parse_dollar(row.get("market_value", "")),
                "unrealized_gl": _parse_dollar(row.get("unrealized_gl", "")),
                "account": current_account,
            })
        except (ValueError, AttributeError) as e:
            log.warning("Skipping malformed row in '%s': %s — %s", current_account, row, e)
            continue

    log.info("Parsed %d holdings from %s (as of %s)", len(holdings), path.name, as_of)
    return holdings, as_of


def _parse_dollar(s: str) -> float:
    """Parse a dollar string like '$1,234.56' or '-$500' into a float."""
    if not s:
        return 0.0
    s = s.replace("$", "").replace(",", "").strip()
    if s in ("", "-", "n/a", "N/A"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def load_portfolio() -> list[dict]:
    """Load all portfolio holdings from reference data."""
    holdings_path = PORTFOLIO_DIR / "portfolio-holdings.md"
    holdings, _ = _parse_holdings_md(holdings_path)
    return holdings


def get_portfolio_as_of() -> str:
    """Get the as-of date string from the portfolio file."""
    holdings_path = PORTFOLIO_DIR / "portfolio-holdings.md"
    _, as_of = _parse_holdings_md(holdings_path)
    return as_of


def get_unique_symbols() -> list[str]:
    """Get unique ticker symbols from the portfolio."""
    holdings = load_portfolio()
    symbols = list({h["symbol"] for h in holdings if h["symbol"]})
    return sorted(symbols)


def load_watchlist() -> list[dict]:
    """Load watchlist symbols from reference/watchlist.md.

    Parses a markdown table with columns: Symbol, Name.
    Returns list of dicts with symbol and name keys.
    """
    watchlist_path = PORTFOLIO_DIR / "watchlist.md"
    if not watchlist_path.exists():
        log.warning("Watchlist file not found: %s", watchlist_path)
        return []

    text = watchlist_path.read_text()
    items = []
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
                elif lower in ("name", "company"):
                    column_map[i] = "name"
                elif lower in ("notes", "note"):
                    column_map[i] = "notes"
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
            items.append({
                "symbol": symbol,
                "name": row.get("name", ""),
                "notes": row.get("notes", ""),
            })

    log.info("Loaded %d watchlist symbols from %s", len(items), watchlist_path.name)
    return items


def load_rsu_schedule() -> list[dict]:
    """Load RSU vesting schedule from reference data."""
    rsu_path = PORTFOLIO_DIR / "rsu-schedule.md"
    if not rsu_path.exists():
        return []

    text = rsu_path.read_text()
    schedule = []

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|") and not line.startswith("|-") and "Date" not in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                try:
                    schedule.append({
                        "date": parts[0],
                        "grant": parts[1] if len(parts) > 1 else "",
                        "pct_of_grant": parts[2] if len(parts) > 2 else "",
                        "est_value": parts[3] if len(parts) > 3 else "",
                    })
                except (ValueError, IndexError):
                    continue

    return schedule
