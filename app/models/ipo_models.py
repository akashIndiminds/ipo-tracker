# app/models/ipo_models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class IPOData(BaseModel):
    """Single IPO record model"""
    symbol: str = Field(..., description="IPO symbol")
    company_name: str = Field(..., description="Company name")
    series: str = Field(default="EQ", description="Series (EQ/SME)")
    issue_start_date: str = Field(default="", description="Issue start date")
    issue_end_date: str = Field(default="", description="Issue end date")
    issue_price: str = Field(default="", description="Issue price range")
    issue_size: str = Field(default="", description="Issue size")
    status: str = Field(default="Unknown", description="IPO status")
    subscription_times: str = Field(default="0.00x", description="Subscription times")
    shares_offered: Optional[int] = Field(default=0, description="Shares offered")
    shares_bid: Optional[int] = Field(default=0, description="Shares bid")
    subscription_ratio: Optional[float] = Field(default=0.0, description="Subscription ratio")
    category: Optional[str] = Field(default="", description="IPO category")
    grade: Optional[str] = Field(default="", description="IPO grade")
    processed_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_source: str = Field(default="NSE_API", description="Data source")

class SubscriptionCategory(BaseModel):
    """Subscription category data"""
    category_name: str = Field(..., description="Category name")
    subscription_times: str = Field(..., description="Subscription times (e.g., 2.50x)")
    subscription_times_numeric: float = Field(..., description="Numeric subscription value")
    shares_offered: int = Field(..., description="Shares offered")
    shares_bid: int = Field(..., description="Shares bid for")
    status: str = Field(..., description="Subscription status")

class SubscriptionData(BaseModel):
    """IPO subscription details"""
    symbol: str = Field(..., description="IPO symbol")
    last_updated: str = Field(..., description="Last update timestamp")
    total_subscription: str = Field(..., description="Total subscription (e.g., 3.75x)")
    total_subscription_numeric: Optional[float] = Field(default=0.0, description="Numeric total subscription")
    overall_status: str = Field(default="Unknown", description="Overall subscription status")
    categories: Dict[str, SubscriptionCategory] = Field(default={}, description="Category-wise subscription")
    raw_data_available: bool = Field(default=True, description="Whether raw data is available")

class MarketStatus(BaseModel):
    """Market status model"""
    market: str = Field(..., description="Market name")
    market_status: str = Field(..., description="Market status (Open/Closed)")
    trade_date: str = Field(..., description="Trade date")
    index: Optional[str] = Field(default="", description="Index name")

class IPOResponse(BaseModel):
    """Standard IPO API response"""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    data: List[IPOData] = Field(default=[], description="IPO data list")
    count: int = Field(default=0, description="Number of records")
    metadata: Dict[str, Any] = Field(default={}, description="Response metadata")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class SubscriptionResponse(BaseModel):
    """Subscription API response"""
    success: bool = Field(..., description="Success status")
    symbol: str = Field(..., description="IPO symbol")
    subscription_data: Optional[SubscriptionData] = Field(default=None, description="Subscription details")
    message: str = Field(default="", description="Response message")
    from_cache: bool = Field(default=False, description="Whether data is from cache")
    cache_age: Optional[int] = Field(default=None, description="Cache age in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class MarketStatusResponse(BaseModel):
    """Market status API response"""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    data: List[MarketStatus] = Field(default=[], description="Market status data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(default=False, description="Success status")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class SystemStatus(BaseModel):
    """System status model"""
    service_name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    last_check: str = Field(..., description="Last check timestamp")
    details: Dict[str, Any] = Field(default={}, description="Additional details")

class SystemStatusResponse(BaseModel):
    """System status API response"""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    system_status: List[SystemStatus] = Field(default=[], description="System status list")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class RefreshResponse(BaseModel):
    """Data refresh API response"""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    refresh_summary: Dict[str, str] = Field(default={}, description="Refresh summary")
    success_rate: Optional[float] = Field(default=None, description="Success rate percentage")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# Request models (if needed for POST requests)
class RefreshRequest(BaseModel):
    """Refresh request model"""
    force_refresh: bool = Field(default=True, description="Force refresh all data")
    data_types: Optional[List[str]] = Field(default=None, description="Specific data types to refresh")

class CacheSettings(BaseModel):
    """Cache settings model"""
    data_type: str = Field(..., description="Data type")
    cache_duration: int = Field(..., description="Cache duration in seconds")
    enabled: bool = Field(default=True, description="Cache enabled status")

class IPOSummary(BaseModel):
    """IPO Summary model"""
    total_current: int = Field(default=0, description="Total current IPOs")
    total_upcoming: int = Field(default=0, description="Total upcoming IPOs")
    total_active: int = Field(default=0, description="Total active IPOs")
    market_activity: str = Field(default="Low", description="Market activity level")
    summary_date: str = Field(default_factory=lambda: datetime.now().isoformat())