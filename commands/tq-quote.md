---
name: tq-quote
description: Get a real-time stock/ETF quote
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, VTI, PINS)
    required: true
---

Use the `terminalq_get_quote` MCP tool to get a real-time quote for the ticker symbol "$ARGUMENTS".

Present the result in a clean format showing:

- Current price with daily change ($ and %)
- Day range (low - high)
- Previous close

If the symbol is in our portfolio (check with `terminalq_get_portfolio`), also show how many shares we hold and the current position value.
