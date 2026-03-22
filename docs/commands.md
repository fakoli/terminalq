# TerminalQ Slash Commands

Slash commands are markdown files in `commands/` that define reusable prompts for Claude. When a user types `/tq-quote AAPL`, Claude reads the corresponding command file and follows its instructions.

## Command Format

Each command is a `.md` file with YAML frontmatter and a markdown instruction body:

```markdown
---
name: command_name
description: Short description shown in command list
arguments:
  - name: arg_name
    description: What this argument is
    required: true
  - name: optional_arg
    description: An optional parameter
    required: false
---

Instructions for Claude to follow when this command is invoked.

The variable "$ARGUMENTS" is replaced with whatever the user typed after the command name.
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Command name (used as `/name`) |
| `description` | yes | Short description for command list |
| `arguments` | no | List of argument definitions |

### Argument Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Argument name |
| `description` | yes | What the argument is for |
| `required` | yes | `true` or `false` |

### The `$ARGUMENTS` Variable

The string `$ARGUMENTS` in the instruction body is replaced with the user's raw input after the command name. For example, if the user types `/tq-quote AAPL`, then `$ARGUMENTS` becomes `"AAPL"`.

For commands with multiple arguments (e.g., `/tq-filings PINS 10-K`), the command instructions should parse the combined string.

---

## Existing Commands

### Market Data Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `/tq-quote SYMBOL` | symbol (required) | Real-time stock/ETF quote |
| `/tq-historical SYMBOL [PERIOD]` | symbol (required), period (optional) | Historical OHLCV data |
| `/tq-dividends SYMBOL` | symbol (required) | Dividend history and yield |
| `/tq-technicals SYMBOL` | symbol (required) | Technical analysis indicators |

### Portfolio Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `/tq-portfolio` | none | All holdings with live prices and daily P&L |
| `/tq-rsu` | none | RSU vesting schedule and employer stock |

### Research Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `/tq-news [SYMBOL]` | symbol (optional) | News for a ticker or top portfolio holdings |
| `/tq-earnings SYMBOL` | symbol (required) | Earnings history and estimates |
| `/tq-financials SYMBOL [STATEMENT]` | symbol (required), statement (optional) | SEC financial statements |
| `/tq-filings SYMBOL [TYPE]` | symbol (required), type (optional) | SEC filing search |

### Economics & Screening Commands

| Command | Arguments | Description |
|---------|-----------|-------------|
| `/tq-economy [INDICATOR]` | indicator (optional) | Single indicator or full macro dashboard |
| `/tq-screen [CRITERIA]` | criteria (optional) | S&P 500 stock screener |

---

## How to Create a New Command

### 1. Create the command file

Create `commands/your_command.md`:

```markdown
---
name: your_command
description: What this command does
arguments:
  - name: symbol
    description: Ticker symbol (e.g., AAPL, PINS)
    required: true
---

Use the `terminalq_get_your_data` MCP tool to get data for "$ARGUMENTS".

Present the results showing:
- Metric 1: value with context
- Metric 2: value with comparison

If the symbol is in our portfolio (check with `terminalq_get_portfolio`),
also show position-specific context.
```

### 2. Writing good command instructions

Commands should tell Claude:

1. **Which MCP tool(s) to call** -- reference them by exact name
2. **How to parse arguments** -- especially for multi-argument commands
3. **How to present results** -- formatting, grouping, what to highlight
4. **When to cross-reference** -- e.g., checking portfolio context

### 3. Best practices

- Keep instructions focused. Claude will interpret and follow them.
- Reference MCP tools by their exact registered name (e.g., `terminalq_get_quote`).
- For multi-argument commands, explain parsing: "If a period is specified (e.g., 'AAPL 6mo'), pass it as the period parameter."
- Include presentation guidance: tables, grouping, color hints, summary statistics.
- Cross-reference portfolio data when it adds context (e.g., "show how many shares we hold").
- Use conditional logic: "If no symbol is provided, get news for top 5 portfolio holdings."

### 4. Example: Multi-tool command

```markdown
---
name: analysis
description: Full analysis of a stock
arguments:
  - name: symbol
    description: Ticker symbol
    required: true
---

Run the following MCP tools for "$ARGUMENTS":
1. `terminalq_get_quote` -- current price
2. `terminalq_get_company_profile` -- company overview
3. `terminalq_get_technicals` -- technical signals
4. `terminalq_get_earnings` -- earnings track record
5. `terminalq_get_financials` with statement="income" -- revenue/profit trends

Synthesize into a research report with:
- **Overview**: Company name, sector, market cap
- **Price Action**: Current price, daily change, technical signals
- **Fundamentals**: Revenue growth, earnings trends, margins
- **Verdict**: Bullish / Bearish / Neutral with 2-3 sentence rationale
```
