---
name: financials
description: Get financial statements from SEC filings
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, PINS)
    required: true
  - name: statement
    description: "Statement type: income, balance_sheet, or cash_flow. Default: income."
    required: false
---

Use the `terminalq_get_financials` MCP tool to get financial statement data for "$ARGUMENTS".

If a statement type is specified (e.g., "AAPL balance_sheet"), pass it as the statement parameter.

Present the results as a clean financial table showing:
- **For income statement**: Revenue, Cost of Revenue, Gross Profit, Operating Income, Net Income, EPS — across 4 annual periods
- **For balance sheet**: Total Assets, Current Assets, Cash, Total Liabilities, Current Liabilities, Long-term Debt, Stockholders' Equity
- **For cash flow**: Operating Cash Flow, Investing Cash Flow, Financing Cash Flow, Capital Expenditure

Include year-over-year growth rates for key metrics. Highlight any significant trends (accelerating/decelerating revenue, margin expansion/compression).
