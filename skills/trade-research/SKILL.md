---
name: trade-research
description: Investment decision support — thesis, valuation, portfolio fit, entry point
triggers:
  - should I buy
  - should I sell
  - trade idea
  - evaluate
  - investment thesis
  - is it a good time to buy
  - trade research
  - add to my position
arguments:
  - name: symbol
    description: Ticker symbol to evaluate (e.g., AAPL, NVDA, AMZN)
    required: true
---

Provide comprehensive investment decision support for "$ARGUMENTS" by calling these tools in parallel:

**Round 1 — Company & Market Data (parallel):**

1. `terminalq_get_company_profile(symbol)` — overview
2. `terminalq_get_quote(symbol)` — current price
3. `terminalq_get_financials(symbol, "income", 4)` — revenue and earnings trends
4. `terminalq_get_financials(symbol, "balance_sheet", 4)` — financial strength
5. `terminalq_get_financials(symbol, "cash_flow", 4)` — cash generation
6. `terminalq_get_technicals(symbol)` — technical indicators
7. `terminalq_get_analyst_ratings(symbol)` — Wall Street consensus
8. `terminalq_get_news(symbol, 14)` — recent news
9. `terminalq_get_earnings(symbol)` — earnings history
10. `terminalq_chart_price(symbol, "1y", "line")` — price chart

**Round 2 — Portfolio Context (parallel):**

11. `terminalq_get_allocation()` — current portfolio allocation
12. `terminalq_get_risk_metrics("1y")` — portfolio risk baseline

After gathering all data, produce an investment decision brief:

**Investment Thesis:**

- Bull case (3-4 data-driven points from financials, growth, and catalysts)
- Bear case (3-4 risk factors from financials, technicals, and news)
- One-line thesis summary

**Valuation Assessment:**

- Current P/E vs historical and sector average
- P/S ratio context
- Analyst price target range (low / average / high) vs current price
- Upside/downside to consensus target

**Technical Entry Point:**

- Is now a good time? (relative to support/resistance levels, trend, momentum)
- RSI: overbought (>70) = poor entry, oversold (<30) = potential opportunity
- Where are the key support levels? (potential stop-loss points)
- MACD trend (bullish/bearish crossover)

**Portfolio Fit Analysis:**

- Current allocation by asset class — would this stock increase or decrease concentration?
- Sector exposure — does the portfolio already have heavy exposure to this sector?
- Correlation with existing holdings — does this add diversification?
- If already held, should the position be increased?

**Position Sizing Suggestion:**

- Based on current portfolio size, conviction level, and risk
- Start with 1-2% for new positions, 3-5% for high-conviction
- Account for total sector exposure after adding

**Risk Management:**

- Suggested stop-loss level (technical support or % max loss)
- Position sizing that keeps max loss within risk tolerance
- Which account to buy in (taxable vs Roth) for tax efficiency

**Decision Summary:**

- Clear BUY / WAIT / AVOID recommendation with rationale
- If WAIT: what conditions would make it actionable
- If BUY: suggested entry price range, position size, and stop-loss

This is analysis and education, not financial advice. Always note that the user should do their own due diligence.
