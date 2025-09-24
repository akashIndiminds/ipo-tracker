# app/models/response_models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.models.ipo_models import IPOData, MarketStatus

class BaseResponse(BaseModel):
    """Base API Response"""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    timestamp: str = Field(..., description="Response timestamp")

class IPOResponse(BaseResponse):
    """IPO API Response"""
    count: int = Field(..., description="Number of records")
    data: List[IPOData] = Field(..., description="IPO data list")
    include_gmp: bool = Field(default=False, description="Whether GMP data is included")
    source: str = Field(default="NSE API", description="Data source")

class MarketStatusResponse(BaseResponse):
    """Market Status API Response"""
    count: int = Field(..., description="Number of records")
    data: List[MarketStatus] = Field(..., description="Market status data")
    source: str = Field(default="NSE API", description="Data source")

class ConnectionTestResponse(BaseResponse):
    """Connection Test Response"""
    test_results: Dict[str, Any] = Field(..., description="Test results")
    recommendations: List[str] = Field(..., description="Recommendations")
    session_info: Dict[str, Any] = Field(..., description="Session information")

class ErrorResponse(BaseResponse):
    """Error Response"""
    success: bool = Field(default=False, description="Success status")
    error: Optional[str] = Field(default=None, description="Error code")
    detail: Optional[str] = Field(default=None, description="Error detail")