# app/routes/local_routes.py
"""Local Routes - Clean API for stored IPO data"""

from fastapi import APIRouter, Query
from typing import Dict, Any, Optional

from ..controllers.local_controller import local_controller

# Create router
router = APIRouter(prefix="/api/local", tags=["Local IPO Data"])

@router.get("/current")
async def get_current_ipos(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today")
) -> Dict[str, Any]:
    """
    Get current IPOs with subscription data
    
    Returns IPO details with Groww-style subscription breakdown:
    - QIB subscription
    - NII subscription  
    - Retail subscription
    - Total subscription
    
    Example: GET /api/local/current?date=2025-09-29
    """
    return await local_controller.get_current_ipos(date)


@router.get("/upcoming")
async def get_upcoming_ipos(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today")
) -> Dict[str, Any]:
    """
    Get upcoming IPOs
    
    Returns list of upcoming IPOs with basic details
    
    Example: GET /api/local/upcoming?date=2025-09-29
    """
    return await local_controller.get_upcoming_ipos(date)


@router.get("/subscription")
async def get_subscription_data(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today")
) -> Dict[str, Any]:
    """
    Get raw subscription data for all IPOs
    
    Returns detailed subscription breakdown for all symbols
    
    Example: GET /api/local/subscription?date=2025-09-29
    """
    return await local_controller.get_subscription_data(date)