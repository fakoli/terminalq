---
name: screen
description: Screen S&P 500 stocks by criteria
arguments:
  - name: criteria
    description: "Screening criteria (e.g., 'Technology sector', 'Healthcare min market cap 50000')"
    required: false
---

Use the `terminalq_screen_stocks` MCP tool to screen S&P 500 stocks.

Parse the user's criteria from "$ARGUMENTS":
- Sector keywords → sector parameter (e.g., "tech" → "Technology", "health" → "Health Care")
- "large cap" or "mega cap" → min_market_cap=50000
- "mid cap" → max_market_cap=50000
- "small cap" → max_market_cap=10000

If no criteria provided, show all sectors with counts and ask the user to pick one.

Present results as a table: Symbol, Name, Sector, Market Cap, Industry.

If the user has portfolio holdings in the screened sector, note which they already own.
