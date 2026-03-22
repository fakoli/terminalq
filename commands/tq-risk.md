---
name: tq-risk
description: Compute portfolio risk metrics (Sharpe, Sortino, drawdown, VaR, beta)
arguments:
  - name: period
    description: "Analysis period: 6mo, 1y, 2y (default 1y)"
    required: false
---

Use `terminalq_compute_portfolio_risk` with the specified period (default "1y").

Present the risk report showing:

- **Return**: Annualized return vs SPY benchmark
- **Volatility**: Annualized standard deviation
- **Sharpe Ratio**: Risk-adjusted return (>1 good, >2 excellent)
- **Sortino Ratio**: Downside risk-adjusted return
- **Max Drawdown**: Worst peak-to-trough decline
- **VaR (95%)**: Expected worst daily loss 19 out of 20 days
- **Beta vs SPY**: Market sensitivity (1.0 = market, <1 defensive, >1 aggressive)

End with a 2-3 sentence risk assessment of the portfolio.
