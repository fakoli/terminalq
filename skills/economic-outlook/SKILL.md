---
name: economic-outlook
description: Macro economic analysis — business cycle, inflation, yields, Fed policy
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

After gathering all data, synthesize:

**Business Cycle Positioning:**

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

Present as a structured macro brief — lead with the big picture, then drill into each area.
