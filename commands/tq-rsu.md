---
name: tq-rsu
description: Show RSU vesting schedule and current employer stock holdings
---

1. Use `terminalq_get_rsu_schedule` to get the vesting schedule.
2. From the RSU schedule, identify the employer stock ticker symbol.
3. Use `terminalq_get_quote` with that symbol to get the current stock price.
4. Use `terminalq_get_portfolio` to find current holdings of the RSU stock.

Present:

- **Current Holdings**: Shares held at current price = current value
- **Upcoming Vests**: Show the next 3-4 vesting dates with estimated share count and value at current price
- **Projected Vesting Value**: Sum of upcoming vests at current stock price
- **Concentration Warning**: What % of total investable assets is the RSU stock (including unvested RSUs)

If the grant conversion price depends on a future average closing price, show dollar values from the grant letter until the conversion is finalized.
