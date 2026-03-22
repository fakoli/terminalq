---
name: tq-usage
description: View TerminalQ usage statistics and API budget
arguments: []
---

Use `terminalq_get_usage_stats` to retrieve usage statistics.

Present the results as a usage dashboard:

**Today's Activity:**

- Total tool calls
- Total data transferred (payload bytes, formatted as KB/MB)
- Estimated token consumption (payload bytes / 4)

**Top Tools Today:** Ranked list of most-called tools with call counts and total duration.

**API Budgets:**

- Brave Search: calls used / 2,000 monthly limit, remaining calls, % used
- If over 80% used, flag as a warning

**Cost Awareness:**

- Note that TerminalQ tools are free, but each tool call consumes Claude tokens
- Estimated token usage today based on payload sizes
- Suggest batching quotes (get_quotes_batch vs individual get_quote) if many single-quote calls detected
