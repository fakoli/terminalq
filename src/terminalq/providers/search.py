"""Brave Search provider — web search for market news and research."""

import httpx

from terminalq import cache, usage_tracker
from terminalq.config import BRAVE_API_KEY, BRAVE_MONTHLY_LIMIT, CACHE_TTL_SEARCH
from terminalq.logging_config import log

BASE_URL = "https://api.search.brave.com/res/v1/web/search"


async def web_search(query: str, count: int = 5) -> dict:
    """Search the web using Brave Search API.

    Args:
        query: Search query string.
        count: Number of results to return (default 5, max 20).

    Returns:
        Dict with search results including title, url, and description.
    """
    if not BRAVE_API_KEY:
        return {
            "error": "BRAVE_API_KEY not configured. Get a free key at https://brave.com/search/api/",
            "source": "brave_search",
        }

    cache_key = f"brave_search_{query}_{count}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    # Atomically increment and check Brave Search budget
    within_budget, usage = await usage_tracker.increment_and_check("brave_search", BRAVE_MONTHLY_LIMIT)
    if not within_budget:
        return {
            "error": f"Brave Search monthly limit reached ({BRAVE_MONTHLY_LIMIT} calls). Resets next month.",
            "usage": usage,
            "source": "brave_search",
        }

    count = min(count, 20)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                BASE_URL,
                params={"q": query, "count": count},
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": BRAVE_API_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        log.warning("Brave Search timeout for query: %s", query)
        return {"error": "Request timed out", "source": "brave_search"}
    except httpx.HTTPStatusError as e:
        log.warning("Brave Search HTTP %d for query: %s", e.response.status_code, query)
        return {"error": f"HTTP {e.response.status_code}", "source": "brave_search"}
    except httpx.ConnectError:
        log.error("Brave Search connection failed")
        return {"error": "Connection failed", "source": "brave_search"}

    # Parse web results
    web_results = data.get("web", {}).get("results", [])
    results = []
    for item in web_results[:count]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "age": item.get("age", ""),
            }
        )

    # Parse news results if available
    news_results = data.get("news", {}).get("results", [])
    news = []
    for item in news_results[:5]:
        news.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "age": item.get("age", ""),
                "source": item.get("meta_url", {}).get("hostname", ""),
            }
        )

    result = {
        "query": query,
        "total_results": len(results),
        "results": results,
        "news": news,
        "source": "brave_search",
        "usage": usage_tracker.get_monthly_usage("brave_search", BRAVE_MONTHLY_LIMIT),
    }
    cache.set(cache_key, result, CACHE_TTL_SEARCH)
    return result
