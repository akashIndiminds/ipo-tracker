# app/routes/gmp_routes.py

from fastapi import APIRouter, Path, Query
from ..controllers.gmp_controller import gmp_controller
from typing import Optional

router = APIRouter(prefix="/api/gmp", tags=["GMP"])

@router.post("/fetch")
async def fetch_gmp_data():
    """
    Fetch current GMP data for current IPOs only
    
    Process:
    1. Gets current IPOs from stored NSE data
    2. Scrapes GMP data from sources
    3. Filters only current IPO related data
    4. Stores filtered data in: gmp_current/date.json
    
    Returns:
    - success: bool
    - message: str
    - current_ipos_count: int
    - matched_gmp_entries: int
    """
    return await gmp_controller.fetch_gmp_data()

@router.get("/predict/{symbol}")
async def get_gmp_prediction(
    symbol: str = Path(..., description="IPO symbol (from NSE current IPOs)"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
):
    """
    Get GMP prediction for specific symbol
    
    Args:
    - symbol: IPO symbol (e.g., TRUALT)
    - date: Optional date for historical data
    
    Returns:
    - success: bool
    - symbol: str
    - data: dict (IPO + GMP data)
    """
    return await gmp_controller.get_symbol_prediction(symbol, date)

@router.get("/current")
async def get_current_predictions(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
):
    """
    Get all current IPOs with their GMP data for given date
    
    Args:
    - date: Optional date (default: today)
    
    Returns:
    - success: bool
    - date: str
    - total_current_ipos: int
    - predictions: dict (all current IPOs with GMP data)
    """
    return await gmp_controller.get_current_predictions(date)