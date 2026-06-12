"""
CAS (Consolidated Account Statement) PDF Parser
================================================
Parses e-CAS PDFs from CAMS / KFintech to automatically import:
  - Mutual Fund holdings (scheme name, units, NAV, current value)
  - Stock holdings (company, ISIN, shares, buy price)

Supported formats:
  - CAMS CAS (https://www.camsonline.com/Investors/Statements/Consolidated-Account-Statement)
  - KFintech CAS (https://mfs.kfintech.com/investor/General/ConsolidatedAccountStatement)
  - NSDL CAS (CDSL/NSDL equity statements)

Usage:
    from app.services.cas_parser import parse_cas_pdf
    holdings = parse_cas_pdf("/path/to/cas_statement.pdf", password="PAN+DOB")
"""

import re
import logging
from typing import List, Dict, Optional
from pypdf import PdfReader

logger = logging.getLogger(__name__)


# ── HELPERS ──────────────────────────────────────────────────────────────────

def _clean_number(text: str) -> Optional[float]:
    """Convert formatted number strings like '1,23,456.78' to float."""
    if not text:
        return None
    try:
        return float(text.replace(",", "").strip())
    except ValueError:
        return None


def _extract_text_from_pdf(filepath: str, password: Optional[str] = None) -> str:
    """
    Extract all text from a PDF file.
    
    Args:
        filepath: Path to the PDF file
        password: Optional password for encrypted PDFs (CAMS format: PANddmmyyyy)
    
    Returns:
        Full extracted text as a single string
    """
    reader = PdfReader(filepath)
    
    if reader.is_encrypted:
        if not password:
            raise ValueError(
                "This CAS PDF is password-protected. "
                "Please provide your password (PAN + Date of Birth in ddmmyyyy format, e.g. ABCDE1234F01011990)"
            )
        result = reader.decrypt(password)
        if result == 0:
            raise ValueError("Incorrect password. CAMS password format: PAN (uppercase) + DOB as ddmmyyyy")
    
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    return full_text


# ── MUTUAL FUND PARSER ───────────────────────────────────────────────────────

