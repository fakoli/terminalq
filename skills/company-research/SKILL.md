---
name: company-research
description: >-
  Deep-dive research report on a single company covering financials, technicals, analyst ratings,
  news catalysts, and portfolio fit. Use this skill when you need to research a stock, perform
  due diligence, or want a comprehensive company analysis. Ask to "research AAPL", "deep dive
  into NVDA", "analyze company PINS", "stock analysis", "tell me about MSFT", "due diligence
  on AMZN", or "look into GOOG" to trigger this workflow. Produces a Research Report contract output.
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

After gathering all data, produce a structured research report following the **Research Report** contract in `docs/output-contracts.md`:

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

**Data Freshness:** Include a table noting each data source, how recent it is, and confidence level (High/Moderate/Low per `docs/output-contracts.md`).

**Disclaimer:** End with the standard disclaimer from `docs/output-contracts.md`.

Format as a professional research brief — concise, data-driven, with clear section headers.

## Failure Modes

| Failure Mode | Signal | Response |
|---|---|---|
| Financials unavailable | All 3 `terminalq_get_financials` calls return errors | Flag that financial analysis is unavailable; focus on technicals, ratings, and news |
| Invalid ticker | `terminalq_get_company_profile` returns error | Stop and ask user to verify the ticker symbol |
| Technicals fail | `terminalq_get_technicals` errors | Skip Technical Picture section; note it in Data Freshness |
| Allocation unavailable | `terminalq_get_allocation` fails | Skip Portfolio Fit section; note portfolio data was unavailable |
| Partial financials | Only 1-2 of 3 financial statement types return | Analyze what's available; note which statements are missing |
| Stale news | `terminalq_get_news` returns old articles (>14 days) | Note in Recent Catalysts that no recent news was found |

## When Not to Use

- **Do not use** for buy/sell decisions — use `trade-research` instead (it includes portfolio fit and position sizing)
- **Do not use** for broad market context — use `market-overview` instead
- **Do not use** for earnings-specific prep — use `earnings-preview` instead
