# app/routes/orchestrator_routes.py
"""
Orchestrator Routes - Handle sequential data initialization

Add to main.py:
    from app.routes import orchestrator_routes
    app.include_router(orchestrator_routes.router)
"""

from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional

from ..services.data_orchestrator import data_orchestrator

router = APIRouter(prefix="/api/orchestrator", tags=["Data Orchestrator"])

@router.post("/initialize")
async def initialize_all_data(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today"),
    background_tasks: BackgroundTasks = None
) -> dict:
    """
    Initialize ALL data in correct sequence
    
    Order:
    1. Current IPOs (NSE)
    2. Upcoming IPOs (NSE)
    3. Subscription Data (NSE)
    4. GMP Data (Web Scraping)
    5. Math Predictions
    6. AI Predictions
    7. Final Predictions
    
    Returns complete status of all steps
    """
    return await data_orchestrator.initialize_all_data(date)


@router.get("/status")
async def get_data_status():
    """
    Get current status of all data types
    
    Shows which data is loaded, when it was updated, and any errors
    """
    return data_orchestrator.get_status()


@router.post("/refresh/{data_type}")
async def refresh_specific_data(
    data_type: str,
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """
    Refresh specific data type only
    
    Valid types:
    - current_ipos
    - upcoming_ipos
    - subscription
    - gmp
    - math
    - ai
    - final
    """
    return await data_orchestrator.refresh_specific_data(data_type, date)