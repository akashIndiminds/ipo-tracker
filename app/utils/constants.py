
# app/utils/constants.py
"""
Constants for IPO Tracker
"""

# API Endpoints
NSE_ENDPOINTS = {
    "CURRENT_IPOS": "/ipo-current-issue",
    "UPCOMING_IPOS": "/all-upcoming-issues?category=ipo",
    "MARKET_STATUS": "/marketStatus",
    "ALL_INDICES": "/allIndices",
    "MARKET_SUMMARY": "/NextApi/apiClient?functionName=getMarketTurnoverSummary"
}

# GMP Sources
GMP_SOURCES = {
    "IPOWATCH": "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/",
    "CHITTORGARH": "https://www.chittorgarh.com/ipo_grey_market_premium.asp"
}

# Risk Levels
RISK_LEVELS = {
    "LOW": {"min_subscription": 2.0, "min_gmp": 30},
    "MEDIUM": {"min_subscription": 1.0, "min_gmp": 15},
    "HIGH": {"min_subscription": 0.0, "min_gmp": 0}
}

# Notification Types
NOTIFICATION_TYPES = {
    "SUBSCRIPTION_MILESTONE": "subscription_milestone",
    "GMP_CHANGE": "gmp_change",
    "IPO_OPENING": "ipo_opening",
    "IPO_CLOSING": "ipo_closing",
    "LISTING_DATE": "listing_date",
    "DAILY_SUMMARY": "daily_summary"
}

# Market Timings (IST)
MARKET_TIMINGS = {
    "PRE_OPEN": "09:00",
    "OPEN": "09:15", 
    "CLOSE": "15:30",
    "POST_CLOSE": "16:00"
}

# Major Indices for Dashboard
MAJOR_INDICES = [
    "NIFTY 50",
    "NIFTY BANK", 
    "NIFTY IT",
    "NIFTY FMCG",
    "NIFTY AUTO",
    "NIFTY MIDCAP 100",
    "NIFTY SMLCAP 100"
]

# Response Messages (Hindi + English)
MESSAGES = {
    "hi": {
        "market_open": "बाज़ार खुला है",
        "market_closed": "बाज़ार बंद है", 
        "ipo_fully_subscribed": "IPO पूरी तरह भर गया है",
        "high_gmp": "अच्छा GMP मिल रहा है",
        "investment_advice": "निवेश की सलाह"
    },
    "en": {
        "market_open": "Market is Open",
        "market_closed": "Market is Closed",
        "ipo_fully_subscribed": "IPO is Fully Subscribed", 
        "high_gmp": "Good GMP Available",
        "investment_advice": "Investment Advice"
    }
}