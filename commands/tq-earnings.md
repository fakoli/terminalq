---
name: tq-earnings
description: Get earnings history and estimates for a company
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, PINS)
    required: true
---

Use the `terminalq_get_earnings` MCP tool to get earnings data for "$ARGUMENTS".

Present the results showing:

- **Earnings History**: Last 8 quarters with actual EPS, estimate, and surprise (beat/miss)
- **Beat Rate**: How often the company beats estimates
- **Trend**: Is EPS growing, declining, or flat?

Also use `terminalq_get_quote` to show the current stock price for P/E context.
