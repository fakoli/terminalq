---
name: ratings
description: Get analyst ratings and price targets for a stock
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, PINS, NVDA)
    required: true
---

Use the `terminalq_get_analyst_ratings` MCP tool to get analyst consensus and price targets for "$ARGUMENTS".

Present the results showing:

- **Consensus Rating**: Strong Buy / Buy / Hold / Sell with total analyst count
- **Price Target**: low, mean, median, and high targets
- **Upside/Downside**: % from current price to mean target (fetch current price with `terminalq_get_quote`)
- **Trend**: How ratings have shifted over the last 3-6 months (improving or deteriorating)

If the symbol is in our portfolio, note our position size and what the consensus implies.
