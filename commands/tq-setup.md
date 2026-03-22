---
name: tq-setup
description: Interactive onboarding — configure API keys and private data directory for TerminalQ
---

Guide the user through first-time TerminalQ setup. Check what's already configured and only prompt for what's missing.

## Step 1: Check existing configuration

Read `~/.env` to see which API keys are already set. Also check the shell environment. Build a status list:

**Required keys:**
- `FINNHUB_API_KEY` — needed for quotes, news, earnings, analyst ratings
- `FRED_API_KEY` — needed for economic indicators, yield curve, forex, macro dashboard

**Optional keys:**
- `BRAVE_API_KEY` — enables `/tq-search` web search (2,000 free calls/month)
- `POLYGON_API_KEY` — enables Polygon.io fallback for stock data (5 free calls/min)
- `SEC_USER_AGENT` — identifies you to SEC EDGAR (defaults to "TerminalQ user@example.com")

Show the user a status summary like:

```
TerminalQ Setup Status
──────────────────────
FINNHUB_API_KEY:  [found] or [MISSING - required]
FRED_API_KEY:     [found] or [MISSING - required]
BRAVE_API_KEY:    [found] or [not set - optional]
POLYGON_API_KEY:  [found] or [not set - optional]
SEC_USER_AGENT:   [found] or [using default]
```

If all required keys are present, tell the user they're good to go and ask if they want to configure any optional keys or set up their portfolio data directory.

If any required keys are missing, proceed to Step 2.

## Step 2: Guide through each missing key

For each missing **required** key, walk the user through obtaining it using AskUserQuestion. Present the keys one at a time.

### FINNHUB_API_KEY

If missing, tell the user:

```
Finnhub provides real-time stock quotes, company news, earnings data, and analyst ratings.
Their free tier gives you 60 API calls per minute — more than enough for personal use.

To get your free API key:
  1. Go to https://finnhub.io/register
  2. Sign up with your email (no credit card required)
  3. After signing in, your API key is shown on the dashboard at https://finnhub.io/dashboard
  4. Copy the API key (it looks like: d6xxxxxxxxxxxx)
```

Then use AskUserQuestion to ask: "Paste your Finnhub API key (or choose 'Skip' to set it up later)"
- Option 1: "I have my key ready" — then prompt them to enter it
- Option 2: "Skip for now" — move on, warn that quotes/news/earnings won't work

### FRED_API_KEY

If missing, tell the user:

```
FRED (Federal Reserve Economic Data) provides economic indicators, interest rates,
yield curves, forex rates, and the macro dashboard.
Their API is completely free with 120 calls per minute.

To get your free API key:
  1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
  2. Click "Request or view your API keys"
  3. Create a free account if you don't have one
  4. Request an API key — it's approved instantly
  5. Copy the 32-character key (it looks like: abcdef1234567890abcdef1234567890)
```

Then use AskUserQuestion to ask: "Paste your FRED API key (or choose 'Skip' to set it up later)"
- Option 1: "I have my key ready" — then prompt them to enter it
- Option 2: "Skip for now" — move on, warn that economic data/yield curve/forex won't work

## Step 3: Optional keys

After required keys are handled, ask if the user wants to set up optional keys.

Use AskUserQuestion: "Would you like to configure any optional API keys?"
- Option 1: "Brave Search API" — web search for financial research
- Option 2: "Polygon.io API" — fallback stock data provider
- Option 3: "SEC User Agent" — custom identity for SEC EDGAR requests
- Option 4: "Skip optional setup"

### BRAVE_API_KEY (if selected)

```
Brave Search API enables the /tq-search command for web-based financial research.
Free tier: 2,000 searches per month.

To get your API key:
  1. Go to https://brave.com/search/api/
  2. Click "Get Started for Free"
  3. Create an account and select the Free plan
  4. Your API key will be available in the developer dashboard
```

### POLYGON_API_KEY (if selected)

```
Polygon.io provides an alternative stock data source as a fallback.
Free tier: 5 API calls per minute.

To get your API key:
  1. Go to https://polygon.io/
  2. Click "Get your Free API Key"
  3. Sign up (no credit card required for the free tier)
  4. Your API key is on the dashboard after signing in
```

### SEC_USER_AGENT (if selected)

```
SEC EDGAR requires a User-Agent header to identify who's making requests.
The default is "TerminalQ user@example.com" but SEC recommends using your real identity.

Format: "YourName your-email@example.com"
```

## Step 4: Write keys to ~/.env

For each key the user provided, **append** it to `~/.env`. CRITICAL rules:
- If `~/.env` doesn't exist, create it with mode 600 (owner read/write only)
- If `~/.env` exists, DO NOT overwrite — only append new lines
- Before appending, check if the key already exists in the file. If it does, ask the user if they want to update it
- Use the format: `KEY_NAME="value"` (one per line)
- Add a blank line before the TerminalQ section if the file already has content
- Add a comment header the first time: `# TerminalQ API Keys`

Use the Bash tool to append, for example:
```bash
# Check if key already in file
grep -q "^FINNHUB_API_KEY=" ~/.env 2>/dev/null
# If not, append
echo 'FINNHUB_API_KEY="the_key_value"' >> ~/.env
```

Set file permissions if creating new:
```bash
touch ~/.env && chmod 600 ~/.env
```

## Step 5: Verify and set up data directory

After API keys are configured, check if `~/.terminalq/` exists:
- If not, create it and copy example templates from the plugin's `reference/` directory
- If it exists, show what files are there

Tell the user:
```
Your private data directory is ready at ~/.terminalq/

To import your portfolio data, run: /tq-ingest holdings
You can paste brokerage statements, CSVs, or enter positions manually.
```

## Step 6: Final summary

Show a final status with all configured keys and next steps:

```
TerminalQ is ready!

Configured APIs:
  Finnhub    — quotes, news, earnings, ratings
  FRED       — economics, yield curve, forex
  [any optional ones configured]

Next steps:
  /tq-ingest holdings  — Import your portfolio from brokerage data
  /tq-portfolio        — View your holdings with live prices
  /tq-quote AAPL       — Get a real-time stock quote
  /market-overview     — Get a morning market briefing
```

If any required keys were skipped, remind them:
```
Skipped keys (some features will be unavailable):
  FINNHUB_API_KEY — run /tq-setup again to add it
```
