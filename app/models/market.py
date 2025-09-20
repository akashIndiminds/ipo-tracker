
# app/routers/market.py
"""
Market related API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.services.nse_service import NSEService
from app.models.market import MarketIndex, MarketSummary, MarketStatus

router = APIRouter()
nse_service = NSEService()

@router.get("/status", response_model=MarketStatus)
async def get_market_status():
    """Get current market status"""
    try:
        status = nse_service.get_market_status()
        if not status:
            raise HTTPException(status_code=404, detail="Market status not available")
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market status: {str(e)}")

@router.get("/indices", response_model=List[MarketIndex])
async def get_market_indices():
    """Get all major market indices"""
    try:
        indices = nse_service.get_market_indices()
        
        # Filter to show only major indices
        major_indices = [
            'NIFTY 50', 'NIFTY BANK', 'NIFTY IT', 'NIFTY FMCG', 
            'NIFTY AUTO', 'NIFTY MIDCAP 100', 'NIFTY SMLCAP 100'
        ]
        
        filtered_indices = [idx for idx in indices if idx.index_name in major_indices]
        return filtered_indices
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market indices: {str(e)}")

@router.get("/summary", response_model=MarketSummary)
async def get_market_summary():
    """Get market summary statistics"""
    try:
        summary = nse_service.get_market_summary()
        if not summary:
            raise HTTPException(status_code=404, detail="Market summary not available")
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market summary: {str(e)}")

@router.get("/dashboard")
async def get_market_dashboard():
    """Get comprehensive market dashboard data"""
    try:
        # Get all market data
        status = nse_service.get_market_status()
        indices = nse_service.get_market_indices()
        summary = nse_service.get_market_summary()
        
        # Filter major indices
        major_indices = [
            'NIFTY 50', 'NIFTY BANK', 'NIFTY IT', 'NIFTY FMCG'
        ]
        filtered_indices = [idx for idx in indices if idx.index_name in major_indices]
        
        # Calculate market sentiment
        positive_indices = len([idx for idx in filtered_indices if idx.change_percent > 0])
        total_indices = len(filtered_indices)
        market_sentiment = "Positive" if positive_indices > total_indices/2 else "Negative"
        
        dashboard_data = {
            "market_status": status.dict() if status else None,
            "major_indices": [idx.dict() for idx in filtered_indices],
            "market_summary": summary.dict() if summary else None,
            "market_sentiment": market_sentiment,
            "sentiment_score": (positive_indices / total_indices) * 100 if total_indices > 0 else 50
        }
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")
