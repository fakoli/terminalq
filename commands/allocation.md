---
name: allocation
description: Analyze portfolio allocation by asset class, region, and style
---

Use `terminalq_compute_allocation` to analyze the portfolio breakdown.

Present the allocation report with:
- **By Asset Class**: US Equity, International Equity, Emerging Markets, Fixed Income, Cash — with % weights
- **By Region**: US, Developed ex-US, Emerging Markets, International
- **By Sub-Class**: Growth vs Value vs Blend, Large vs Mid vs Small cap
- **Top 10 Holdings**: Largest positions by weight
- **Concentration Risk**: Any single holding >10% of portfolio, any asset class >60%

Flag any unclassified holdings. Suggest rebalancing if allocation is significantly off from a balanced target.
