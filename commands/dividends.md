---
name: dividends
description: Get dividend history and yield for a symbol
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, VTI, QUAL)
    required: true
---

Use the `terminalq_get_dividends` MCP tool to get dividend data for "$ARGUMENTS".

Present the results showing:
- **Current Yield**: Annual dividend / current price
- **Annual Dividend**: Sum of last 4 payments
- **Payout Frequency**: Monthly, quarterly, semi-annual, or annual
- **Recent Payments**: Last 4-8 dividend payments with dates and amounts
- **Trend**: Is the dividend growing, stable, or declining?

If the symbol is in our portfolio, also show the projected annual income from this holding (annual dividend × shares held). Use `terminalq_get_portfolio` to check.
