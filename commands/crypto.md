---
name: crypto
description: Get cryptocurrency prices and market data
arguments:
  - name: symbol
    description: "Crypto ticker (e.g., BTC, ETH, SOL) or comma-separated list, or leave blank for top coins"
    required: false
---

If specific symbol(s) provided ("$ARGUMENTS"), use `terminalq_get_crypto_quote` for a single symbol or `terminalq_get_crypto_batch` for multiple.

If no symbol provided, fetch the default set: BTC, ETH, SOL, ADA, AVAX, LINK, DOT, UNI.

Present each coin showing:
- Price with 24h change ($ and %)
- 7d and 30d change %
- Market cap and rank
- 24h volume
- Distance from ATH
