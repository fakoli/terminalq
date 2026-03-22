---
name: tq-filings
description: Search SEC filings for a company
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, PINS)
    required: true
  - name: type
    description: "Filing type filter: 10-K, 10-Q, 8-K, DEF 14A, etc. Default: all."
    required: false
---

Use the `terminalq_get_filings` MCP tool to get SEC filings for "$ARGUMENTS".

If a filing type is specified (e.g., "PINS 10-K"), pass it as the filing_type parameter.

Present each filing with:

- Filing type and date
- Description
- Link to the document on SEC.gov

Group by filing type if showing all types.
