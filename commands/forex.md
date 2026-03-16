---
name: forex
description: Get exchange rate for a currency pair
arguments:
  - name: pair
    description: "Currency pair (e.g., eurusd, usdjpy, gbpusd) or leave blank for major pairs overview"
    required: false
---

If a specific pair is provided ("$ARGUMENTS"), use `terminalq_get_forex` with that pair.

If no pair is provided, fetch the major pairs: eurusd, usdjpy, gbpusd, usdchf, usdcad, audusd.

Present each pair showing:

- Current rate and date
- Daily change (absolute and %)
- Recent trend direction over the last 5-10 observations

For a single pair, also show a mini sparkline of the last 30 data points.
