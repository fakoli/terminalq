---
name: earnings-preview
description: >-
  Earnings season preparation covering upcoming earnings dates, EPS estimates, historical beat
  rates, pre-earnings technical setups, and portfolio risk assessment. Use this skill to prepare
  for earnings announcements across your portfolio holdings. Ask for an "earnings preview",
  "upcoming earnings", "prep for earnings", "earnings season overview", "earnings calendar",
  "who reports this week", or "earnings this week" to trigger this workflow. Produces an
  Earnings Preview contract output.
triggers:
  - earnings preview
  - upcoming earnings
  - prep for earnings
  - earnings season
  - earnings calendar
  - who reports this week
  - earnings this week
---

Prepare for upcoming earnings season by following these steps:

**Step 1:** Call these tools in parallel to gather context:

1. `terminalq_get_portfolio_live()` — current portfolio holdings
2. `terminalq_get_economic_calendar(14)` — upcoming macro events (may include some earnings dates)

**Step 2:** The economic calendar focuses on macro events and may not include all corporate earnings dates. To find upcoming earnings for portfolio holdings, take the top 5-8 holdings by value and call these tools in parallel per symbol:

3. `terminalq_get_earnings(symbol)` — historical EPS, beat/miss pattern
4. `terminalq_get_analyst_ratings(symbol)` — consensus expectations and price targets
5. `terminalq_get_technicals(symbol)` — pre-earnings technical setup
6. `terminalq_get_news(symbol, 7)` — recent news and sentiment

After gathering all data, produce an earnings prep report following the **Earnings Preview** contract in `docs/output-contracts.md`:

**Earnings Calendar:**

- Table of portfolio holdings with known/expected earnings dates
- Sort by date (soonest first)

**Per-Company Analysis (for each holding with upcoming earnings):**

_[SYMBOL] — [Company Name]_

- **Consensus:** Expected EPS, revenue estimate if available
- **Track Record:** Beat rate (X of last Y quarters), average surprise %
- **Technical Setup:** Is the stock trending up/down into earnings? RSI level (overbought before earnings = risky), support/resistance levels
- **Recent Sentiment:** Key news themes — positive catalysts, concerns, or guidance signals
- **Position Risk:** Current position size \* expected move (historical earnings day move %) = estimated P&L impact

**Portfolio Earnings Risk Summary:**

- Total portfolio exposure to upcoming earnings
- Highest-risk positions (largest position \* largest expected move)
- Any positions where technical setup + sentiment suggest elevated risk

**Action Items:**

- Positions to consider trimming before earnings (high risk, overbought)
- Positions well-set-up for potential upside
- Hedging suggestions if total earnings exposure is high

**Data Freshness:** Include a table noting each data source, how recent it is, and confidence level (High/Moderate/Low per `docs/output-contracts.md`).

**Disclaimer:** End with the standard disclaimer from `docs/output-contracts.md`.

Keep each company analysis concise — focus on the numbers and signals, not background.

## Failure Modes

| Failure Mode | Signal | Response |
|---|---|---|
| Portfolio unavailable | `terminalq_get_portfolio_live` fails | Stop and instruct user to run `/ingest` first — cannot identify holdings without portfolio data |
| No earnings data | `terminalq_get_earnings` returns empty for a symbol | Note that no earnings history is available; skip that holding's analysis |
| Earnings dates unknown | No upcoming earnings dates found in data | Note that earnings dates may not be announced yet; present available analysis for current quarter |
| Technicals fail | `terminalq_get_technicals` errors for a symbol | Skip Technical Setup for that holding; note in output |
| Few holdings | Portfolio has < 3 holdings | Analyze all holdings rather than filtering to top 5-8 |

## When Not to Use

- **Do not use** for a single stock's earnings — use `company-research` with the symbol instead
- **Do not use** outside of earnings season when no portfolio holdings have upcoming earnings
- **Do not use** for buy/sell decisions — use `trade-research` for position-level decisions
