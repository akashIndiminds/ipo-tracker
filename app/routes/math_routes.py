# app/routes/math_routes.py

from fastapi import APIRouter, Path, HTTPException
from datetime import datetime
from ..controllers.math_controller import math_controller

router = APIRouter(prefix="/api/math", tags=["Math Prediction"])

@router.post("/predict/{date}")
async def predict_all_ipos(
    date: str = Path(..., description="Date in YYYY-MM-DD format", example="2025-09-29")
):
    """
    Route 1: Generate math predictions for ALL IPOs on a specific date
    
    This endpoint:
    - Loads all current IPOs for the date from data/nse/current/{date}.json
    - Loads subscription data from data/nse/subscription/{date}.json
    - Generates predictions using research-based mathematical models
    - Saves predictions to data/predictions/math/{date}.json
    - Returns all predictions with detailed analysis
    
    Example: POST {{base_url}}/api/math/predict/2025-09-29
    """
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD (e.g., 2025-09-29)"
        )
    
    result = await math_controller.predict_all_by_date(date)
    
    if not result.get('success'):
        raise HTTPException(
            status_code=404 if 'not found' in result.get('error', '').lower() else 500,
            detail=result.get('error', 'Prediction generation failed')
        )
    
    return result


@router.get("/predictions/{date}")
async def get_all_predictions(
    date: str = Path(..., description="Date in YYYY-MM-DD format", example="2025-09-29")
):
    """
    Route 2: Get ALL saved math predictions for a specific date
    
    Returns previously generated predictions from data/predictions/math/{date}.json
    If predictions don't exist, use POST /api/math/predict/{date} first to generate them.
    
    Example: GET {{base_url}}/api/math/predictions/2025-09-29
    """
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD (e.g., 2025-09-29)"
        )
    
    result = await math_controller.get_all_predictions_by_date(date)
    
    if not result.get('success'):
        raise HTTPException(
            status_code=404 if 'not found' in result.get('error', '').lower() else 500,
            detail=result.get('error', 'Failed to retrieve predictions')
        )
    
    return result


@router.get("/prediction/{symbol}/{date}")
async def get_single_prediction(
    symbol: str = Path(..., description="IPO symbol", example="TRUALT"),
    date: str = Path(..., description="Date in YYYY-MM-DD format", example="2025-09-29")
):
    """
    Route 3: Get math prediction for ONE specific IPO symbol and date
    
    First tries to get from saved predictions (cached).
    If not found, generates fresh prediction on-the-fly.
    
    Example: GET {{base_url}}/api/math/prediction/TRUALT/2025-09-29
    """
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD (e.g., 2025-09-29)"
        )
    
    result = await math_controller.get_prediction_by_symbol_and_date(symbol, date)
    
    if not result.get('success'):
        raise HTTPException(
            status_code=404 if 'not found' in result.get('error', '').lower() else 500,
            detail=result.get('error', 'Failed to retrieve prediction')
        )
    
    return result


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Math Prediction Service",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }