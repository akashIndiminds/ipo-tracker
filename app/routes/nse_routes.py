# app/routes/ipo_routes.py
"""IPO Routes - NSE Live Data Endpoints"""

from fastapi import APIRouter, Query
from typing import Dict, Any

from ..controllers.nse_controller import nse_controller

# Create router
router = APIRouter(prefix="/api/ipo", tags=["NSE Live IPO Data"])

@router.get("/current")
async def get_current_ipos(
    include_gmp: bool = Query(False, description="Include Grey Market Premium data"),
    save_data: bool = Query(True, description="Save data to JSON file")
) -> Dict[str, Any]:
    """Get current/active IPOs from NSE and save to file"""
    return await nse_controller.get_current_ipos(include_gmp, save_data)

@router.get("/upcoming")
async def get_upcoming_ipos(
    include_gmp: bool = Query(False, description="Include Grey Market Premium data"),
    save_data: bool = Query(True, description="Save data to JSON file")
) -> Dict[str, Any]:
    """Get upcoming IPOs from NSE and save to file"""
    return await nse_controller.get_upcoming_ipos(include_gmp, save_data)

@router.get("/market-status")
async def get_market_status(
    save_data: bool = Query(True, description="Save data to JSON file")
) -> Dict[str, Any]:
    """Get current market status from NSE and save to file"""
    return await nse_controller.get_market_status(save_data)

@router.get("/active-category/{symbol}")
async def get_ipo_active_category(
    symbol: str,
    save_data: bool = Query(True, description="Save data to JSON file")
) -> Dict[str, Any]:
    """Get IPO active category with bid information for specific symbol"""
    return await nse_controller.get_ipo_active_category(symbol, save_data)

@router.get("/test")
async def test_nse_connection() -> Dict[str, Any]:
    """Test NSE API connectivity and all endpoints"""
    return await nse_controller.test_nse_connection()

@router.post("/refresh")
async def refresh_nse_session() -> Dict[str, Any]:
    """Manually refresh NSE session and clear cache"""
    return await nse_controller.refresh_session()

@router.post("/fetch-all")
async def fetch_and_save_all_data() -> Dict[str, Any]:
    """Fetch all NSE data (current, upcoming, market status) and save to files"""
    return await nse_controller.fetch_and_save_all_data()