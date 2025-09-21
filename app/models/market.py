from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MarketIndex(BaseModel):
    """Market index model"""
    index_name: str = Field(..., description="Index name")
    last: Optional[float] = Field(None, description="Last price")
    open: Optional[float] = Field(None, description="Opening price")
    high: Optional[float] = Field(None, description="Day high")
    low: Optional[float] = Field(None, description="Day low") 
    previous_close: Optional[float] = Field(None, description="Previous close")
    change: Optional[float] = Field(None, description="Point change")
    percent_change: Optional[float] = Field(None, description="Percentage change")
    year_high: Optional[float] = Field(None, description="52-week high")
    year_low: Optional[float] = Field(None, description="52-week low")
    time_val: Optional[str] = Field(None, description="Last update time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "index_name": "NIFTY 50",
                "last": 25300.50,
                "open": 25280.00,
                "high": 25450.75,
                "low": 25200.25,
                "previous_close": 25350.00,
                "change": -49.50,
                "percent_change": -0.19,
                "year_high": 26277.35,
                "year_low": 21743.65,
                "time_val": "20-Sep-2025 15:30"
            }
        }

class MarketStatus(BaseModel):
    """Market status model"""
    market: str = Field(..., description="Market name")
    market_status: str = Field(..., description="Market status (Open/Closed)")
    trade_date: str = Field(..., description="Trading date")
    index: Optional[str] = Field(None, description="Associated index")

class MarketSentiment(BaseModel):
    """Market sentiment model"""
    sentiment: str = Field(..., description="Overall sentiment (positive/negative/neutral)")
    sentiment_score: float = Field(..., description="Sentiment score (0-100)")
    positive_count: int = Field(..., description="Number of positive indices")
    negative_count: int = Field(..., description="Number of negative indices")
    total_count: int = Field(..., description="Total indices analyzed")

class MarketHighlights(BaseModel):
    """Market highlights model"""
    top_gainers: List[MarketIndex] = Field(default=[], description="Top gaining indices")
    top_losers: List[MarketIndex] = Field(default=[], description="Top losing indices")
    most_active: List[MarketIndex] = Field(default=[], description="Most active indices")

class MarketDashboard(BaseModel):
    """Market dashboard model"""
    market_status: List[MarketStatus] = Field(default=[], description="Market status list")
    major_indices: List[MarketIndex] = Field(default=[], description="Major indices")
    market_sentiment: MarketSentiment = Field(..., description="Market sentiment analysis")
    highlights: MarketHighlights = Field(..., description="Market highlights")
    last_updated: str = Field(..., description="Last update timestamp")

class MarketResponse(BaseModel):
    """Standard market API response"""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    count: int = Field(..., description="Number of records")
    data: List[MarketIndex] = Field(default=[], description="Market data list")
    timestamp: str = Field(..., description="Response timestamp")
    source: str = Field(default="NSE API", description="Data source")

class MarketOverview(BaseModel):
    """Market overview model"""
    nifty_50: Optional[MarketIndex] = Field(None, description="NIFTY 50 data")
    bank_nifty: Optional[MarketIndex] = Field(None, description="BANK NIFTY data")
    market_cap: Optional[float] = Field(None, description="Total market capitalization")
    trading_volume: Optional[float] = Field(None, description="Total trading volume")
    advance_decline_ratio: Optional[float] = Field(None, description="Advance/Decline ratio")