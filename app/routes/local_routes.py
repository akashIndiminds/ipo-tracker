# app/routes/local_routes.py
"""Local Routes - Stored JSON Data Endpoints"""

from fastapi import APIRouter, Query, Path
from typing import Dict, Any, Optional

from ..controllers.local_controller import local_controller

# Create router
router = APIRouter(prefix="/api/local", tags=["Local Stored Data"])

@router.get("/current-ipos")
async def get_stored_current_ipos(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
) -> Dict[str, Any]:
    """Get current IPOs from stored JSON file"""
    return await local_controller.get_stored_current_ipos(date)

@router.get("/upcoming-ipos")
async def get_stored_upcoming_ipos(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
) -> Dict[str, Any]:
    """Get upcoming IPOs from stored JSON file"""
    return await local_controller.get_stored_upcoming_ipos(date)

@router.get("/market-status")
async def get_stored_market_status(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
) -> Dict[str, Any]:
    """Get market status from stored JSON file"""
    return await local_controller.get_stored_market_status(date)

@router.get("/active-category")
async def get_stored_active_category(
    symbol: Optional[str] = Query(None, description="IPO symbol (optional)"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
) -> Dict[str, Any]:
    """Get IPO active category data from stored JSON file"""
    return await local_controller.get_stored_active_category(symbol, date)

@router.get("/available-dates/{data_type}")
async def get_available_dates(
    data_type: str = Path(..., description="Data type: current_ipos, upcoming_ipos, market_status, active_category")
) -> Dict[str, Any]:
    """Get list of available dates for a data type"""
    return await local_controller.get_available_dates(data_type)

@router.get("/summary")
async def get_data_summary() -> Dict[str, Any]:
    """Get summary of all stored data"""
    return await local_controller.get_data_summary()

@router.delete("/data/{data_type}/{date}")
async def delete_stored_data(
    data_type: str = Path(..., description="Data type: current_ipos, upcoming_ipos, market_status, active_category"),
    date: str = Path(..., description="Date in YYYY-MM-DD format")
) -> Dict[str, Any]:
    """Delete stored data for specific date"""
    return await local_controller.delete_stored_data(data_type, date)

@router.post("/cleanup/{data_type}")
async def cleanup_old_data(
    data_type: str = Path(..., description="Data type: current_ipos, upcoming_ipos, market_status, active_category"),
    keep_days: int = Query(30, description="Number of days to keep (default: 30)")
) -> Dict[str, Any]:
    """Cleanup old stored data, keeping only recent files"""
    return await local_controller.cleanup_old_data(data_type, keep_days)