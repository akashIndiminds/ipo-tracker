# app/controllers/gmp_controller.py

from typing import Dict
import logging
from ..services.gmp_service import gmp_service
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class GMPController:
    """GMP Controller - handles GMP data and predictions"""
    
    async def fetch_gmp_data(self) -> Dict:
        """Fetch last month GMP data"""
        try:
            result = gmp_service.fetch_last_month_gmp()
            
            if result['success']:
                # Save raw GMP data
                file_storage.save_data("gmp/raw", result['data'])
                
                return {
                    'success': True,
                    'message': f"Fetched {result['total']} IPOs GMP data",
                    'total': result['total'],
                    'period': 'last_month'
                }
            
            return {
                'success': False,
                'message': 'Failed to fetch GMP data'
            }
            
        except Exception as e:
            logger.error(f"GMP Controller error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_gmp_prediction(self, symbol: str, ipo_data: Dict) -> Dict:
        """Get GMP's own prediction for symbol"""
        try:
            prediction = gmp_service.get_gmp_prediction(symbol, ipo_data)
            
            # Save prediction
            file_storage.save_data(f"gmp/predictions/{symbol}", prediction)
            
            return prediction
            
        except Exception as e:
            logger.error(f"GMP prediction error for {symbol}: {e}")
            return {
                'symbol': symbol,
                'source': 'GMP',
                'error': str(e)
            }

gmp_controller = GMPController()