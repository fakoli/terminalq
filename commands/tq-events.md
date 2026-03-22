---
name: tq-events
description: Show upcoming economic events calendar
arguments:
  - name: days
    description: "Number of days ahead to show (default 7)"
    required: false
---

Use `terminalq_get_economic_calendar` with the specified number of days (default 7).

Present the calendar grouped by day, showing:

- Date and event name
- Impact level (high/medium/low) with visual indicator
- Previous value, estimate, and actual (if released)

Highlight high-impact events prominently. Note any events that could move markets significantly.
