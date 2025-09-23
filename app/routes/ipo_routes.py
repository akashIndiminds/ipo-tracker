# app/routes/ipo_routes.py
from fastapi import APIRouter, Query
from app.controllers.ipo_controller import ipo_controller

router = APIRouter(prefix="/api/ipo", tags=["IPO"])

@router.get("/current")
async def get_current_ipos(force_refresh: bool = Query(False)):
    """Get current/active IPOs"""
    return await ipo_controller.get_current_ipos(force_refresh)

@router.get("/upcoming")
async def get_upcoming_ipos(force_refresh: bool = Query(False)):
    """Get upcoming IPOs"""
    return await ipo_controller.get_upcoming_ipos(force_refresh)

@router.get("/{symbol}/subscription")
async def get_subscription_details(symbol: str, force_refresh: bool = Query(False)):
    """Get subscription details for specific IPO"""
    return await ipo_controller.get_subscription_details(symbol, force_refresh)

@router.get("/market/status")
async def get_market_status():
    """Get market status"""
    return await ipo_controller.get_market_status()

@router.get("/status")
async def get_system_status():
    """Get system status"""
    return await ipo_controller.get_system_status()

@router.post("/refresh")
async def refresh_all_data():
    """Refresh all cached data"""
    return await ipo_controller.refresh_all_data()