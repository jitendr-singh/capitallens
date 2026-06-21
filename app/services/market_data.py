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
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Cache (5-minute TTL) ──────────────────────────────────────────────────────
_price_cache: Dict[str, tuple] = {}
CACHE_TTL_SECONDS = 300

# ── Historical Cache (10-minute TTL) ──────────────────────────────────────────
_historical_cache: Dict[str, tuple] = {}
HISTORICAL_CACHE_TTL_SECONDS = 600

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
        
    # Fallback: Direct Symbol (supports US stocks like AAPL, crypto like BTC-USD)
    if price is None:
        price = _fetch_yf_price(base)
    
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
                if "data" in data and len(data["data"]) > 0:
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
                    if "data" in data and len(data["data"]) > 0:
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
        asset_type: "stocks", "mutual_funds", "gold", "crypto" or "cryptocurrency"
        asset_name: NSE ticker / fund name+code / ignored for gold
    """
    if asset_type == "stocks" or asset_type == "crypto" or asset_type == "cryptocurrency":
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


# ── HISTORICAL PRICE LOOKUP ───────────────────────────────────────────────────

def _fetch_yf_chart(ticker: str) -> Optional[dict]:
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"interval": "1d", "range": "10y"}
    try:
        resp = requests.get(url, headers=YF_HEADERS, params=params, timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"Error fetching YF chart for {ticker}: {e}")
    return None


def _parse_yf_chart_data(chart_data: dict) -> Optional[dict]:
    result = chart_data.get("chart", {}).get("result", [])
    if not result:
        return None
        
    timestamps = result[0].get("timestamp", [])
    close_prices = result[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
    meta = result[0].get("meta", {})
    current_price = meta.get("regularMarketPrice") or meta.get("previousClose")
    
    if not timestamps or not close_prices:
        return None
        
    now = time.time()
    one_year_s = 365 * 24 * 3600
    intervals = {
        "1": now - one_year_s,
        "3": now - 3 * one_year_s,
        "5": now - 5 * one_year_s,
        "10": now - 10 * one_year_s
    }
    
    periods = {}
    for name, target_ts in intervals.items():
        closest_idx = None
        min_diff = float('inf')
        for idx, ts in enumerate(timestamps):
            if close_prices[idx] is None:
                continue
            diff = abs(ts - target_ts)
            if diff < min_diff:
                min_diff = diff
                closest_idx = idx
                
        if closest_idx is not None and min_diff < 10 * 24 * 3600:
            periods[name] = round(float(close_prices[closest_idx]), 2)
        else:
            periods[name] = None
            
    return {
        "current_price": round(float(current_price), 2) if current_price else None,
        "periods": periods
    }


def _fetch_mf_historical_data(scheme_code_or_name: str) -> Optional[dict]:
    code = scheme_code_or_name.strip()
    if not code.isdigit():
        search_url = "https://api.mfapi.in/mf/search"
        try:
            resp = requests.get(search_url, params={"q": scheme_code_or_name}, timeout=3)
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    code = str(results[0]["schemeCode"])
                else:
                    return None
            else:
                return None
        except Exception as e:
            logger.error(f"Error searching MF {scheme_code_or_name}: {e}")
            return None
            
    url = f"{AMFI_API_URL}{code}"
    try:
        resp = requests.get(url, timeout=3)
        if resp.status_code != 200:
            return None
            
        data = resp.json()
        nav_list = data.get("data", [])
        if not nav_list:
            return None
            
        latest_nav = float(nav_list[0]["nav"])
        
        now = datetime.utcnow()
        targets = {
            "1": datetime(now.year - 1, now.month, now.day),
            "3": datetime(now.year - 3, now.month, now.day),
            "5": datetime(now.year - 5, now.month, now.day),
            "10": datetime(now.year - 10, now.month, now.day)
        }
        
        periods = {}
        for name, target_date in targets.items():
            closest_nav = None
            min_diff = float('inf')
            
            for item in nav_list:
                try:
                    dt = datetime.strptime(item["date"], "%d-%m-%Y")
                    diff = abs((dt - target_date).days)
                    if diff < min_diff:
                        min_diff = diff
                        closest_nav = float(item["nav"])
                except:
                    continue
                    
            if closest_nav is not None and min_diff < 10:
                periods[name] = closest_nav
            else:
                periods[name] = None
                
        return {
            "current_price": latest_nav,
            "periods": periods
        }
    except Exception as e:
        logger.error(f"Error fetching historical MF NAV for {scheme_code_or_name}: {e}")
        return None


def _parse_gold_chart_data(gold_chart: dict, inr_chart: dict) -> Optional[dict]:
    gold_res = gold_chart.get("chart", {}).get("result", [])
    inr_res = inr_chart.get("chart", {}).get("result", [])
    if not gold_res or not inr_res:
        return None
        
    gold_ts = gold_res[0].get("timestamp", [])
    gold_close = gold_res[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
    gold_meta = gold_res[0].get("meta", {})
    gold_curr = gold_meta.get("regularMarketPrice") or gold_meta.get("previousClose")
    
    inr_ts = inr_res[0].get("timestamp", [])
    inr_close = inr_res[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
    inr_meta = inr_res[0].get("meta", {})
    inr_curr = inr_meta.get("regularMarketPrice") or inr_meta.get("previousClose")
    
    if not gold_ts or not gold_close or not inr_ts or not inr_close:
        return None
        
    if gold_curr and inr_curr:
        current_price = round((gold_curr * inr_curr) / 31.1035, 2)
    else:
        current_price = None
        
    now = time.time()
    one_year_s = 365 * 24 * 3600
    intervals = {
        "1": now - one_year_s,
        "3": now - 3 * one_year_s,
        "5": now - 5 * one_year_s,
        "10": now - 10 * one_year_s
    }
    
    periods = {}
    for name, target_ts in intervals.items():
        g_idx = None
        g_min_diff = float('inf')
        for idx, ts in enumerate(gold_ts):
            if gold_close[idx] is None:
                continue
            diff = abs(ts - target_ts)
            if diff < g_min_diff:
                g_min_diff = diff
                g_idx = idx
                
        i_idx = None
        i_min_diff = float('inf')
        for idx, ts in enumerate(inr_ts):
            if inr_close[idx] is None:
                continue
            diff = abs(ts - target_ts)
            if diff < i_min_diff:
                i_min_diff = diff
                i_idx = idx
                
        if g_idx is not None and i_idx is not None and g_min_diff < 10 * 24 * 3600 and i_min_diff < 10 * 24 * 3600:
            gold_usd = gold_close[g_idx]
            usd_inr = inr_close[i_idx]
            periods[name] = round((gold_usd * usd_inr) / 31.1035, 2)
        else:
            periods[name] = None
            
    return {
        "current_price": current_price,
        "periods": periods
    }


def get_historical_data(asset_type: str, symbol: str) -> Optional[dict]:
    """
    Unified public method to fetch actual historical data for an asset.
    Returns: { "current_price": float, "periods": { "1": float, "3": float, "5": float, "10": float } }
    """
    symbol = symbol.strip().upper()
    cache_key = f"hist_{asset_type}_{symbol}"
    
    # Check cache
    if cache_key in _historical_cache:
        cached_data, timestamp = _historical_cache[cache_key]
        if (time.time() - timestamp) < HISTORICAL_CACHE_TTL_SECONDS:
            logger.info(f"Returning cached historical data for {asset_type} {symbol}")
            return cached_data

    result = None
    if asset_type == "stocks":
        base = symbol.replace(".NS", "").replace(".BO", "")
        # Try NSE
        chart = _fetch_yf_chart(f"{base}.NS")
        if not chart:
            # Try BSE
            chart = _fetch_yf_chart(f"{base}.BO")
        if not chart:
            # Try direct raw symbol (US stocks/crypto)
            chart = _fetch_yf_chart(base)
            
        if chart:
            result = _parse_yf_chart_data(chart)
        
    elif asset_type == "mutual_funds":
        result = _fetch_mf_historical_data(symbol)
        
    elif asset_type == "gold":
        gold_chart = _fetch_yf_chart("GC=F")
        inr_chart = _fetch_yf_chart("INR=X")
        if gold_chart and inr_chart:
            result = _parse_gold_chart_data(gold_chart, inr_chart)
            
    if result:
        _historical_cache[cache_key] = (result, time.time())
        
    return result

