# app/utils/helpers.py
"""
Utility functions for IPO Tracker
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Union

def clean_text(text: str) -> str:
    """Clean and normalize text data"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text.strip())

def extract_number(text: str) -> float:
    """Extract number from text (handles ₹, %, etc.)"""
    if not text:
        return 0.0
    
    # Remove currency symbols and spaces
    cleaned = re.sub(r'[₹,%\s]', '', str(text))
    
    # Extract number
    match = re.search(r'[\d.]+', cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return 0.0
    return 0.0

def parse_date(date_str: str) -> int:
    """Calculate days from today to given date"""
    if not date_str:
        return 0
    
    try:
        # Handle different date formats
        if '-' in date_str:
            date_obj = datetime.strptime(date_str, '%d-%b-%Y')
        else:
            date_obj = datetime.strptime(date_str, '%d %b %Y')
        
        today = datetime.now()
        diff = (date_obj - today).days
        return max(0, diff)
    except:
        return 0

def clean_subscription_data(data: str) -> float:
    """Clean subscription times data"""
    if not data:
        return 0.0
    
    # Handle scientific notation
    try:
        return float(data)
    except:
        return 0.0

def calculate_risk_level(subscription_times: float, gmp: int) -> str:
    """Calculate risk level based on subscription and GMP"""
    if subscription_times >= 2.0 and gmp > 30:
        return "low"
    elif subscription_times >= 1.0 and gmp > 15:
        return "medium"
    else:
        return "high"

def format_currency(amount: Union[int, float]) -> str:
    """Format currency in Indian style"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.1f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.1f}L"
    else:
        return f"₹{amount:,.0f}"

