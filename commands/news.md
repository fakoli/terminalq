---
name: news
description: Get recent news for a ticker or portfolio holdings
arguments:
  - name: symbol
    description: Ticker symbol (e.g., PINS, AAPL). Leave blank for portfolio-wide news.
    required: false
---

If a symbol is provided ("$ARGUMENTS"), use `terminalq_get_news` to get recent news for that ticker.

If no symbol is provided, get news for the top 5 portfolio holdings by value using `terminalq_get_portfolio` first to identify them, then `terminalq_get_news` for each.

Present each article with:

- Headline
- Source and date
- Brief summary (1-2 sentences)

Group by ticker if showing portfolio-wide news. Flag any articles that could materially impact portfolio value.