def _parse_mutual_fund_holdings(text: str) -> List[Dict]:
    """
    Parse mutual fund holdings from CAS text.
    
    Extracts: scheme name, folio, units held, current NAV, current value
    
    Returns list of dicts:
    [
        {
            "scheme_name": "HDFC Midcap Opportunities Fund - Growth",
            "folio": "12345678",
            "units": 123.456,
            "nav": 98.765,
            "current_value": 12188.23,
            "invested_value": 10000.0,
            "asset_type": "mutual_funds"
        },
        ...
    ]
    """
    holdings = []
    
    # --- Pattern 1: CAMS / KFintech standard format ---
    # Matches: "Scheme: HDFC Midcap..." then units/NAV lines
    scheme_pattern = re.compile(
        r'(?:Scheme|Fund)\s*:\s*([^\n]+)\n'
        r'(?:.*?\n){0,5}?'
        r'(?:Units|Balance)\s*:\s*([\d,\.]+)\s*'
        r'(?:.*?NAV\s*:\s*([\d,\.]+))?',
        re.IGNORECASE | re.DOTALL
    )

    # --- Pattern 2: Tabular Format (most CAMS CAS) ---
    # Example line: "HDFC Midcap Opportunities - Growth | 12345 | 1,234.567 | 98.76 | 1,21,890.45"
    tabular_pattern = re.compile(
        r'^([A-Z][^\|]{10,80}?)\s*\|\s*'
        r'([\d/]+)\s*\|\s*'        # Folio
        r'([\d,\.]+)\s*\|\s*'     # Units
        r'([\d,\.]+)\s*\|\s*'     # NAV
        r'([\d,\.]+)',             # Current Value
        re.MULTILINE
    )

    # --- Pattern 3: NSDL / CDSL equity style ---
    equity_mf_pattern = re.compile(
        r'((?:ICICI|HDFC|SBI|Axis|Kotak|Mirae|Nippon|DSP|UTI|Tata|Franklin|IDFC|Canara|Birla|Aditya)[^,\n]{5,60})\s+'
        r'([\d,\.]+)\s+'  # Units
        r'([\d,\.]+)\s+'  # NAV 
        r'([\d,\.]+)',     # Value
        re.MULTILINE
    )

    # Try tabular first (most reliable)
    for m in tabular_pattern.finditer(text):
        scheme = m.group(1).strip()
        folio = m.group(2).strip()
        units = _clean_number(m.group(3))
        nav = _clean_number(m.group(4))
        current_value = _clean_number(m.group(5))
        
        if units and units > 0 and nav:
            holdings.append({
                "scheme_name": scheme,
                "folio": folio,
                "units": units,
                "nav": nav,
                "current_value": current_value or (units * nav),
                "invested_value": None,  # Not always available in CAS
                "asset_type": "mutual_funds"
            })
    
    # Fallback: text-based CAMS parsing
    if not holdings:
        # Extract lines with fund names + unit balances
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Detect fund names (common AMC keywords)
            amc_keywords = [
                "Direct Growth", "Direct Plan", "Regular Growth",
                "Fund", "Opportunities", "Bluechip", "Flexicap",
                "Midcap", "Smallcap", "Largecap", "Index", "ELSS",
                "Liquid Fund", "Debt Fund", "Hybrid"
            ]
            
            if any(kw.lower() in line.lower() for kw in amc_keywords) and len(line) > 15:
                scheme_name = line
                
                # Look for unit balance in next few lines
                for j in range(i+1, min(i+8, len(lines))):
                    unit_match = re.search(r'(?:Units|Balance|Closing Balance)\s*:?\s*([\d,\.]+)', lines[j], re.IGNORECASE)
                    if unit_match:
                        units = _clean_number(unit_match.group(1))
                        
                        # Look for NAV
                        nav_match = re.search(r'NAV\s*:?\s*([\d,\.]+)', lines[j], re.IGNORECASE)
                        nav = _clean_number(nav_match.group(1)) if nav_match else None
                        
                        if units and units > 0:
                            holdings.append({
                                "scheme_name": scheme_name,
                                "folio": "",
                                "units": units,
                                "nav": nav,
                                "current_value": (units * nav) if (nav and units) else None,
                                "invested_value": None,
                                "asset_type": "mutual_funds"
                            })
                        break
            i += 1
    
    return holdings


# ── STOCK / EQUITY PARSER ────────────────────────────────────────────────────

def _parse_equity_holdings(text: str) -> List[Dict]:
    """
    Parse equity / stock holdings from CDSL / NSDL CAS.
    
    Extracts: company name, ISIN, quantity, buy value
    
    Returns list of dicts:
    [
        {
            "company_name": "Reliance Industries Ltd",
            "isin": "INE002A01018",
            "quantity": 10,
            "buy_value": 25000.0,
            "asset_type": "stocks"
        },
        ...
    ]
    """
    holdings = []
    
    # ISIN pattern: IN + 10 alphanumeric chars
    isin_pattern = re.compile(
        r'(IN[A-Z0-9]{10})\s+'   # ISIN
        r'([^\d\n]{5,60}?)\s+'   # Company Name
        r'(\d+)\s+'               # Quantity
        r'([\d,\.]+)',            # Value
        re.MULTILINE
    )
    
    # Alternative: Company Name first, then ISIN
    company_isin_pattern = re.compile(
        r'^([A-Z][A-Z\s&\.]{5,50}(?:LTD|LIMITED|INDUSTRIES|BANK|FINANCE|TECH|INFOTECH)?\.?)\s*\n'
        r'\s*(IN[A-Z0-9]{10})\s+'
        r'(\d+)\s+'
        r'([\d,\.]+)',
        re.MULTILINE
    )
    
    for m in isin_pattern.finditer(text):
        isin = m.group(1).strip()
        company = m.group(2).strip().title()
        quantity = _clean_number(m.group(3))
        value = _clean_number(m.group(4))
        
        if quantity and quantity > 0 and value:
            holdings.append({
                "company_name": company,
                "isin": isin,
                "quantity": int(quantity),
                "buy_value": value,
                "ticker": isin_to_ticker(isin),   # Try to resolve ticker
                "asset_type": "stocks"
            })
    
    if not holdings:
        for m in company_isin_pattern.finditer(text):
            company = m.group(1).strip().title()
            isin = m.group(2).strip()
            quantity = _clean_number(m.group(3))
            value = _clean_number(m.group(4))
            
            if quantity and quantity > 0:
                holdings.append({
                    "company_name": company,
                    "isin": isin,
                    "quantity": int(quantity),
                    "buy_value": value or 0,
                    "ticker": isin_to_ticker(isin),
                    "asset_type": "stocks"
                })
    
    return holdings


