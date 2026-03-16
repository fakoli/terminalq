"""CoinGecko data provider — cryptocurrency quotes and batch pricing."""

import httpx

from terminalq import cache
from terminalq.config import CACHE_TTL_CRYPTO, COINGECKO_RATE_LIMIT
from terminalq.logging_config import log
from terminalq.rate_limiter import RateLimiter

BASE_URL = "https://api.coingecko.com/api/v3"
_rate_limiter = RateLimiter(calls_per_minute=COINGECKO_RATE_LIMIT)

# Common symbol → CoinGecko ID mapping
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "DOT": "polkadot",
    "AVAX": "avalanche-2",
    "MATIC": "matic-network",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "SHIB": "shiba-inu",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "NEAR": "near",
    "FIL": "filecoin",
    "APT": "aptos",
    "ARB": "arbitrum",
    "OP": "optimism",
    "SUI": "sui",
    "SEI": "sei-network",
    "TIA": "celestia",
    "INJ": "injective-protocol",
    "RENDER": "render-token",
    "FET": "fetch-ai",
    "PEPE": "pepe",
    "WIF": "dogwifcoin",
}


def _resolve_id(symbol: str) -> str:
    """Resolve a ticker symbol to a CoinGecko coin ID."""
    return SYMBOL_TO_ID.get(symbol.upper(), symbol.lower())


async def _fetch(client: httpx.AsyncClient, url: str, params: dict) -> dict | list:
    """Rate-limited HTTP GET with error handling."""
    await _rate_limiter.acquire()
    log.debug("CoinGecko request: %s params=%s", url, params)
    try:
        resp = await client.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except httpx.TimeoutException:
        log.warning("CoinGecko timeout: %s %s", url, params)
        return {"_error": "Request timed out"}
    except httpx.HTTPStatusError as e:
        log.warning("CoinGecko HTTP %d: %s %s", e.response.status_code, url, params)
        return {"_error": f"HTTP {e.response.status_code}"}
    except httpx.ConnectError:
        log.error("CoinGecko connection failed: %s", url)
        return {"_error": "Connection failed"}


async def get_crypto_quote(symbol: str) -> dict:
    """Get real-time cryptocurrency quote.

    Args:
        symbol: Crypto ticker (e.g. "BTC", "ETH", "SOL") or CoinGecko ID.

    Returns:
        Dict with price, market cap, volume, and 24h change.
    """
    coin_id = _resolve_id(symbol)
    cache_key = f"coingecko_quote_{coin_id}"
    cached = cache.get(cache_key)
    if cached:
        log.debug("Cache hit: %s", cache_key)
        return cached

    async with httpx.AsyncClient() as client:
        data = await _fetch(
            client,
            f"{BASE_URL}/coins/{coin_id}",
            {
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false",
            },
        )

    if isinstance(data, dict) and "_error" in data:
        return {"symbol": symbol.upper(), "error": data["_error"], "source": "coingecko"}

    market = data.get("market_data", {})
    result = {
        "symbol": symbol.upper(),
        "coin_id": coin_id,
        "name": data.get("name", ""),
        "current_price": market.get("current_price", {}).get("usd"),
        "market_cap": market.get("market_cap", {}).get("usd"),
        "market_cap_rank": data.get("market_cap_rank"),
        "total_volume": market.get("total_volume", {}).get("usd"),
        "high_24h": market.get("high_24h", {}).get("usd"),
        "low_24h": market.get("low_24h", {}).get("usd"),
        "price_change_24h": market.get("price_change_24h"),
        "price_change_pct_24h": market.get("price_change_percentage_24h"),
        "price_change_pct_7d": market.get("price_change_percentage_7d"),
        "price_change_pct_30d": market.get("price_change_percentage_30d"),
        "circulating_supply": market.get("circulating_supply"),
        "total_supply": market.get("total_supply"),
        "ath": market.get("ath", {}).get("usd"),
        "ath_change_pct": market.get("ath_change_percentage", {}).get("usd"),
        "source": "coingecko",
    }
    cache.set(cache_key, result, CACHE_TTL_CRYPTO)
    return result


async def get_crypto_batch(symbols: list[str]) -> list[dict]:
    """Get quotes for multiple cryptocurrencies concurrently.

    Args:
        symbols: List of crypto tickers (e.g. ["BTC", "ETH", "SOL"]).

    Returns:
        List of quote dicts.
    """
    results: dict[str, dict] = {}
    uncached: list[str] = []

    # Check cache first
    for symbol in symbols:
        coin_id = _resolve_id(symbol)
        cache_key = f"coingecko_quote_{coin_id}"
        cached = cache.get(cache_key)
        if cached:
            log.debug("Cache hit: %s", cache_key)
            results[symbol] = cached
        else:
            uncached.append(symbol)

    if not uncached:
        return [results[s] for s in symbols]

    # Use /coins/markets for batch lookup (more efficient than individual calls)
    coin_ids = [_resolve_id(s) for s in uncached]
    ids_str = ",".join(coin_ids)

    log.info("Fetching %d uncached crypto quotes: %s", len(uncached), uncached)

    async with httpx.AsyncClient() as client:
        data = await _fetch(
            client,
            f"{BASE_URL}/coins/markets",
            {
                "vs_currency": "usd",
                "ids": ids_str,
                "order": "market_cap_desc",
                "sparkline": "false",
                "price_change_percentage": "24h,7d,30d",
            },
        )

    if isinstance(data, dict) and "_error" in data:
        for symbol in uncached:
            results[symbol] = {"symbol": symbol.upper(), "error": data["_error"], "source": "coingecko"}
        return [results.get(s, {"symbol": s.upper(), "error": "Not found", "source": "coingecko"}) for s in symbols]

    # Build a lookup from coin_id → data
    id_to_data = {}
    if isinstance(data, list):
        for item in data:
            id_to_data[item.get("id", "")] = item

    for symbol in uncached:
        coin_id = _resolve_id(symbol)
        item = id_to_data.get(coin_id)
        if not item:
            results[symbol] = {"symbol": symbol.upper(), "error": "Not found on CoinGecko", "source": "coingecko"}
            continue

        result = {
            "symbol": symbol.upper(),
            "coin_id": coin_id,
            "name": item.get("name", ""),
            "current_price": item.get("current_price"),
            "market_cap": item.get("market_cap"),
            "market_cap_rank": item.get("market_cap_rank"),
            "total_volume": item.get("total_volume"),
            "high_24h": item.get("high_24h"),
            "low_24h": item.get("low_24h"),
            "price_change_24h": item.get("price_change_24h"),
            "price_change_pct_24h": item.get("price_change_percentage_24h"),
            "price_change_pct_7d": item.get("price_change_percentage_7d_in_currency"),
            "price_change_pct_30d": item.get("price_change_percentage_30d_in_currency"),
            "circulating_supply": item.get("circulating_supply"),
            "total_supply": item.get("total_supply"),
            "ath": item.get("ath"),
            "ath_change_pct": item.get("ath_change_percentage"),
            "source": "coingecko",
        }
        cache.set(f"coingecko_quote_{coin_id}", result, CACHE_TTL_CRYPTO)
        results[symbol] = result

    return [results.get(s, {"symbol": s.upper(), "error": "Not found", "source": "coingecko"}) for s in symbols]
