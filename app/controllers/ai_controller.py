# app/controllers/ai_controller.py
"""AI Controller - Handles Gemini AI predictions"""

import logging
from typing import Dict, Any
from fastapi import HTTPException

from ..services.gemini_ai_service import gemini_ai_service
from ..services.nse_service import nse_service

logger = logging.getLogger(__name__)

class AIController:
    """Controller for AI predictions"""
    
    def __init__(self):
        self.ai_service = gemini_ai_service
        self.nse_service = nse_service
    
    async def analyze_current_ipos_with_ai(self) -> Dict[str, Any]:
        """Analyze all current IPOs with Gemini AI"""
        try:
            logger.info("Starting AI analysis for current IPOs")
            
            # Get current IPOs
            current_ipos = self.nse_service.fetch_current_ipos()
            
            if not current_ipos:
                raise HTTPException(
                    status_code=404,
                    detail="No current IPOs found"
                )
            
            # Analyze with AI
            result = self.ai_service.analyze_all_current_ipos(current_ipos)
            
            return {
                'success': True,
                'message': f'AI analyzed {result["total_analyzed"]} IPOs',
                'total_analyzed': result['total_analyzed'],
                'predictions': result['predictions'],
                'timestamp': result['timestamp']
            }
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"AI analysis failed: {str(e)}"
            )
    
    async def get_ai_prediction(self, symbol: str) -> Dict[str, Any]:
        """Get AI prediction for specific symbol"""
        try:
            # Check saved predictions first
            prediction = self.ai_service.get_ai_prediction_for_symbol(symbol)
            
            if prediction:
                return {
                    'success': True,
                    'source': 'CACHED',
                    'prediction': prediction
                }
            
            # Generate new prediction
            current_ipos = self.nse_service.fetch_current_ipos()
            ipo_data = None
            
            for ipo in current_ipos:
                if ipo.get('symbol', '').upper() == symbol.upper():
                    ipo_data = ipo
                    break
            
            if not ipo_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"IPO {symbol} not found"
                )
            
            # Get AI prediction
            prediction = self.ai_service.analyze_ipo_with_ai(ipo_data)
            
            return {
                'success': True,
                'source': 'FRESH',
                'prediction': prediction
            }
            
        except Exception as e:
            logger.error(f"Error getting AI prediction for {symbol}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get AI prediction: {str(e)}"
            )
    
    async def refresh_all_ai_predictions(self) -> Dict[str, Any]:
        """Refresh AI predictions for all current IPOs"""
        try:
            # Clear cache
            self.ai_service.predictions_cache.clear()
            
            # Re-analyze all
            return await self.analyze_current_ipos_with_ai()
            
        except Exception as e:
            logger.error(f"Error refreshing AI predictions: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to refresh AI predictions: {str(e)}"
            )

# Create instance
ai_controller = AIController()