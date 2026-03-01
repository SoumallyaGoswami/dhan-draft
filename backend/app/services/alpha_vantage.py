"""Alpha Vantage API client for real-time and historical stock data."""
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from ..config import settings

logger = logging.getLogger(__name__)


def _fetch_url(url: str, params: dict) -> Optional[dict]:
    """Sync HTTP GET using stdlib (no httpx required). Returns JSON dict or None."""
    try:
        full_url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full_url, headers={"User-Agent": "DhanDraft/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning("Alpha Vantage fetch failed: %s", e)
        return None

# Indian stocks (used when Alpha Vantage is disabled and data comes from DB seed)
STOCK_METADATA = [
    {"symbol": "RELIANCE", "alpha_symbol": "RELIANCE.BSE", "name": "Reliance Industries", "sector": "Energy", "marketCap": "16.5L Cr"},
    {"symbol": "TCS", "alpha_symbol": "TCS.BSE", "name": "Tata Consultancy Services", "sector": "Technology", "marketCap": "14.2L Cr"},
    {"symbol": "HDFCBANK", "alpha_symbol": "HDFCBANK.BSE", "name": "HDFC Bank", "sector": "Banking", "marketCap": "12.4L Cr"},
    {"symbol": "INFY", "alpha_symbol": "INFY.BSE", "name": "Infosys", "sector": "Technology", "marketCap": "6.3L Cr"},
    {"symbol": "ITC", "alpha_symbol": "ITC.BSE", "name": "ITC Limited", "sector": "FMCG", "marketCap": "5.8L Cr"},
    {"symbol": "BHARTIARTL", "alpha_symbol": "BHARTIARTL.BSE", "name": "Bharti Airtel", "sector": "Telecom", "marketCap": "9.4L Cr"},
    {"symbol": "SBIN", "alpha_symbol": "SBIN.BSE", "name": "State Bank of India", "sector": "Banking", "marketCap": "7.0L Cr"},
    {"symbol": "SUNPHARMA", "alpha_symbol": "SUNPHARMA.BSE", "name": "Sun Pharma", "sector": "Pharma", "marketCap": "4.4L Cr"},
]

# US stocks - Alpha Vantage free tier supports these (5 symbols = under 5 calls/min limit)
ALPHA_STOCK_METADATA: List[Dict[str, Any]] = [
    {"symbol": "AAPL", "alpha_symbol": "AAPL", "name": "Apple Inc", "sector": "Technology", "marketCap": "3.0T"},
    {"symbol": "MSFT", "alpha_symbol": "MSFT", "name": "Microsoft Corp", "sector": "Technology", "marketCap": "2.8T"},
    {"symbol": "GOOGL", "alpha_symbol": "GOOGL", "name": "Alphabet (Google)", "sector": "Technology", "marketCap": "2.2T"},
    {"symbol": "AMZN", "alpha_symbol": "AMZN", "name": "Amazon.com", "sector": "Consumer", "marketCap": "1.9T"},
    {"symbol": "NVDA", "alpha_symbol": "NVDA", "name": "NVIDIA Corp", "sector": "Technology", "marketCap": "2.6T"},
]


def get_metadata_for_alpha() -> List[Dict[str, Any]]:
    """Return the stock list to use when Alpha Vantage API key is set (US symbols for reliable data)."""
    return ALPHA_STOCK_METADATA

# In-memory cache: key -> (data, expiry_ts). TTL in seconds to reduce API calls (free tier: 5/min, 500/day).
_CACHE: dict = {}
_CACHE_TTL = 300  # 5 minutes


def _cache_get(key: str):
    now = datetime.now(timezone.utc).timestamp()
    if key in _CACHE:
        data, expiry = _CACHE[key]
        if now < expiry:
            return data
        del _CACHE[key]
    return None


def _cache_set(key: str, data):
    _CACHE[key] = (data, datetime.now(timezone.utc).timestamp() + _CACHE_TTL)


async def get_quote(alpha_symbol: str) -> Optional[dict]:
    """Fetch global quote for a symbol. Returns currentPrice, change (%), previousClose, etc."""
    key = (settings.ALPHA_VANTAGE_API_KEY or "").strip()
    if not key:
        return None
    cache_key = f"quote:{alpha_symbol}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    import asyncio
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": alpha_symbol,
        "apikey": key,
    }
    data = await asyncio.to_thread(_fetch_url, url, params)
    if not data:
        return None
    err_msg = data.get("Error Message") or data.get("Note")
    if err_msg:
        logger.warning("Alpha Vantage error for %s: %s", alpha_symbol, err_msg[:200])
        return None
    quote = data.get("Global Quote") or {}
    if not quote:
        logger.warning("Alpha Vantage GLOBAL_QUOTE empty for %s", alpha_symbol)
        return None
    price_str = quote.get("05. price") or quote.get("5. price")
    prev_str = quote.get("08. previous close") or quote.get("8. previous close")
    chg_str = quote.get("10. change percent") or quote.get("09. change") or "0"
    if not price_str:
        return None
    try:
        price = float(price_str)
        prev = float(prev_str) if prev_str else price
        try:
            change_pct = float(str(chg_str).replace("%", "").strip())
        except (ValueError, TypeError):
            change_pct = ((price - prev) / prev * 100) if prev else 0
        out = {
            "currentPrice": round(price, 2),
            "change": round(change_pct, 2),
            "previousClose": round(prev, 2),
            "volume": int(float(quote.get("06. volume") or quote.get("6. volume") or 0)),
        }
        _cache_set(cache_key, out)
        return out
    except (TypeError, ValueError) as e:
        logger.warning("Alpha Vantage parse error for %s: %s", alpha_symbol, e)
        return None


