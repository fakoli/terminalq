---
name: portfolio
description: Show portfolio holdings with live prices and daily P&L
---

Use the `terminalq_get_portfolio_live` MCP tool to get all holdings with real-time prices.

Present the results as a table grouped by account (use the account names from the data).

For each holding show: Symbol, Shares, Live Price, Live Value, Daily Change ($), Daily Change (%).

At the top, show:

- **Total Portfolio Value** (sum of all live values)
- **Total Daily Change** (sum of all daily changes)

At the bottom, show:

- **Asset Allocation Summary**: Group by category (US Equity, International, Emerging Markets, Fixed Income, Cash)
- **Top 5 Holdings by Value**
- **Top Concentration**: What % of total portfolio is the single largest stock position

Use green for gains, red for losses in your formatting.
