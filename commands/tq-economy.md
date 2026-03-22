---
name: tq-economy
description: Get economic indicators or a full macro dashboard
arguments:
  - name: indicator
    description: "Specific indicator (gdp, cpi, unemployment, fed_funds, 10y_yield, yield_spread, etc.) or leave blank for full dashboard"
    required: false
---

If a specific indicator is provided ("$ARGUMENTS"), use `terminalq_get_economic_indicator` with that indicator name.

If no indicator is provided, use `terminalq_get_macro_dashboard` to get the full dashboard.

**For a single indicator**, present:

- Current value and date
- Trend over last 12 observations
- Context (what this indicator measures, why it matters)

**For the full dashboard**, present a macro overview:

- **Growth**: GDP trend
- **Inflation**: CPI, Core CPI levels and direction
- **Labor**: Unemployment rate, claims trend
- **Rates**: Fed Funds, 10Y yield, 2Y yield
- **Yield Curve**: 10Y-2Y spread — is it inverted (recession signal)?
- **Sentiment**: Consumer sentiment direction

End with a 2-3 sentence economic outlook synthesis.
