# STEP 2: Create app/routers/ipo.py
# ===============================================

from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from app.services.enhanced_nse_service import AntiBlockingNSEService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/test")
async def test_nse_connection():
    """Test NSE API connection and get sample data"""
    try:
        print("\n🧪 Testing NSE API Connection...")
        nse_service = AntiBlockingNSEService()
        
        # Test all endpoints
        results = {}
        
        # Test current IPOs
        current_ipos = nse_service.get_current_ipos()
        results['current_ipos'] = {
            'count': len(current_ipos) if current_ipos else 0,
            'status': 'success' if current_ipos else 'failed',
            'sample': current_ipos[:2] if current_ipos else []
        }
        
        # Test upcoming IPOs
        upcoming_ipos = nse_service.get_upcoming_ipos()
        results['upcoming_ipos'] = {
            'count': len(upcoming_ipos) if upcoming_ipos else 0,
            'status': 'success' if upcoming_ipos else 'failed',
            'sample': upcoming_ipos[:2] if upcoming_ipos else []
        }
        
        # Test past IPOs
        past_ipos = nse_service.get_past_ipos(7)
        results['past_ipos'] = {
            'count': len(past_ipos) if past_ipos else 0,
            'status': 'success' if past_ipos else 'failed',
            'sample': past_ipos[:2] if past_ipos else []
        }
        
        # Test market indices
        market_indices = nse_service.get_market_indices()
        results['market_indices'] = {
            'count': len(market_indices) if market_indices else 0,
            'status': 'success' if market_indices else 'failed',
            'sample': market_indices[:2] if market_indices else []
        }
        
        # Overall status
        total_success = sum(1 for r in results.values() if r['status'] == 'success')
        overall_status = 'success' if total_success >= 2 else 'partial' if total_success >= 1 else 'failed'
        
        logger.info(f"NSE API test completed: {total_success}/4 endpoints working")
        
        return {
            "success": True,
            "overall_status": overall_status,
            "message": f"NSE API test completed: {total_success}/4 endpoints working",
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"NSE API test failed: {e}")
        return {
            "success": False,
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/current")
async def get_current_ipos():
    """Get all current active IPOs"""
    try:
        print("\n🚀 API Call: Current IPOs")
        nse_service = AntiBlockingNSEService()
        current_ipos = nse_service.get_current_ipos()
        
        logger.info(f"Fetched {len(current_ipos)} current IPOs")
        
        return {
            "success": True,
            "count": len(current_ipos),
            "data": current_ipos,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching current IPOs: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/upcoming")
async def get_upcoming_ipos():
    """Get all upcoming IPOs"""
    try:
        print("\n🚀 API Call: Upcoming IPOs")
        nse_service = AntiBlockingNSEService()
        upcoming_ipos = nse_service.get_upcoming_ipos()
        
        logger.info(f"Fetched {len(upcoming_ipos)} upcoming IPOs")
        
        return {
            "success": True,
            "count": len(upcoming_ipos),
            "data": upcoming_ipos,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching upcoming IPOs: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/past")
async def get_past_ipos(days_back: int = 30):
    """Get past IPO performance"""
    try:
        print(f"\n🚀 API Call: Past IPOs (Last {days_back} days)")
        
        if days_back > 90:
            days_back = 90  # Limit to 90 days max
        
        nse_service = AntiBlockingNSEService()
        past_ipos = nse_service.get_past_ipos(days_back)
        
        logger.info(f"Fetched {len(past_ipos)} past IPOs")
        
        return {
            "success": True,
            "count": len(past_ipos),
            "data": past_ipos,
            "days_back": days_back,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching past IPOs: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/summary")
async def get_ipo_summary():
    """Get complete IPO summary with all data"""
    try:
        print("\n🚀 API Call: Complete IPO Summary")
        nse_service = AntiBlockingNSEService()
        
        # Get all data
        current_ipos = nse_service.get_current_ipos() or []
        upcoming_ipos = nse_service.get_upcoming_ipos() or []
        past_ipos = nse_service.get_past_ipos(30) or []
        
        # Create summary
        summary = {
            "current_ipos": {
                "count": len(current_ipos),
                "data": current_ipos[:5]  # Show first 5
            },
            "upcoming_ipos": {
                "count": len(upcoming_ipos),
                "data": upcoming_ipos[:5]  # Show first 5
            },
            "past_ipos": {
                "count": len(past_ipos),
                "data": past_ipos[:5]  # Show first 5
            },
            "statistics": {
                "total_active": len(current_ipos),
                "total_upcoming": len(upcoming_ipos),
                "total_past_30_days": len(past_ipos)
            }
        }
        
        logger.info("IPO summary generated successfully")
        
        return {
            "success": True,
            "summary": summary,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error generating IPO summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
