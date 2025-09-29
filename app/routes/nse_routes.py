# app/routes/nse_routes.py
"""NSE Routes - 5 Essential Endpoints Only"""

from fastapi import APIRouter, Query
from typing import Dict, Any

from ..controllers.nse_controller import nse_controller

# Create router
router = APIRouter(prefix="/api/ipo", tags=["NSE Live IPO Data"])

@router.get("/current")
async def get_current_ipos(
    save_data: bool = Query(True, description="Save data to JSON file")
) -> Dict[str, Any]:
    """Get current/active IPOs from NSE and save to file"""
    return await nse_controller.get_current_ipos(save_data)

@router.get("/upcoming")
async def get_upcoming_ipos(
    save_data: bool = Query(True, description="Save data to JSON file")
) -> Dict[str, Any]:
    """Get upcoming IPOs from NSE and save to file"""
    return await nse_controller.get_upcoming_ipos(save_data)

@router.get("/subscription")
async def get_all_subscriptions(
    save_data: bool = Query(True, description="Save data to JSON file")
) -> Dict[str, Any]:
    """Get subscription data for all current IPOs and save to file"""
    return await nse_controller.get_all_subscriptions(save_data)

@router.get("/test")
async def test_nse_connection() -> Dict[str, Any]:
    """Test NSE API connectivity and all endpoints"""
    return await nse_controller.test_nse_connection()

@router.post("/refresh")
async def refresh_nse_session() -> Dict[str, Any]:
    """Manually refresh NSE session and clear cache"""
    return await nse_controller.refresh_session()