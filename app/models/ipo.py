
# app/models/past_ipo.py
"""
Model for past IPO data
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PastIPO(BaseModel):
    symbol: str
    company_name: str
    listing_date: str
    issue_price: str
    listing_price: Optional[float] = None
    listing_gain_percent: Optional[float] = None
    current_price: Optional[float] = None
    performance_status: Optional[str] = "unknown"  # profit, loss, neutral
    
class IPOPerformanceAnalysis(BaseModel):
    total_ipos: int
    profitable_ipos: int
    loss_making_ipos: int
    success_rate: float
    average_listing_gain: float
    best_performer: Optional[PastIPO] = None
    worst_performer: Optional[PastIPO] = None
