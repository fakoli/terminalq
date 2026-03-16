---
name: historical
description: Get historical price data for a symbol
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, PINS)
    required: true
  - name: period
    description: Lookback period (1mo, 3mo, 6mo, 1y, 2y, 5y). Default 1y.
    required: false
---

Use the `terminalq_get_historical` MCP tool to get historical OHLCV data for "$ARGUMENTS".

If a period is specified (e.g., "AAPL 6mo"), pass it as the period parameter. Default is 1y.

Present the results as:

- **Period Summary**: Date range, number of trading days
- **Price Range**: 52-week high/low (or period high/low), current price
- **Performance**: Total return over the period (%)
- **Key Levels**: Show the first, last, high, and low prices

If the data has more than 20 points, show a summary table of monthly closes rather than every daily bar.
