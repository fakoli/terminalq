---
name: portfolio-health
description: Portfolio health check — performance, risk, allocation, RSU exposure
triggers:
  - how is my portfolio
  - portfolio health
  - portfolio review
  - portfolio check
  - check my portfolio
  - portfolio performance
  - my holdings
  - am I diversified
---

Perform a comprehensive portfolio health check in two steps:

**Step 1:** Call these tools in parallel to gather portfolio and RSU data:

1. `terminalq_get_portfolio_live()` — current holdings with live prices and daily P&L
2. `terminalq_get_risk_metrics("1y")` — Sharpe, Sortino, VaR, beta, max drawdown
3. `terminalq_get_allocation()` — asset class breakdown and concentration risk
4. `terminalq_chart_allocation()` — visual allocation chart
5. `terminalq_get_rsu_schedule()` — upcoming RSU vests

**Step 2:** From the RSU schedule results, identify the RSU ticker symbol. Then call `terminalq_get_quote(rsu_symbol)` to get the current price for RSU valuation. If no RSU schedule exists, skip this step.

After gathering all data, produce a structured health check:

**Portfolio Scorecard:**

- Total value (live)
- Daily P&L ($ and %)
- Top 3 performers today
- Bottom 3 performers today

**Risk Assessment:**

- Sharpe ratio (>1 good, >2 excellent, <0.5 needs attention)
- Sortino ratio (downside risk awareness)
- Maximum drawdown (how much has been lost peak-to-trough)
- VaR at 95% (worst expected daily loss)
- Beta vs SPY (>1 = more volatile than market)

**Allocation Analysis:**

- Embed the allocation chart
- Asset class breakdown (US equity, international, fixed income, alternatives)
- Concentration warnings: flag any single stock > 10% of portfolio
- RSU stock exposure: combine direct holdings + unvested RSUs to show total RSU-stock exposure as % of net worth

**RSU Impact:**

- Upcoming vests (dates, share counts, estimated value at current price from Step 2)
- Total unvested RSU value
- If RSU stock concentration (held + unvested) > 15%, flag as a risk

**Performance vs Benchmark:**

- Compare portfolio return to SPY over the same period
- Risk-adjusted comparison (Sharpe vs SPY Sharpe)

**Action Items:**

- Rebalancing suggestions if allocation has drifted significantly
- Tax awareness: note which accounts are taxable vs Roth (sell from Roth first for tax efficiency)
- Concentration reduction plan if RSU stock > 15%

Keep it practical — scorecard first, then details, then actionable recommendations.
