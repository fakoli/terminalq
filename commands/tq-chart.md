---
name: tq-chart
description: Generate a price chart for a symbol
arguments:
  - name: args
    description: "Symbol and optional period/type (e.g., 'AAPL', 'AAPL 3mo', 'AAPL 6mo candlestick')"
    required: true
---

Parse the arguments "$ARGUMENTS" to extract:

- **symbol**: the ticker symbol (first word, e.g., AAPL)
- **period**: optional lookback period (1mo, 3mo, 6mo, 1y, 2y, 5y). Default: 6mo
- **chart_type**: optional type — "line" (default) or "candlestick"

Examples: "AAPL" → symbol=AAPL, period=6mo, chart_type=line. "AAPL 3mo" → symbol=AAPL, period=3mo, chart_type=line. "AAPL 1y candlestick" → symbol=AAPL, period=1y, chart_type=candlestick.

**Steps:**

1. Call `terminalq_get_historical` with the symbol and period (interval="1d").

2. From the result, extract the `prices` array (each item has: date, open, high, low, close, volume).

3. Use the `terminalq.charts` module to render the chart:
   - If chart_type is "candlestick": call `charts.candlestick_chart(prices, title=f"{symbol} — {period}")`.
   - If chart_type is "line": extract close prices and date labels, then call `charts.line_chart(closes, labels=dates, title=f"{symbol} — {period}")`.

4. Also generate a sparkline: `charts.sparkline(closes, label=symbol)`.

5. Present the output as:
   - The chart (rendered as a code block so alignment is preserved)
   - Below the chart: the sparkline
   - A brief summary: period start price, end price, high, low, total return %

Example output format:

```
AAPL — 6mo

 195.00 ┤                                              ╭─╮
 190.00 ┤                                         ╭────╯  │
 185.00 ┤                              ╭──────────╯       ╰──
 ...

2024-09-15                    2024-12-15                    2025-03-15

AAPL  ▁▂▃▃▄▅▅▆▇█▇▆▅

Open: $171.22  Close: $192.53  High: $198.11  Low: $168.30  Return: +12.4%
```
