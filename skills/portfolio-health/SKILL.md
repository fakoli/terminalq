---
name: portfolio-health
description: >-
  Comprehensive portfolio health check covering performance, risk metrics, asset allocation,
  RSU exposure, and benchmark comparison. Use this skill when you want to review your portfolio,
  check diversification, assess risk, or understand RSU concentration. Ask "how is my portfolio",
  "portfolio health", "portfolio review", "check my portfolio", "portfolio performance",
  "my holdings", or "am I diversified" to trigger this workflow. Produces a Portfolio Scorecard contract output.
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

After gathering all data, produce a structured health check following the **Portfolio Scorecard** contract in `docs/output-contracts.md`:

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

**Data Freshness:** Include a table noting each data source, how recent it is, and confidence level (High/Moderate/Low per `docs/output-contracts.md`).

**Disclaimer:** End with the standard disclaimer from `docs/output-contracts.md`.

Keep it practical — scorecard first, then details, then actionable recommendations.

## Failure Modes

| Failure Mode | Signal | Response |
|---|---|---|
| Portfolio data missing | `terminalq_get_portfolio_live` fails or returns empty | Stop and instruct user to run `/tq-ingest` to set up portfolio data |
| Risk metrics fail | `terminalq_get_risk_metrics` errors | Skip Risk Assessment section; note that risk analysis requires historical data |
| No RSU schedule | `terminalq_get_rsu_schedule` returns empty or errors | Skip RSU Impact section entirely; note in output that no RSU data was found |
| Allocation tool fails | `terminalq_get_allocation` errors | Skip Allocation Analysis chart; try to estimate allocation from portfolio holdings directly |
| Stale portfolio prices | Quote data is from previous close | Note in Data Freshness that prices are from last close (markets may be closed) |

## When Not to Use

- **Do not use** if portfolio data hasn't been ingested — run `/tq-ingest` first
- **Do not use** for individual stock decisions — use `trade-research` instead
- **Do not use** for broad market context — use `market-overview` instead
