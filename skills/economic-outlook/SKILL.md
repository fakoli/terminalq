---
name: economic-outlook
description: >-
  Comprehensive macro economic analysis covering business cycle positioning, inflation trends,
  labor market conditions, yield curve signals, Fed policy outlook, and portfolio implications.
  Use this skill when you need to understand the economic environment, assess recession risk,
  or evaluate how macro conditions affect your portfolio. Ask for an "economic outlook",
  "macro analysis", "fed watch", "recession risk assessment", "economy overview", "macro outlook",
  "interest rates analysis", "yield curve check", or "inflation update" to trigger this workflow.
  Produces an Economic Brief contract output.
triggers:
  - economic outlook
  - macro analysis
  - fed watch
  - recession risk
  - economy overview
  - macro outlook
  - interest rates
  - yield curve
  - inflation update
---

Generate a comprehensive macro economic analysis by calling these tools in parallel:

1. `terminalq_get_macro_dashboard()` — all key FRED indicators (GDP, CPI, unemployment, Fed funds, yields, claims, payrolls, PCE, etc.)
2. `terminalq_get_economic_calendar(14)` — upcoming events over the next 2 weeks
3. `terminalq_chart_yield_curve()` — Treasury yield curve visualization
4. `terminalq_get_forex("")` — major currency pairs dashboard
5. `terminalq_get_quotes_batch("SPY,TLT,GLD,USO,UUP")` — real-time asset class proxies (equities, bonds, gold, oil, dollar)

After gathering all data, synthesize following the **Economic Brief** contract in `docs/output-contracts.md`:

**Business Cycle Position:**

- Assess where we are: early expansion, mid expansion, late expansion, contraction
- Use GDP growth rate, unemployment trend, and leading indicators to determine phase
- Compare current readings to historical cycle patterns

**Inflation Dashboard:**

- CPI trend (headline and core if available)
- PCE (Fed's preferred measure)
- Direction: accelerating, stable, or decelerating
- Implications for Fed policy

**Labor Market:**

- Unemployment rate and direction
- Initial claims trend (leading indicator)
- Nonfarm payrolls growth
- Assessment: strong, cooling, or deteriorating

**Yield Curve Analysis:**

- Embed the yield curve chart
- Is it inverted? (2Y-10Y spread)
- What does the shape signal? (Normal = expansion, flat = slowdown, inverted = recession warning)
- How has it changed recently?

**Fed Policy Outlook:**

- Current Fed funds rate
- Based on inflation and employment data, is the Fed likely to cut, hold, or hike?
- Timeline expectation

**Currency & Commodities:**

- Dollar strength (UUP proxy)
- Gold trend (risk haven demand)
- Oil direction (inflation input, demand indicator)
- Major forex moves

**Portfolio Implications:**

- Which asset classes benefit from current macro regime?
- Risk factors to watch
- Positioning suggestions (overweight/underweight equity, bonds, commodities)

**Upcoming Catalysts:**

- List the most important upcoming economic releases and their expected market impact

**Data Freshness:** Include a table noting each data source, how recent it is, and confidence level (High/Moderate/Low per `docs/output-contracts.md`).

**Disclaimer:** End with the standard disclaimer from `docs/output-contracts.md`.

Present as a structured macro brief — lead with the big picture, then drill into each area.

## Failure Modes

| Failure Mode | Signal | Response |
|---|---|---|
| FRED API down | `terminalq_get_macro_dashboard` returns errors | This is critical — most sections depend on FRED data. Note that macro data is unavailable; focus on market proxies (SPY, TLT, GLD) for directional signals |
| Yield curve fails | `terminalq_chart_yield_curve` errors | Skip chart; describe yield curve shape from FRED rate data if available |
| Forex data missing | `terminalq_get_forex` fails | Skip Currency & Commodities forex section; use UUP quote as dollar proxy |
| Calendar empty | `terminalq_get_economic_calendar` returns no events | Note that no upcoming events were found; check if this is a holiday period |
| Stale FRED data | Indicators show data > 30 days old | Note in Data Freshness that economic data releases on a lag (monthly/quarterly) — this is normal for FRED |

## When Not to Use

- **Do not use** for individual stock analysis — use `company-research` instead
- **Do not use** for portfolio-specific review — use `portfolio-health` instead
- **Do not use** for trade timing — use `trade-research` which incorporates macro context
