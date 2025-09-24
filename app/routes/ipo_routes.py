# app/routes/ipo_routes.py
from fastapi import APIRouter, Query, HTTPException
from typing import Dict, Any

# Fixed imports
from ..controllers.ipo_controller import ipo_controller

# Create router
router = APIRouter(prefix="/api/ipo", tags=["IPO"])

@router.get("/current")
async def get_current_ipos(
    include_gmp: bool = Query(False, description="Include Grey Market Premium data")
) -> Dict[str, Any]:
    """Get current/active IPOs from NSE"""
    return await ipo_controller.get_current_ipos(include_gmp)

@router.get("/upcoming")
async def get_upcoming_ipos(
    include_gmp: bool = Query(False, description="Include Grey Market Premium data")
) -> Dict[str, Any]:
    """Get upcoming IPOs from NSE"""
    return await ipo_controller.get_upcoming_ipos(include_gmp)

@router.get("/market-status")
async def get_market_status() -> Dict[str, Any]:
    """Get current market status from NSE"""
    return await ipo_controller.get_market_status()

@router.get("/test")
async def test_nse_connection() -> Dict[str, Any]:
    """Test NSE API connectivity"""
    return await ipo_controller.test_nse_connection()

@router.post("/refresh")
async def refresh_nse_session() -> Dict[str, Any]:
    """Manually refresh NSE session and clear cache"""
    return await ipo_controller.refresh_session()

@router.post("/clear-cache")
async def clear_cache() -> Dict[str, Any]:
    """Clear cached data"""
    return await ipo_controller.clear_cache()