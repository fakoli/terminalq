# TerminalQ Output Contracts

Every skill output MUST conform to one of the contracts below. Contracts define **required sections** — each section must appear as a level-2 or level-3 markdown heading. Optional sections are marked. Every contract includes a mandatory **Data Freshness** footer and **Disclaimer**.

---

## Market Briefing

**Used by:** `market-overview`

| # | Section | Required | Description |
|---|---------|----------|-------------|
| 1 | Market Mood | Yes | Risk-on vs risk-off assessment from VIX, TLT, GLD signals |
| 2 | Index Snapshot | Yes | Table: index, price, daily change, % change |
| 3 | Style Rotation | Yes | Growth vs value vs small-cap rotation signals |
| 4 | Sector Heatmap | Yes | Embedded sector chart, leading/lagging sectors noted |
| 5 | Macro Dashboard | Yes | Yield curve, inflation, labor market, Fed funds summary |
| 6 | Upcoming Catalysts | Yes | Market-moving events from economic calendar |
| 7 | Portfolio Impact | Yes | Portfolio performance vs SPY, sector exposure flags |
| 8 | Data Freshness | Yes | Source list with cache age (see footer contract below) |
| 9 | Disclaimer | Yes | See disclaimer contract below |

---

## Research Report

**Used by:** `company-research`

| # | Section | Required | Description |
|---|---------|----------|-------------|
| 1 | Company Overview | Yes | Name, sector, industry, market cap, price, 52-week range |
| 2 | Financial Health | Yes | Revenue trend, margins, balance sheet strength, FCF |
| 3 | Valuation | Yes | P/E, P/S, sector comparison |
| 4 | Technical Picture | Yes | Trend, momentum (RSI, MACD), Bollinger Bands, price chart |
| 5 | Bull Case | Yes | 3-4 data-driven bullish points |
| 6 | Bear Case | Yes | 3-4 data-driven bearish points |
| 7 | Analyst Consensus | Yes | Rating distribution, price target range, upside/downside |
| 8 | Recent Catalysts | Yes | Key news affecting the stock |
| 9 | Portfolio Fit | Yes | Position context, diversification impact |
| 10 | Data Freshness | Yes | Source list with cache age |
| 11 | Disclaimer | Yes | See disclaimer contract below |

---

## Portfolio Scorecard

**Used by:** `portfolio-health`

| # | Section | Required | Description |
|---|---------|----------|-------------|
| 1 | Portfolio Scorecard | Yes | Total value, daily P&L, top/bottom performers |
| 2 | Risk Assessment | Yes | Sharpe, Sortino, max drawdown, VaR, beta |
| 3 | Allocation Analysis | Yes | Chart, asset class breakdown, concentration warnings |
| 4 | RSU Impact | Conditional | Upcoming vests, unvested value, concentration risk. Skip if no RSU schedule found. |
| 5 | Performance vs Benchmark | Yes | Return vs SPY, risk-adjusted comparison |
| 6 | Action Items | Yes | Rebalancing, tax awareness, concentration reduction |
| 7 | Data Freshness | Yes | Source list with cache age |
| 8 | Disclaimer | Yes | See disclaimer contract below |

---

## Economic Brief

**Used by:** `economic-outlook`

| # | Section | Required | Description |
|---|---------|----------|-------------|
| 1 | Business Cycle Position | Yes | Current phase (early/mid/late expansion, contraction) with evidence |
| 2 | Inflation Dashboard | Yes | CPI, PCE trends, direction, Fed policy implications |
| 3 | Labor Market | Yes | Unemployment, claims, payrolls, assessment |
| 4 | Yield Curve Analysis | Yes | Chart, inversion status, shape signal |
| 5 | Fed Policy Outlook | Yes | Current rate, likely direction, timeline |
| 6 | Currency & Commodities | Yes | Dollar, gold, oil, major forex |
| 7 | Portfolio Implications | Yes | Asset class positioning for current macro regime |
| 8 | Upcoming Catalysts | Yes | Important economic releases and expected impact |
| 9 | Data Freshness | Yes | Source list with cache age |
| 10 | Disclaimer | Yes | See disclaimer contract below |

---

## Trade Decision Brief

**Used by:** `trade-research`

| # | Section | Required | Description |
|---|---------|----------|-------------|
| 1 | Investment Thesis | Yes | Bull case, bear case, one-line summary |
| 2 | Valuation Assessment | Yes | P/E, P/S, analyst target range, upside/downside |
| 3 | Technical Entry Point | Yes | RSI, MACD, support/resistance, timing assessment |
| 4 | Portfolio Fit Analysis | Yes | Allocation impact, sector exposure, correlation |
| 5 | Position Sizing | Yes | Suggested size based on portfolio and conviction |
| 6 | Risk Management | Yes | Stop-loss, max loss, account selection |
| 7 | Decision Summary | Yes | BUY / WAIT / AVOID with rationale and conditions |
| 8 | Data Freshness | Yes | Source list with cache age |
| 9 | Disclaimer | Yes | See disclaimer contract below |

---

## Earnings Preview

**Used by:** `earnings-preview`

| # | Section | Required | Description |
|---|---------|----------|-------------|
| 1 | Earnings Calendar | Yes | Table of holdings with earnings dates, sorted by date |
| 2 | Per-Company Analysis | Yes | For each: consensus, track record, technical setup, sentiment, position risk |
| 3 | Portfolio Earnings Risk Summary | Yes | Total exposure, highest-risk positions |
| 4 | Action Items | Yes | Trim candidates, upside setups, hedging suggestions |
| 5 | Data Freshness | Yes | Source list with cache age |
| 6 | Disclaimer | Yes | See disclaimer contract below |

---

## Cross-Cutting Contracts

### Data Freshness Footer

Every skill output must end with a **Data Freshness** section:

```
### Data Freshness
| Source | Data Age | Confidence |
|--------|----------|------------|
| Finnhub quotes | Live | High |
| FRED macro | Cached 4h | High |
| yfinance OHLCV | Cached 1h | High |
| Finnhub earnings | Cached 24h | Moderate |
```

**Confidence levels:**
- **High** — live data or cache < 1 hour
- **Moderate** — cached 1-24 hours
- **Low** — cached > 24 hours, or data source returned errors and fallback was used

If a data source failed entirely, note it: `| Finnhub financials | UNAVAILABLE | Low — using cached fallback |`

### Disclaimer

Every skill output must include:

> *This analysis is for informational and educational purposes only — not financial advice. Data may be delayed or incomplete. Always do your own due diligence before making investment decisions.*
