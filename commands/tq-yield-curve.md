---
name: tq-yield-curve
description: Plot the current US Treasury yield curve
---

Plot the current US Treasury yield curve using FRED data.

**Steps:**

1. Fetch yields for these maturities by calling `terminalq_get_economic_indicator` for each:
   - `2y_yield` (2-Year)
   - `10y_yield` (10-Year)
   - `30y_yield` (30-Year)
   - `fed_funds` (Fed Funds Rate, as the short-end anchor)
   - `yield_spread` (10Y-2Y spread, for reference)

2. Build the maturity labels and yield values in order:
   - Maturities: ["FFR", "2Y", "10Y", "30Y"]
   - Yields: [fed_funds latest, 2y latest, 10y latest, 30y latest]

3. Use `terminalq.charts.yield_curve_chart(maturities, yields, title="US Treasury Yield Curve")` to render the chart.

4. Present the output as:
   - The yield curve chart in a code block (so alignment is preserved)
   - Below the chart, a summary table:

```
US Treasury Yield Curve

  4.80 ┤
  4.60 ┤──╮
  4.40 ┤  ╰──╮
  4.20 ┤     ╰────────────╮
  4.00 ┤                  ╰──────

  FFR          2Y          10Y          30Y

  Spread: +0.35%  (FFR: 4.58%  vs  30Y: 4.22%)

Maturity    Yield     vs FFR
FFR         4.58%       —
2Y          4.35%     -0.23%
10Y         4.18%     -0.40%
30Y         4.22%     -0.36%

10Y-2Y Spread: -0.17% (from FRED T10Y2Y series)
```

5. Add commentary:
   - If the curve is inverted (short yields > long yields), note this and explain what it historically signals.
   - If the spread is positive and steep (>1%), note the normal yield curve.
   - Comment on where the Fed Funds Rate sits relative to the curve.
