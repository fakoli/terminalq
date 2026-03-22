---
name: tq-compare
description: Compare price performance of multiple symbols
arguments:
  - name: symbols
    description: "Comma-separated symbols (e.g., AAPL,MSFT,GOOGL)"
    required: true
---

Parse the symbols from "$ARGUMENTS" — split on commas and/or spaces to get a list of ticker symbols. Optionally, the user may append a period (e.g., "AAPL,MSFT,GOOGL 6mo"). Default period is 6mo.

**Steps:**

1. For each symbol, call `terminalq_get_historical` with the symbol and period (interval="1d"). Use the batch approach — make all calls, then collect results.

2. From each result, extract the close prices and dates from the `prices` array.

3. Build a series dict: `{symbol: [close_prices...]}` and a shared labels list (dates from the first symbol).

4. Use `terminalq.charts.comparison_chart(series, labels=dates, title=f"Performance Comparison — {period}")` to render the normalized % return chart.

5. Also generate a sparkline for each symbol: `charts.sparkline(closes, label=symbol)`.

6. Present the output as:
   - The comparison chart in a code block
   - Sparklines for each symbol
   - A summary table showing each symbol's: start price, end price, total return %, and best/worst day

Example output format:

```
Performance Comparison — 6mo

 15.00 ┤          ╭──────╮
 10.00 ┤     ╭────╯      ╰───────╮
  5.00 ┤ ────╯                    ╰──────
  0.00 ┤╮                                ──────
 -5.00 ┤╰───────╮
-10.00 ┤        ╰──────────────────────────────

── AAPL (+12.3%)  ╌╌ MSFT (+8.7%)  ┈┈ GOOGL (-3.2%)

AAPL   ▁▂▃▄▅▅▆▇▇█▇▆
MSFT   ▃▃▄▄▅▅▆▆▇▇▆▆
GOOGL  ▇▆▅▅▄▃▃▂▂▁▂▂

Symbol  Start     End       Return
AAPL    $171.22   $192.53   +12.3%
MSFT    $378.91   $411.88   +8.7%
GOOGL   $141.80   $137.27   -3.2%
```
