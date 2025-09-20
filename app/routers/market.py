# app/routers/market.py
# Copy this COMPLETE content to your market.py file

from fastapi import APIRouter, HTTPException
from app.services.enhanced_nse_service import AntiBlockingNSEService
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/indices")
async def get_market_indices():
    """Get major market indices"""
    try:
        print("\n🚀 API Call: Market Indices")
        nse_service = AntiBlockingNSEService()
        indices = nse_service.get_market_indices()
        
        # Filter major indices
        major_indices = [
            'NIFTY 50', 'NIFTY BANK', 'NIFTY IT', 'NIFTY FMCG', 
            'NIFTY AUTO', 'NIFTY MIDCAP 100', 'NIFTY SMLCAP 100'
        ]
        
        filtered_indices = []
        if indices:
            filtered_indices = [
                idx for idx in indices 
                if idx.get('indexName') in major_indices
            ]
        
        logger.info(f"Fetched {len(filtered_indices)} market indices")
        
        return {
            "success": True,
            "count": len(filtered_indices),
            "data": filtered_indices,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching market indices: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/status")
async def get_market_status():
    """Get market status"""
    try:
        print("\n🚀 API Call: Market Status")
        nse_service = AntiBlockingNSEService()
        status = nse_service.get_market_status()
        
        return {
            "success": True,
            "data": status,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching market status: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/dashboard")
async def get_market_dashboard():
    """Get complete market dashboard data"""
    try:
        print("\n🚀 API Call: Market Dashboard")
        nse_service = AntiBlockingNSEService()
        
        # Get all market data
        indices = nse_service.get_market_indices() or []
        status = nse_service.get_market_status() or []
        
        # Filter major indices
        major_indices = ['NIFTY 50', 'NIFTY BANK', 'NIFTY IT', 'NIFTY FMCG']
        filtered_indices = [
            idx for idx in indices 
            if idx.get('indexName') in major_indices
        ]
        
        # Calculate market sentiment
        positive_indices = len([
            idx for idx in filtered_indices 
            if idx.get('percChange', 0) > 0
        ])
        total_indices = len(filtered_indices)
        sentiment_score = (positive_indices / total_indices) * 100 if total_indices > 0 else 50
        market_sentiment = "Positive" if sentiment_score > 50 else "Negative"
        
        dashboard_data = {
            "market_status": status,
            "major_indices": filtered_indices,
            "market_sentiment": market_sentiment,
            "sentiment_score": round(sentiment_score, 1),
            "summary": {
                "total_indices": total_indices,
                "positive_indices": positive_indices,
                "negative_indices": total_indices - positive_indices
            }
        }
        
        return {
            "success": True,
            "dashboard": dashboard_data,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Test endpoint
@router.get("/test")
async def test_market_endpoints():
    """Test market endpoints"""
    try:
        print("\n🧪 Testing Market Endpoints...")
        nse_service = AntiBlockingNSEService()
        
        # Test indices
        indices = nse_service.get_market_indices()
        indices_count = len(indices) if indices else 0
        
        # Test status
        status = nse_service.get_market_status()
        status_count = len(status) if status else 0
        
        results = {
            "indices": {
                "count": indices_count,
                "status": "success" if indices_count > 0 else "failed"
            },
            "market_status": {
                "count": status_count,
                "status": "success" if status_count > 0 else "failed"
            }
        }
        
        total_success = sum(1 for r in results.values() if r['status'] == 'success')
        
        return {
            "success": True,
            "message": f"Market endpoints test: {total_success}/2 working",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }