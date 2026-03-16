---
name: company-research
description: Deep-dive research report on a company — financials, technicals, ratings, news
triggers:
  - research
  - deep dive
  - analyze company
  - company analysis
  - stock analysis
  - tell me about
  - due diligence
  - look into
arguments:
  - name: symbol
    description: Ticker symbol to research (e.g., AAPL, PINS, NVDA)
    required: true
---

Generate a comprehensive research report for "$ARGUMENTS" by calling these tools in parallel:

1. `terminalq_get_company_profile(symbol)` — company overview, sector, market cap
2. `terminalq_get_quote(symbol)` — current price and daily movement
3. `terminalq_get_financials(symbol, "income", 4)` — 4 years of income statements
4. `terminalq_get_financials(symbol, "balance_sheet", 4)` — balance sheet
5. `terminalq_get_financials(symbol, "cash_flow", 4)` — cash flow statement
6. `terminalq_get_technicals(symbol)` — SMA, RSI, MACD, Bollinger Bands
7. `terminalq_get_analyst_ratings(symbol)` — consensus rating and price targets
8. `terminalq_get_news(symbol, 14)` — last 2 weeks of news
9. `terminalq_get_earnings(symbol)` — EPS history and estimates
10. `terminalq_chart_price(symbol, "1y", "line")` — 1-year price chart
11. `terminalq_get_allocation()` — current portfolio allocation (for portfolio fit analysis)

After gathering all data, produce a structured research report:

**Company Overview:** Name, sector, industry, market cap, current price, 52-week context.

**Financial Health:**

- Revenue trend (growing/flat/declining, YoY growth rate)
- Margin analysis (gross margin, operating margin, net margin trends)
- Balance sheet strength (debt-to-equity, current ratio, cash position)
- Cash flow quality (free cash flow trend, FCF margin)

**Valuation:**

- P/E ratio (from earnings data — trailing EPS vs price)
- P/S ratio (from revenue vs market cap)
- Compare to sector averages if available

**Technical Picture:**

- Trend direction (above/below key SMAs)
- Momentum (RSI overbought/oversold, MACD signal)
- Bollinger Band position (near upper/lower/middle)
- Embed the price chart

**Bull Case (3-4 points):** Based on financial trends, analyst sentiment, and recent news.

**Bear Case (3-4 points):** Risks from financial weaknesses, technical signals, or news sentiment.

**Analyst Consensus:** Rating distribution, average price target, upside/downside %.

**Recent Catalysts:** Key news items that may affect the stock.

**Portfolio Fit:** If the user already holds this stock, note the position size. If not, note whether it would add diversification or increase concentration.

Format as a professional research brief — concise, data-driven, with clear section headers.
