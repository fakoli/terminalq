---
name: ingest
description: Import or update portfolio data from brokerage statements, CSVs, or pasted text
arguments:
  - name: type
    description: "What to ingest: holdings, rsu, accounts, watchlist, or etf-classes"
    required: false
---

Help the user import financial data into TerminalQ's private data directory (`~/.terminalq/`).

**Data directory**: All private reference data lives in `~/.terminalq/` (outside the git repo, never committed).

If no type is specified, show what files exist in `~/.terminalq/` and their last-modified dates, then ask what the user wants to update.

## For each type:

### holdings
Target: `~/.terminalq/portfolio-holdings.md`

Ask the user to paste their brokerage statement data. Accept any of these formats:
- **CSV** from Fidelity, Schwab, or other brokerages (parse columns automatically)
- **Pasted table** from a brokerage website (detect columns)
- **Manual entry** (symbol, shares, cost basis, market value)

Convert to the expected markdown format:
```markdown
# Portfolio Holdings (as of [DATE])

## [Account Name] ([ID])

| Symbol | Name | Shares | Cost Basis | Market Value | Unrealized G/L |
|--------|------|--------|------------|--------------|----------------|
| VTI | Vanguard Total Stock Market ETF | 100 | $25,000.00 | $28,500.00 | $3,500.00 |
```

Group by account. Calculate Unrealized G/L if not provided (Market Value - Cost Basis).
Write the result to `~/.terminalq/portfolio-holdings.md`.

### rsu
Target: `~/.terminalq/rsu-schedule.md`

Ask the user to provide their RSU grant details: grant date, total value, vesting schedule (cliff + monthly/quarterly). Generate the markdown table with dates and estimated values.

### accounts
Target: `~/.terminalq/accounts.md`

Ask for account inventory: institution, type, last 4 digits of account number, advisor.

### watchlist
Target: `~/.terminalq/watchlist.md`

Ask for symbols to watch. Accept a comma-separated list or one per line. Optionally add notes. Use `terminalq_get_company_profile` to auto-fill company names.

### etf-classes
Target: `~/.terminalq/etf-classifications.md`

Read the current portfolio holdings, identify all ETF symbols, and auto-classify them using `terminalq_get_company_profile` for each. Map to asset classes (Equity, Fixed Income, Cash) and regions (US, International, EM). Write the classification table.

## Important
- Always write to `~/.terminalq/`, never to the repo's `reference/` directory
- Show the user what will be written before writing it
- Back up existing files before overwriting (copy to `~/.terminalq/[file].backup`)
