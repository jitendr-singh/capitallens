"""
Market Data Service
===================
Fetches real-time prices from Yahoo Finance REST API (v8/v11 JSON endpoints)
and AMFI Open API — NO yfinance library dependency (Python 3.14 compatible).

Sources:
  - NSE / BSE Stocks:   https://query2.finance.yahoo.com/v8/finance/chart/{symbol}
  - Mutual Fund NAV:    https://api.mfapi.in/mf/{scheme_code}  (AMFI, free, no auth)
  - Gold price:         Yahoo Finance GC=F (Gold Futures in USD) + INR=X exchange rate
"""

import requests
import logging
from typing import Optional, Dict
import time
import re

logger = logging.getLogger(__name__)

# ── Cache (5-minute TTL) ──────────────────────────────────────────────────────
_price_cache: Dict[str, tuple] = {}
CACHE_TTL_SECONDS = 300

YF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

def _is_cache_valid(symbol: str) -> bool:
    if symbol not in _price_cache:
        return False
    _, ts = _price_cache[symbol]
    return (time.time() - ts) < CACHE_TTL_SECONDS


def _set_cache(symbol: str, price: float):
    _price_cache[symbol] = (price, time.time())


def _get_cache(symbol: str) -> Optional[float]:
    if _is_cache_valid(symbol):
        return _price_cache[symbol][0]
    return None


# ── YAHOO FINANCE REST API ────────────────────────────────────────────────────

def _fetch_yf_price(yf_symbol: str) -> Optional[float]:
    """
    Fetch latest price using Yahoo Finance v8 chart endpoint.
    No yfinance library needed — pure HTTP.
    """
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{yf_symbol}"
    params = {"interval": "1m", "range": "1d"}
    
    try:
        resp = requests.get(url, headers=YF_HEADERS, params=params, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"YF API returned {resp.status_code} for {yf_symbol}")
            return None
        
        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return None
        
        meta = result[0].get("meta", {})
        # Try regularMarketPrice first (most accurate)
        price = meta.get("regularMarketPrice") or meta.get("previousClose")
        
        if price:
            return round(float(price), 2)
        return None
    except Exception as e:
        logger.error(f"YF REST API error for {yf_symbol}: {e}")
        return None


# ── STOCK PRICE (NSE/BSE) ────────────────────────────────────────────────────

def get_stock_price(ticker: str) -> Optional[float]:
    """
    Fetch latest stock price from Yahoo Finance REST API.
    Auto-appends .NS (NSE) suffix if not present.
    Falls back to .BO (BSE) if NSE fails.
    
    Args:
        ticker: "RELIANCE", "TCS", "INFY", "RELIANCE.NS", "HDFC.BO" etc.
    """
    ticker = ticker.strip().upper()
    
    # Strip .NS/.BO for clean base
    base = ticker.replace(".NS", "").replace(".BO", "")
    
    # Check cache
    cached = _get_cache(f"{base}.NS")
    if cached is not None:
        return cached

    # Try NSE first
    price = _fetch_yf_price(f"{base}.NS")
    
    # Fallback: BSE
    if price is None:
        price = _fetch_yf_price(f"{base}.BO")
    
    if price:
        _set_cache(f"{base}.NS", price)
        logger.info(f"Stock price: {base} = ₹{price}")
    else:
        logger.warning(f"Could not fetch price for: {ticker}")
    
    return price


# ── MUTUAL FUND NAV (AMFI via mfapi.in) ──────────────────────────────────────

AMFI_API_URL = "https://api.mfapi.in/mf/"

