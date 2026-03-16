---
name: market-overview
description: Morning market briefing — indexes, sectors, macro, portfolio in context
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

After gathering all data, synthesize a structured briefing:

**Market Mood:** Determine risk-on vs risk-off from SPY/VIX/TLT/GLD movements. If VIX > 20, flag elevated volatility. If TLT is up while SPY is down, note flight to safety.

**Index Snapshot:** Present major indexes in a table — price, daily change, % change.

**Style Rotation:** Compare QQQ (growth/tech) vs DIA (value/industrials) vs IWM (small caps) to identify rotation trends.

**Sector Heatmap:** Embed the sector performance chart. Highlight leading and lagging sectors.

**Macro Dashboard:** Summarize key readings — yield curve status (inverted = recession signal), inflation trend (CPI direction), labor market (unemployment, claims), Fed funds rate.

**Upcoming Catalysts:** List the most market-moving events from the economic calendar (CPI releases, FOMC, NFP, earnings).

**Portfolio Impact:** Note how the user's portfolio performed relative to SPY. Flag any holdings in lagging sectors or with notable moves.

Keep the briefing concise but actionable — what happened, what matters, what to watch.
