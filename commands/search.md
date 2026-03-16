---
name: search
description: Search the web for market news, research, or financial topics
arguments:
  - name: query
    description: Search query (e.g., "NVDA earnings analysis", "fed rate decision")
    required: true
---

Use `terminalq_web_search` to search for "$ARGUMENTS".

Present the results as a concise research brief:

- List top results with title, source, and a one-line summary
- If news results are available, show them separately under a News section
- Highlight any results from trusted financial sources (Bloomberg, Reuters, CNBC, WSJ, FT)

Add a brief synthesis of what the search results suggest about the topic.
