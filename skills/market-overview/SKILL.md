---
name: market-overview
description: >-
  Generate a comprehensive morning market briefing covering index performance, sector rotation,
  macro indicators, and portfolio impact. Use this skill when you need a broad market summary,
  want to know how markets are doing, or need a morning briefing. Ask for a "market overview",
  "morning briefing", "market summary", "daily briefing", "what's the market doing", or
  "what happened in markets" to trigger this workflow. Produces a Market Briefing contract output.
triggers:
  - market overview
  - how are markets
  - morning briefing
  - market summary
  - what happened in markets
  - market update
  - what's the market doing
  - daily briefing
---

Generate a comprehensive morning market briefing by calling these tools in parallel:

1. `terminalq_get_quotes_batch("SPY,QQQ,DIA,IWM,VIX,TLT,GLD,USO")` — major index and asset class snapshot
2. `terminalq_get_macro_dashboard()` — key economic indicators with latest values
3. `terminalq_get_economic_calendar(7)` — upcoming events this week
4. `terminalq_chart_sector_heatmap()` — sector performance visualization
5. `terminalq_get_portfolio_live()` — user's portfolio in market context

After gathering all data, synthesize a structured briefing following the **Market Briefing** contract in `docs/output-contracts.md`:

**Market Mood:** Determine risk-on vs risk-off from SPY/VIX/TLT/GLD movements. If VIX > 20, flag elevated volatility. If TLT is up while SPY is down, note flight to safety.

**Index Snapshot:** Present major indexes in a table — price, daily change, % change.

**Style Rotation:** Compare QQQ (growth/tech) vs DIA (value/industrials) vs IWM (small caps) to identify rotation trends.

**Sector Heatmap:** Embed the sector performance chart. Highlight leading and lagging sectors.

**Macro Dashboard:** Summarize key readings — yield curve status (inverted = recession signal), inflation trend (CPI direction), labor market (unemployment, claims), Fed funds rate.

**Upcoming Catalysts:** List the most market-moving events from the economic calendar (CPI releases, FOMC, NFP, earnings).

**Portfolio Impact:** Note how the user's portfolio performed relative to SPY. Flag any holdings in lagging sectors or with notable moves.

**Data Freshness:** Include a table noting each data source, how recent it is, and confidence level (High/Moderate/Low per `docs/output-contracts.md`).

**Disclaimer:** End with the standard disclaimer from `docs/output-contracts.md`.

Keep the briefing concise but actionable — what happened, what matters, what to watch.

## Failure Modes

| Failure Mode | Signal | Response |
|---|---|---|
| Macro dashboard errors | `terminalq_get_macro_dashboard` returns errors | Proceed with available data; note which macro indicators are missing |
| Portfolio unavailable | `terminalq_get_portfolio_live` fails or returns empty | Skip Portfolio Impact section; note that portfolio data was unavailable |
| Sector heatmap fails | `terminalq_chart_sector_heatmap` errors | Omit chart; list sector performance from quote data if available |
| Stale cache data | Data sources return cached data > 6h old | Mark affected sections as "Moderate confidence" in Data Freshness |
| Market closed | Quotes show zero daily change | Note that markets are closed; show last close data |

## When Not to Use

- **Do not use** for individual stock analysis — use `company-research` instead
- **Do not use** for buy/sell decisions — use `trade-research` instead
- **Do not use** for deep macro analysis — use `economic-outlook` instead
- **Do not use** for portfolio-specific health checks — use `portfolio-health` instead
