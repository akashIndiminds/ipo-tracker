# app/routes/ai_routes.py
"""AI Routes - Gemini AI prediction endpoints"""

from fastapi import APIRouter, Path
from typing import Dict, Any

from ..controllers.ai_controller import ai_controller

router = APIRouter(prefix="/api/ai", tags=["Gemini AI Predictions"])

@router.post("/analyze-all")
async def analyze_all_ipos_with_ai() -> Dict[str, Any]:
    """
    Analyze All Current IPOs with Gemini AI
    
    This will:
    - Fetch all current IPOs
    - Send each to Gemini AI for analysis
    - Store predictions in JSON file
    - Return all predictions
    """
    return await ai_controller.analyze_current_ipos_with_ai()

@router.get("/prediction/{symbol}")
async def get_ai_prediction(
    symbol: str = Path(..., description="IPO symbol")
) -> Dict[str, Any]:
    """
    Get AI Prediction for Specific IPO
    
    Returns:
    - AI recommendation
    - Expected listing gain
    - Risk assessment
    - Market sentiment
    - Price targets
    """
    return await ai_controller.get_ai_prediction(symbol)

@router.post("/refresh")
async def refresh_ai_predictions() -> Dict[str, Any]:
    """
    Refresh All AI Predictions
    
    Clears cache and regenerates all predictions
    """
    return await ai_controller.refresh_all_ai_predictions()

@router.get("/stored-predictions")
async def get_stored_ai_predictions() -> Dict[str, Any]:
    """
    Get All Stored AI Predictions
    
    Returns all saved AI predictions from file
    """
    from ..services.gemini_ai_service import gemini_ai_service
    
    data = gemini_ai_service.load_ai_predictions()
    
    return {
        'success': bool(data.get('predictions')),
        'predictions': data.get('predictions', {}),
        'total': len(data.get('predictions', {}))
    }