# ── ISIN -> TICKER LOOKUP ─────────────────────────────────────────────────────

# Common ISIN to NSE Ticker mappings (frequently held stocks)
_ISIN_TICKER_MAP = {
    "INE002A01018": "RELIANCE",
    "INE040A01034": "HDFCBANK",
    "INE009A01021": "INFY",
    "INE467B01029": "TCS",
    "INE062A01020": "SBIN",
    "INE030A01027": "BAJFINANCE",
    "INE881D01027": "ADANIENT",
    "INE585B01010": "AXISBANK",
    "INE090A01021": "ICICIBANK",
    "INE669C01036": "LTIM",
    "INE522F01014": "BAJAJFINSV",
    "INE001A01036": "WIPRO",
    "INE018A01030": "LARSEN",
    "INE721A01013": "TITAN",
    "INE397D01024": "SUNPHARMA",
    "INE148A01028": "ONGC",
    "INE113A01013": "GRASIM",
    "INE101A01026": "NTPC",
    "INE066A01021": "POWERGRID",
    "INE752E01010": "NESTLEIND",
}


def isin_to_ticker(isin: str) -> Optional[str]:
    """Look up NSE ticker from ISIN. Returns None if not in local map."""
    return _ISIN_TICKER_MAP.get(isin.strip().upper())


# ── MAIN PARSER ENTRY POINT ───────────────────────────────────────────────────

def parse_cas_pdf(filepath: str, password: Optional[str] = None) -> Dict:
    """
    Main entry point: parse a CAS PDF and return all detected holdings.
    
    Args:
        filepath: Absolute path to the PDF file
        password: PDF password. CAMS format: PAN+DOB (e.g. "ABCDE1234F01011990")
                  KFintech: same format. NSDL: usually open.
    
    Returns:
        {
            "mutual_funds": [ { scheme_name, units, nav, current_value, ... }, ... ],
            "stocks": [ { company_name, isin, quantity, buy_value, ... }, ... ],
            "total_holdings": 5,
            "source": "CAMS" | "KFintech" | "NSDL" | "Unknown"
        }
    
    Raises:
        ValueError: If PDF is password-protected and no password is provided
        FileNotFoundError: If PDF file does not exist
    """
    logger.info(f"Parsing CAS PDF: {filepath}")
    
    # Extract raw text
    text = _extract_text_from_pdf(filepath, password)
    
    # Detect source CAS provider
    source = "Unknown"
    if "CAMS" in text or "Computer Age Management" in text:
        source = "CAMS"
    elif "KFintech" in text or "Karvy" in text:
        source = "KFintech"
    elif "NSDL" in text:
        source = "NSDL"
    elif "CDSL" in text:
        source = "CDSL"
    
    logger.info(f"Detected CAS source: {source}")
    
    # Parse both types
    mf_holdings = _parse_mutual_fund_holdings(text)
    equity_holdings = _parse_equity_holdings(text)
    
    total = len(mf_holdings) + len(equity_holdings)
    
    logger.info(f"CAS parsed: {len(mf_holdings)} mutual funds, {len(equity_holdings)} stocks")
    
    return {
        "mutual_funds": mf_holdings,
        "stocks": equity_holdings,
        "total_holdings": total,
        "source": source,
        "raw_text_length": len(text)
    }
