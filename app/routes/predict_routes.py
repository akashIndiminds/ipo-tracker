# app/routes/predict_routes.py

from fastapi import APIRouter, Path, Query
from ..controllers.final_controller import final_controller
from typing import Optional

router = APIRouter(prefix="/api/predict", tags=["Final Prediction"])

# IMPORTANT: Batch route PEHLE define karo
@router.post("/batch")
async def process_all_ipos_batch(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Process all current IPOs - Complete Analysis"""
    return await final_controller.process_all_ipos(date)


# Single IPO route BAAD mein
@router.post("/{symbol}")
async def generate_final_prediction(
    symbol: str = Path(..., description="IPO symbol"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Generate Final Prediction for Single IPO"""
    return await final_controller.get_final_prediction(symbol, date)


@router.get("/batch/summary")
async def get_batch_summary(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Get Batch Summary"""
    return await final_controller.get_batch_summary(date)


@router.get("/{symbol}")
async def get_stored_final_prediction(
    symbol: str = Path(..., description="IPO symbol"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format")
):
    """Get Stored Final Prediction"""
    return await final_controller.get_stored_final_prediction(symbol, date)