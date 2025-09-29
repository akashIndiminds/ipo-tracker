# app/routes/predict_routes.py - FIXED Final Prediction Routes

from fastapi import APIRouter, Path, Query
from ..controllers.final_controller import final_controller
from typing import Optional

router = APIRouter(prefix="/api/predict", tags=["Final Prediction"])

@router.post("/{symbol}")
async def generate_final_prediction(
    symbol: str = Path(..., description="IPO symbol"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
):
    """
    Generate final combined prediction for a symbol
    
    Combines:
    - GMP prediction
    - Math prediction  
    - AI prediction
    
    Saves to: data/predictions/final_prediction/{date}/{symbol}.json
    
    Example: POST /api/predict/SWIGGY?date=2025-09-29
    """
    return await final_controller.get_final_prediction(symbol, date)


@router.get("/{symbol}")
async def get_stored_final_prediction(
    symbol: str = Path(..., description="IPO symbol"),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
):
    """
    Get stored final prediction for a symbol
    
    Loads from: data/predictions/final_prediction/{date}/{symbol}.json
    
    Example: GET /api/predict/SWIGGY?date=2025-09-29
    """
    return await final_controller.get_stored_final_prediction(symbol, date)


@router.post("/batch")
async def process_all_ipos(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (default: today)")
):
    """
    Process all current IPOs and generate final predictions
    
    Steps:
    1. Fetches all current IPOs
    2. Generates GMP data
    3. Generates Math predictions
    4. Generates AI predictions
    5. Combines all for final prediction
    
    Saves:
    - Individual predictions: data/predictions/final_prediction/{date}/{symbol}.json
    - Batch summary: data/predictions/final_prediction/{date}/batch_summary.json
    
    Example: POST /api/predict/batch?date=2025-09-29
    """
    return await final_controller.process_all_ipos(date)


@router.get("/health")
async def health_check():
    """Health check endpoint for final prediction service"""
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "Final Prediction Service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "storage_locations": {
            "gmp": "data/predictions/gmp/{date}.json",
            "math": "data/predictions/math/{date}.json",
            "ai": "data/predictions/ai/{date}.json",
            "final": "data/predictions/final_prediction/{date}/{symbol}.json"
        }
    }