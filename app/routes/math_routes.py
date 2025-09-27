# app/routes/math_routes.py

from fastapi import APIRouter, Path
from ..services.math_prediction import math_prediction_service
from ..services.nse_service import nse_service
from ..utils.file_storage import file_storage

router = APIRouter(prefix="/api/math", tags=["Math Prediction"])

@router.get("/predict/{symbol}")
async def get_math_prediction(symbol: str = Path(...)):
    """Get pure math prediction"""
    # Get IPO and subscription data
    current_ipos = nse_service.fetch_current_ipos()
    ipo_data = next((ipo for ipo in current_ipos if ipo['symbol'] == symbol.upper()), {})
    
    # Get subscription data
    subscription_data = nse_service.fetch_ipo_active_category(symbol)
    
    prediction = math_prediction_service.predict(ipo_data, subscription_data)
    file_storage.save_data(f"predictions/math/{symbol}", prediction)
    return prediction
