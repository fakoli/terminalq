---
name: rsu
description: Show Pinterest RSU vesting schedule and current PINS holdings
---

1. Use `terminalq_get_rsu_schedule` to get the vesting schedule.
2. Use `terminalq_get_quote` with symbol "PINS" to get the current stock price.

Present:

- **Current PINS Holdings**: 2,722 shares at current price = current value
- **Upcoming Vests**: Show the next 3-4 vesting dates with estimated share count and value at current price
- **Total 2026 Projected Vesting Value**: Sum of all 2026 vests at current PINS price
- **Concentration Warning**: What % of total investable assets is PINS (including unvested RSUs)

Note: The grant conversion price (shares per vest) depends on the 30-day average closing price from Feb 18 - Mar 31, 2026. Until that's finalized, show dollar values from the grant letter.