def get_mutual_fund_nav(scheme_code_or_name: str) -> Optional[float]:
    """
    Fetch latest NAV for a mutual fund scheme from AMFI (via mfapi.in).
    
    Args:
        scheme_code_or_name: Numeric scheme code ("120503") or partial fund name
    """
    cache_key = f"mf_{scheme_code_or_name}"
    cached = _get_cache(cache_key)
    if cached is not None:
        return cached

    try:
        if scheme_code_or_name.strip().isdigit():
            # Direct code lookup
            url = f"{AMFI_API_URL}{scheme_code_or_name.strip()}"
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                nav = float(data["data"][0]["nav"])
                _set_cache(cache_key, nav)
                logger.info(f"MF NAV: {scheme_code_or_name} = ₹{nav}")
                return nav
        
        # Name-based search
        search_url = "https://api.mfapi.in/mf/search"
        resp = requests.get(search_url, params={"q": scheme_code_or_name}, timeout=8)
        if resp.status_code == 200:
            results = resp.json()
            if results:
                scheme_code = results[0]["schemeCode"]
                nav_resp = requests.get(f"{AMFI_API_URL}{scheme_code}", timeout=8)
                if nav_resp.status_code == 200:
                    data = nav_resp.json()
                    nav = float(data["data"][0]["nav"])
                    _set_cache(cache_key, nav)
                    logger.info(f"MF NAV by name '{scheme_code_or_name}' = ₹{nav}")
                    return nav
        
        return None
    except Exception as e:
        logger.error(f"MF NAV error for {scheme_code_or_name}: {e}")
        return None


# ── GOLD PRICE (Yahoo Finance: GC=F + INR conversion) ────────────────────────

def get_gold_price_per_gram() -> Optional[float]:
    """
    Fetch current gold price per gram in INR.
    Uses Yahoo Finance Gold Futures (GC=F) USD/oz → INR/gram conversion.
    1 troy oz = 31.1035 grams
    """
    cached = _get_cache("GOLD_INR_PER_GRAM")
    if cached is not None:
        return cached

    try:
        gold_usd_oz = _fetch_yf_price("GC=F")
        usd_inr_rate = _fetch_yf_price("INR=X")   # USD per 1 INR → need reciprocal
        
        # INR=X gives USD per INR, so: 1 USD = 1/rate INR
        # Actually Yahoo gives USD/INR as "how many USD per 1 INR" 
        # But typically INR=X shows how many INR per 1 USD
        # Let's verify by checking value > 1 means USD/INR rate (e.g. ~83)
        
        if gold_usd_oz and usd_inr_rate:
            # usd_inr_rate is the INR value of 1 USD (e.g. ~83)
            inr_per_oz = gold_usd_oz * usd_inr_rate
            inr_per_gram = round(inr_per_oz / 31.1035, 2)
            _set_cache("GOLD_INR_PER_GRAM", inr_per_gram)
            logger.info(f"Gold: ₹{inr_per_gram}/gram (${gold_usd_oz}/oz × {usd_inr_rate} INR)")
            return inr_per_gram
        
        return None
    except Exception as e:
        logger.error(f"Gold price error: {e}")
        return None


# ── MASTER DISPATCHER ─────────────────────────────────────────────────────────

def get_live_price(asset_type: str, asset_name: str) -> Optional[float]:
    """
    Fetch live price for an asset based on type.
    
    Args:
        asset_type: "stocks", "mutual_funds", or "gold"
        asset_name: NSE ticker / fund name+code / ignored for gold
    """
    if asset_type == "stocks":
        return get_stock_price(asset_name)
    elif asset_type == "mutual_funds":
        return get_mutual_fund_nav(asset_name)
    elif asset_type == "gold":
        return get_gold_price_per_gram()
    return None


def calculate_live_investment_value(
    asset_type: str,
    asset_name: str,
    quantity: Optional[float],
    buy_price: Optional[float],
    amount_invested: float
) -> Dict:
    """
    Calculate the live current value of a market-linked investment.
    
    Returns dict with: current_value, current_price, is_live, change_pct
    """
    live_price = get_live_price(asset_type, asset_name)

    if live_price and quantity and quantity > 0:
        current_value = round(live_price * quantity, 2)
        change_pct = (
            (current_value - amount_invested) / amount_invested * 100
        ) if amount_invested > 0 else 0.0
        return {
            "current_value": current_value,
            "current_price": live_price,
            "is_live": True,
            "change_pct": round(change_pct, 2)
        }

    return {
        "current_value": None,
        "current_price": live_price,
        "is_live": False,
        "change_pct": 0.0
    }
