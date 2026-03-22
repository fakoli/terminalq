---
name: tq-audit
description: View the audit trail of all TerminalQ tool invocations
arguments:
  - name: date
    description: "Date to view (YYYY-MM-DD format, default: today)"
    required: false
---

Use `terminalq_get_audit_log` to retrieve the audit trail for "$ARGUMENTS" (or today if no date specified).

Present the results as:

**Summary:**

- Total tool calls, total duration, total payload bytes
- Time range (first call → last call)

**Top Tools:** Table of tools ranked by call count with total duration.

**Recent Activity:** Show the last 10-15 entries as a table:

- Timestamp (HH:MM:SS)
- Tool name (shortened — drop "terminalq\_" prefix)
- Key args (symbol, query, etc.)
- Duration (ms)
- Data source

This audit trail is for compliance and debugging. Highlight any unusually slow calls (>5s) or errors.
