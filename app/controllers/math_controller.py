# app/controllers/math_controller.py

from typing import Dict, Optional
import logging
from ..services.math_prediction import math_prediction_service
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class MathController:
    """Math Controller - handles pure mathematical predictions"""
    
    async def get_prediction(self, ipo_data: Dict, subscription_data: Optional[Dict] = None) -> Dict:
        """Get math prediction for IPO"""
        try:
            symbol = ipo_data.get('symbol', 'UNKNOWN')
            
            prediction = math_prediction_service.predict(ipo_data, subscription_data)
            
            # Save prediction
            file_storage.save_data(f"predictions/math/{symbol}", prediction)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Math prediction error: {e}")
            return {
                'symbol': ipo_data.get('symbol', 'UNKNOWN'),
                'source': 'MATH',
                'error': str(e)
            }

math_controller = MathController()
