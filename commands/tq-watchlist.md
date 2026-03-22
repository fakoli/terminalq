---
name: tq-watchlist
description: Show watchlist with live quotes and daily changes
---

Use `terminalq_get_watchlist` to load the watchlist, then `terminalq_get_quotes_batch` to get live prices for all symbols.

Present as a table showing: Symbol, Name, Price, Change ($), Change (%), and any notes.

Highlight the biggest movers (top gainer and biggest loser) at the top.

Sort by absolute percent change descending to show most active names first.
