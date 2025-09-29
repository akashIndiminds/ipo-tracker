# app/routes/ai_routes.py

from fastapi import APIRouter, Path, Query
from datetime import datetime
from ..controllers.ai_controller import ai_controller

router = APIRouter(prefix="/api/ai", tags=["AI Prediction"])

@router.post("/predict")
async def predict_all_current_ipos(date: str = Query(None, description="Date in YYYY-MM-DD format, defaults to today")):
    """
    Generate AI predictions for all current IPOs
    
    - Fetches current IPO data from NSE
    - Fetches subscription data
    - Generates AI predictions using Gemini
    - Saves predictions to file
    
    Query Parameters:
    - date: Optional date in YYYY-MM-DD format (defaults to today)
    
    Example: POST /api/ai/predict
    Example: POST /api/ai/predict?date=2025-09-29
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    return await ai_controller.predict_all_current_ipos(date)


@router.get("/predictions/{date}")
async def get_predictions_by_date(date: str = Path(..., description="Date in YYYY-MM-DD format")):
    """
    Get all AI predictions for a specific date
    
    Path Parameters:
    - date: Date in YYYY-MM-DD format
    
    Example: GET /api/ai/predictions/2025-09-29
    """
    return await ai_controller.get_predictions_by_date(date)


@router.get("/prediction/{symbol}/{date}")
async def get_prediction_by_symbol_and_date(
    symbol: str = Path(..., description="IPO symbol"),
    date: str = Path(..., description="Date in YYYY-MM-DD format")
):
    """
    Get AI prediction for specific symbol and date
    
    Path Parameters:
    - symbol: IPO symbol (e.g., SWIGGY, ZOMATO)
    - date: Date in YYYY-MM-DD format
    
    Example: GET /api/ai/prediction/SWIGGY/2025-09-29
    """
    return await ai_controller.get_prediction_by_symbol_and_date(symbol, date)