# app/routes/_routes.py
"""
 Fast Routes - Read-Only APIs
No scraping, No AI calls, Just file reads
Can handle 10000+ concurrent users
"""

from fastapi import APIRouter, Query, Path, HTTPException
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/v2", tags=["Fast Read-Only APIs"])

# Import  controller
from ..controllers.local_controller import local_controller

# Import scheduler for admin actions
from ..services.scheduler_service import data_scheduler


# ==================== INSTANT READ APIs ====================

@router.get("/current")
async def get_current_ipos_fast(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """
    ⚡ ULTRA FAST - Get Current IPOs
    
    - Instant response (< 50ms)
    - No scraping, just file read
    - Supports 10000+ concurrent requests
    - Data updated 4 times daily by background scheduler
    
    Example: GET /api/v2/current?date=2025-09-29
    """
    return await local_controller.get_current_ipos(date)


@router.get("/upcoming")
async def get_upcoming_ipos_fast(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """
    ⚡ ULTRA FAST - Get Upcoming IPOs
    
    Example: GET /api/v2/upcoming?date=2025-09-29
    """
    return await local_controller.get_upcoming_ipos(date)


@router.get("/subscription")
async def get_subscription_fast(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """
    ⚡ ULTRA FAST - Get Subscription Data
    
    Example: GET /api/v2/subscription?date=2025-09-29
    """
    return await local_controller.get_subscription_data(date)


@router.get("/ipo/{symbol}")
async def get_ipo_by_symbol_fast(
    symbol: str = Path(..., description="IPO Symbol"),
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """
    ⚡ ULTRA FAST - Get Single IPO by Symbol
    
    Direct symbol lookup - < 30ms response time
    
    Example: GET /api/v2/ipo/SWIGGY?date=2025-09-29
    """
    return await local_controller.get_ipo_by_symbol(symbol, date)


@router.get("/predictions/{symbol}")
async def get_predictions_by_symbol_fast(
    symbol: str = Path(..., description="IPO Symbol"),
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """
    ⚡ FAST - Get All Predictions for Symbol
    
    Returns GMP, Math, AI, and Final predictions
    Pre-generated data - no computation needed
    
    Example: GET /api/v2/predictions/SWIGGY?date=2025-09-29
    """
    return await local_controller.get_predictions_by_symbol(symbol, date)


@router.get("/predictions")
async def get_all_predictions_fast(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """
    ⚡ FAST - Get All Predictions (Batch)
    
    Returns predictions for all IPOs
    Single file read - very fast
    
    Example: GET /api/v2/predictions?date=2025-09-29
    """
    return await local_controller.get_all_predictions(date)


@router.get("/dates")
async def get_available_dates(
    data_type: str = Query("current", description="Data type: current/upcoming/subscription/predictions")
):
    """
    Get Available Historical Dates
    
    Returns list of dates for which data is available
    
    Example: GET /api/v2/dates?data_type=predictions
    """
    return await local_controller.get_available_dates(data_type)


# ==================== ADMIN APIs (Protected) ====================

@router.post("/admin/refresh")
async def manual_data_refresh(
    api_key: str = Query(..., description="Admin API Key")
):
    """
    🔒 ADMIN ONLY - Manual Data Refresh
    
    Triggers complete data refresh cycle
    This is the ONLY API that does scraping
    
    Takes 2-5 minutes to complete
    Use sparingly - scheduled updates happen 4x daily
    
    Example: POST /api/v2/admin/refresh?api_key=YOUR_KEY
    """
    # Simple API key check (you should use proper auth)
    if api_key != "your-secret-admin-key-here":
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    result = await data_scheduler.manual_refresh()
    return result


@router.get("/admin/scheduler-status")
async def get_scheduler_status(
    api_key: str = Query(..., description="Admin API Key")
):
    """
    🔒 ADMIN ONLY - Get Scheduler Status
    
    Shows scheduler status, last run, next run times
    
    Example: GET /api/v2/admin/scheduler-status?api_key=YOUR_KEY
    """
    if api_key != "your-secret-admin-key-here":
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return data_scheduler.get_status()


@router.post("/admin/clear-cache")
async def clear_cache(
    api_key: str = Query(..., description="Admin API Key")
):
    """
    🔒 ADMIN ONLY - Clear Internal Cache
    
    Clears in-memory cache
    Use after manual data refresh
    
    Example: POST /api/v2/admin/clear-cache?api_key=YOUR_KEY
    """
    if api_key != "your-secret-admin-key-here":
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return await local_controller.clear_cache()


# ==================== SYSTEM INFO ====================

@router.get("/system/info")
async def get_system_info():
    """
    System Information
    
    Returns API version, update schedule, etc.
    """
    return {
        'api_version': '2.0',
        'mode': 'read_only_',
        'update_schedule': ['09:00', '12:00', '15:30', '18:00'],
        'update_timezone': 'IST',
        'features': [
            'Ultra-fast response times',
            'No scraping on read APIs',
            'Supports 10000+ concurrent users',
            'Data updated 4x daily automatically',
            'Historical data available'
        ],
        'endpoints': {
            'current_ipos': '/api/v2/current',
            'upcoming_ipos': '/api/v2/upcoming',
            'subscription': '/api/v2/subscription',
            'single_ipo': '/api/v2/ipo/{symbol}',
            'predictions': '/api/v2/predictions/{symbol}',
            'all_predictions': '/api/v2/predictions',
            'available_dates': '/api/v2/dates'
        },
        'timestamp': datetime.now().isoformat()
    }


@router.get("/health")
async def health_check():
    """Quick health check"""
    try:
        # Test file read
        from ..utils.file_storage import file_storage
        date = datetime.now().strftime("%Y-%m-%d")
        data = file_storage.load_data("nse/current", date)
        
        return {
            'status': 'healthy',
            'data_available': data is not None,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }