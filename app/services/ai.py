import json
import logging
import requests
from app.config.settings import settings

logger = logging.getLogger(__name__)

def generate_investment_suggestions(
    available_cash: float,
    savings_rate: float,
    total_income: float,
    total_expense: float,
    total_savings: float
) -> list:
    """
    Calls Gemini API to generate 3 customized investment options (Low, Medium, High risk)
    based on the user's detailed financial snapshot.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set. Falling back to mock suggestions.")
        return get_mock_suggestions(available_cash, savings_rate, total_income, total_expense, total_savings)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    
    prompt = f"""
    You are a professional financial planner. Based on the user's financial profile, suggest EXACTLY 3 investment recommendations:
    1. Low Risk (Conservative, e.g. Index Mutual Funds, Gold, Govt Bonds)
    2. Medium Risk (Moderate, e.g. Blue-chip Stocks, REITs)
    3. High Risk (Aggressive, e.g. Growth Stocks, Small-cap Funds, Crypto)

    User Profile:
    - Monthly Income: {total_income:.2f}
    - Monthly Expenses: {total_expense:.2f}
    - Net Monthly Savings: {total_savings:.2f}
    - Savings Rate: {savings_rate:.1f}%
    - Available cash to invest (Investable Amount): {available_cash:.2f}

    For each recommendation, provide the following fields in a valid JSON array of objects:
    - asset_name: Name of the asset (e.g. "Nifty 50 Index Fund", "Tata Motors Stock", "Bitcoin")
    - asset_type: One of: "stocks", "fixed_deposit", "mutual_funds", "gold", "govt_schemes", "real_estate"
    - risk_level: One of: "Low", "Medium", "High"
    - risk_score: Volatility rating as an integer from 1 to 10 (e.g. 1 for FD, 3 for index funds, 6 for blue-chip stocks, 9 for crypto)
    - expected_return_rate: Expected CAGR / annual return as a float (e.g., 7.5, 12.0, 30.0)
    - recommended_allocation: Recommended amount to invest from their available cash (e.g. 5000, 10000). Must be less than or equal to available cash.
    - allocation_rationale: JSON array of 3 strings (in Hinglish/Hindi or English) explaining why this specific amount and asset is recommended based on their {savings_rate:.1f}% savings rate and income/expense.
    - holding_period: Recommended holding horizon (e.g., "5+ Years", "3-5 Years", "1-2 Years")
    - pros: JSON array of 3 advantages/pros of this asset.
    - cons: JSON array of 3 unsugarcoated disadvantages/cons (risks, drawbacks, fees, maximum temporary drop expectations). Do not sugarcoat.
    - risk_protection: JSON array of 3-4 reasons why this asset has built-in protection (e.g. "Regulated by SEBI", "50+ companies diversification", "Physical backing").
    - liquidity: "Yes" or "No"
    - ticker: For stocks, the NSE symbol (e.g., "TCS", "INFY", "RELIANCE"). For mutual funds, a short search query (e.g., "NIFTY50"). For gold, "GOLD".
    - historical_data: JSON object containing actual historical price/NAV or interest rates for 1, 3, 5, 10 years ago. Set to null if not available.
      Structure for market-linked (stocks, mutual_funds, gold, ETFs): {{ "current_price": float, "periods": {{ "1": float_price_1y_ago, "3": float_price_3y_ago, "5": float_price_5y_ago, "10": float_price_10y_ago }} }}
      Structure for fixed return (fixed_deposit, bonds): {{ "interest_rates": {{ "1": float_rate_1y_ago, "3": float_rate_3y_ago, "5": float_rate_5y_ago, "10": float_rate_10y_ago }} }}

    Respond ONLY with the raw JSON array. Do not include markdown formatting, backticks, or any conversational text.
    """

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        res_data = response.json()
        
        # Extract response text
        content_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Clean markdown code blocks if any got returned despite instructions
        if content_text.startswith("```"):
            lines = content_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            content_text = "\n".join(lines).strip()
            
        suggestions = json.loads(content_text)
        if isinstance(suggestions, list) and len(suggestions) > 0:
            return suggestions
            
    except Exception as e:
        logger.error(f"Failed to fetch Gemini investment suggestions: {e}")
        
    return get_mock_suggestions(available_cash, savings_rate, total_income, total_expense, total_savings)

def get_mock_suggestions(available_cash: float, savings_rate: float, total_income: float, total_expense: float, total_savings: float) -> list:
    """Fallback high-fidelity mock suggestions in case API fails or key is missing."""
    rec_low = max(1000.0, round(available_cash * 0.4, -2))
    rec_med = max(1000.0, round(available_cash * 0.35, -2))
    rec_high = max(1000.0, round(available_cash * 0.15, -2))
    return [
        {
            "asset_name": "Nifty 50 Index Fund",
            "asset_type": "mutual_funds",
            "risk_level": "Low",
            "risk_score": 3,
            "expected_return_rate": 12.0,
            "recommended_allocation": rec_low,
            "allocation_rationale": [
                f"Your savings rate is stable at {savings_rate:.0f}% - suitable for long-term investments.",
                "Steady income helps handle minor market fluctuations comfortably.",
                "Historical 12% returns comfortably outperform inflation."
            ],
            "holding_period": "5+ Years",
            "pros": [
                "Diversification across India's top 50 blue-chip companies",
                "Low management fee (Expense Ratio)",
                "Long term historical compounding growth"
            ],
            "cons": [
                "Potential for temporary drops of -20% to -30% during major market crashes",
                "Short term (1-2 yr) high volatility",
                "Returns can be negatively impacted by economic recessions"
            ],
            "risk_protection": [
                "Investment distributed across 50 companies",
                "20+ year performance track record",
                "Fully regulated by SEBI",
                "Highly liquid - check prices and sell at any time"
            ],
            "liquidity": "Yes",
            "ticker": "NIFTY50",
            "historical_data": {
                "current_price": 24500.0,
                "periods": {
                    "1": 23200.0,
                    "3": 18600.0,
                    "5": 15700.0,
                    "10": 8100.0
                }
            }
        },
        {
            "asset_name": "Tata Motors Stock",
            "asset_type": "stocks",
            "risk_level": "Medium",
            "risk_score": 6,
            "expected_return_rate": 16.5,
            "recommended_allocation": rec_med,
            "allocation_rationale": [
                "A growth compounder suited for moderate risk profiles.",
                "Strong growth segment potential in electric vehicles (EV).",
                f"Sufficient investable balance leaves emergency cash reserve untouched."
            ],
            "holding_period": "3-5 Years",
            "pros": [
                "EV market leadership in India",
                "Strong quarterly revenue growth",
                "Global automotive presence"
            ],
            "cons": [
                "Automotive demand cyclical factors risk",
                "High competition from Hyundai and Mahindra",
                "No guaranteed dividends payout"
            ],
            "risk_protection": [
                "Tata Group strong management backing",
                "Diversified passenger & commercial portfolio",
                "Strict stock exchange listing regulations"
            ],
            "liquidity": "Yes",
            "ticker": "TATOMOTORS",
            "historical_data": {
                "current_price": 950.0,
                "periods": {
                    "1": 900.0,
                    "3": 560.0,
                    "5": 340.0,
                    "10": 430.0
                }
            }
        },
        {
            "asset_name": "Bitcoin (BTC)",
            "asset_type": "stocks",
            "risk_level": "High",
            "risk_score": 9,
            "expected_return_rate": 35.0,
            "recommended_allocation": rec_high,
            "allocation_rationale": [
                "High volatility product suitable for aggressive allocations",
                "Allocating only a small percentage of savings preserves capital safety",
                "Inflation hedge store-of-value features"
            ],
            "holding_period": "5+ Years",
            "pros": [
                "Massive historical returns scaling",
                "Decentralized global digital asset network",
                "Increasing institutional adoption"
            ],
            "cons": [
                "Extreme price fluctuations (could drop 50%+ in months)",
                "Regulatory uncertainty in India",
                "No underlying cash flow or assets backing"
            ],
            "risk_protection": [
                "Cryptographic blockchain ledger security",
                "High global liquidity 24/7",
                "Fixed supply cap (21 Million coins max)"
            ],
            "liquidity": "Yes",
            "ticker": "BTC-USD",
            "historical_data": {
                "current_price": 5700000.0,
                "periods": {
                    "1": 5000000.0,
                    "3": 2200000.0,
                    "5": 3000000.0,
                    "10": 45000.0
                }
            }
        }
    ]

