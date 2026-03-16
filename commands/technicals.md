---
name: technicals
description: Get technical analysis indicators for a symbol
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, PINS)
    required: true
---

Use the `terminalq_get_technicals` MCP tool to get technical indicators for "$ARGUMENTS".

Present the results as a technical analysis report:

**Trend (Moving Averages)**

- SMA 20/50/200 values and whether price is above/below each
- Golden Cross (SMA50 > SMA200) or Death Cross status
- EMA 12/26/50 values

**Momentum**

- RSI: value and signal (overbought >70, oversold <30, neutral)
- MACD: line, signal, histogram — bullish or bearish crossover

**Volatility**

- Bollinger Bands: upper/middle/lower, bandwidth, %B position
- ATR: current value (indicates daily price range)

**Overall Signal**: Aggregate bullish/bearish/neutral assessment

If the symbol is in our portfolio, add context about what the technicals suggest for the position.