async def get_time_series_daily(alpha_symbol: str, outputsize: str = "compact") -> list:
    """Fetch daily time series. Returns list of { date, open, high, low, close, volume } sorted by date."""
    key = (settings.ALPHA_VANTAGE_API_KEY or "").strip()
    if not key:
        return []
    cache_key = f"daily:{alpha_symbol}:{outputsize}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    import asyncio
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": alpha_symbol,
        "apikey": key,
        "outputsize": outputsize,
    }
    data = await asyncio.to_thread(_fetch_url, url, params)
    if not data:
        return []
    err_msg = data.get("Error Message") or data.get("Note")
    if err_msg:
        logger.warning("Alpha Vantage time series error for %s: %s", alpha_symbol, err_msg[:200])
        return []
    ts_key = "Time Series (Daily)"
    series = data.get(ts_key) or {}
    result = []
    for date_str, ohlcv in series.items():
        try:
            result.append({
                "date": date_str,
                "open": float(ohlcv.get("1. open", 0)),
                "high": float(ohlcv.get("2. high", 0)),
                "low": float(ohlcv.get("3. low", 0)),
                "close": float(ohlcv.get("4. close", 0)),
                "volume": int(float(ohlcv.get("5. volume", 0))),
            })
        except (TypeError, ValueError):
            continue
    result.sort(key=lambda x: x["date"])
    _cache_set(cache_key, result)
    return result


def get_metadata_by_symbol(symbol: str) -> Optional[dict]:
    """Get static metadata for a display symbol (Indian list)."""
    sym_upper = (symbol or "").upper()
    for m in STOCK_METADATA:
        if m["symbol"] == sym_upper:
            return m
    return None


def get_alpha_metadata_by_symbol(symbol: str) -> Optional[dict]:
    """Get metadata for a symbol when using Alpha Vantage (US list)."""
    sym_upper = (symbol or "").upper()
    for m in ALPHA_STOCK_METADATA:
        if m["symbol"] == sym_upper:
            return m
    return None


def get_metadata_by_alpha_symbol(alpha_symbol: str) -> Optional[dict]:
    for m in STOCK_METADATA:
        if m["alpha_symbol"] == alpha_symbol:
            return m
    return None
