# app/controllers/ipo_controller.py
"""
IPO Controller - Handles HTTP requests and responses
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from app.services.ipo_service import IPOService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ipo", tags=["IPO"])

# Initialize service
ipo_service = IPOService()

@router.get("/current")
async def get_current_ipos(include_gmp: bool = Query(True, description="Include GMP data")):
    """Get current IPOs"""
    try:
        result = ipo_service.get_current_ipos(include_gmp)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to fetch data'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Controller error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upcoming")
async def get_upcoming_ipos(include_gmp: bool = Query(True, description="Include GMP data")):
    """Get upcoming IPOs"""
    try:
        result = ipo_service.get_upcoming_ipos(include_gmp)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to fetch data'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Controller error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/past")
async def get_past_ipos(days: int = Query(30, ge=1, le=90, description="Days to look back")):
    """Get past IPOs"""
    try:
        result = ipo_service.get_past_ipos(days)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to fetch data'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Controller error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_ipo_summary():
    """Get IPO summary"""
    try:
        result = ipo_service.get_ipo_summary()
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to fetch data'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Controller error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_nse_connection():
    """Test NSE connection"""
    try:
        scraper = ipo_service.scraper
        
        # Test different methods
        tests = {
            'cloudscraper': scraper._get_cookies_cloudscraper(),
            'requests': scraper._get_cookies_requests(),
            'current_ipos': len(scraper.get_current_ipos()) > 0,
            'market_indices': len(scraper.get_market_indices()) > 0
        }
        
        success_count = sum(1 for v in tests.values() if v)
        
        return {
            'success': success_count > 0,
            'tests_passed': f"{success_count}/{len(tests)}",
            'results': tests,
            'message': 'Connection test completed'
        }
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': 'Connection test failed'
        }
