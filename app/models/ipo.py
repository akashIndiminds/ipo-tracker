from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from pyparsing import Dict

class IPOData(BaseModel):
    """IPO data model"""
    symbol: str = Field(..., description="IPO symbol/ticker")
    company_name: str = Field(..., description="Company name")
    series: Optional[str] = Field(None, description="Series (EQ, BE, etc.)")
    issue_start_date: Optional[str] = Field(None, description="Issue start date")
    issue_end_date: Optional[str] = Field(None, description="Issue end date")
    issue_price: Optional[str] = Field(None, description="Issue price range")
    issue_size: Optional[str] = Field(None, description="Issue size")
    status: Optional[str] = Field(None, description="IPO status")
    subscription_times: Optional[str] = Field(None, description="Subscription times")
    shares_offered: Optional[str] = Field(None, description="Number of shares offered")
    shares_bid: Optional[str] = Field(None, description="Number of shares bid")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "EXAMPLE",
                "company_name": "Example Company Limited",
                "series": "EQ",
                "issue_start_date": "20-Sep-2025",
                "issue_end_date": "24-Sep-2025",
                "issue_price": "Rs.100 to Rs.120",
                "issue_size": "50000000",
                "status": "Active",
                "subscription_times": "1.5",
                "shares_offered": "5000000",
                "shares_bid": "7500000"
            }
        }

class IPOSummary(BaseModel):
    """IPO summary model"""
    total_current: int = Field(..., description="Total current IPOs")
    total_upcoming: int = Field(..., description="Total upcoming IPOs") 
    total_past: int = Field(..., description="Total past IPOs")
    current_ipos: List[IPOData] = Field(default=[], description="Current IPO list")
    upcoming_ipos: List[IPOData] = Field(default=[], description="Upcoming IPO list")
    past_ipos: List[IPOData] = Field(default=[], description="Past IPO list")
    last_updated: str = Field(..., description="Last update timestamp")
    
class IPOResponse(BaseModel):
    """Standard IPO API response"""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    count: int = Field(..., description="Number of records")
    data: List[IPOData] = Field(default=[], description="IPO data list")
    timestamp: str = Field(..., description="Response timestamp")
    source: str = Field(default="NSE API", description="Data source")

class IPOSearchRequest(BaseModel):
    """IPO search request model"""
    query: str = Field(..., min_length=2, description="Search term")
    category: Optional[str] = Field("all", description="IPO category: current, upcoming, past, or all")
    limit: Optional[int] = Field(50, description="Maximum results to return")

class IPOAnalytics(BaseModel):
    """IPO analytics model"""
    total_market_value: Optional[float] = Field(None, description="Total market value")
    average_subscription: Optional[float] = Field(None, description="Average subscription rate")
    sector_distribution: List[Dict] = Field(default=[], description="Sector-wise distribution")
    performance_metrics: Dict = Field(default={}, description="Performance metrics")