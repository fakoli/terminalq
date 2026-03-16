---
name: earnings-preview
description: Earnings season prep — calendar, estimates, beat rates, technical setup
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

- `terminalq_get_portfolio_live()` — current portfolio holdings
- `terminalq_get_economic_calendar(14)` — upcoming macro events (may include some earnings dates)

**Step 2:** The economic calendar focuses on macro events and may not include all corporate earnings dates. To find upcoming earnings for portfolio holdings, take the top 5-8 holdings by value and call these tools in parallel per symbol:

- `terminalq_get_earnings(symbol)` — historical EPS, beat/miss pattern
- `terminalq_get_analyst_ratings(symbol)` — consensus expectations and price targets
- `terminalq_get_technicals(symbol)` — pre-earnings technical setup
- `terminalq_get_news(symbol, 7)` — recent news and sentiment

After gathering all data, produce an earnings prep report:

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

Keep each company analysis concise — focus on the numbers and signals, not background.
