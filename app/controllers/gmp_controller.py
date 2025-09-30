# app/controllers/gmp_controller.py

from typing import Dict, Optional
import logging
from datetime import datetime
from ..services.gmp_service import gmp_service

logger = logging.getLogger(__name__)

class GMPController:
    """GMP Controller - Simple 3 endpoint handling with correct storage"""
    
    def __init__(self):
        self.gmp_service = gmp_service
    
    async def fetch_gmp_data(self) -> Dict:
        """Handle GMP data fetch request - filters for current IPOs only"""
        try:
            logger.info("Processing GMP fetch request for current IPOs")
            
            # Call service for business logic
            result = self.gmp_service.fetch_current_gmp()
            
            # Handle response formatting
            if result.get('success'):
                return {
                    'success': True,
                    'message': result.get('message'),
                    'current_ipos_count': result.get('current_ipos_count', 0),
                    'matched_gmp_entries': result.get('matched_gmp_entries', 0),
                    'total_sources': result.get('total_sources', 0),
                    'successful_sources': result.get('successful_sources', 0),
                    'timestamp': result.get('timestamp')
                }
            else:
                return {
                    'success': False,
                    'message': result.get('message', 'Failed to fetch GMP data'),
                    'error': result.get('error'),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"GMP Controller fetch error: {e}")
            return {
                'success': False,
                'message': 'GMP data fetch failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_current_predictions(self, date: Optional[str] = None) -> Dict:
        """Handle current predictions request - all IPOs for given date"""
        try:
            logger.info(f"Processing current predictions request for date: {date}")
            
            # Call service for business logic
            result = self.gmp_service.get_current_predictions(date)
            
            # Handle response
            if result.get('success'):
                return {
                    'success': True,
                    'date': result.get('date'),
                    'total_current_ipos': result.get('total_current_ipos', 0),
                    'predictions': result.get('predictions', {}),
                    'timestamp': result.get('timestamp')
                }
            else:
                error_code = result.get('error_code', 'UNKNOWN_ERROR')
                
                # Customize response based on error type
                if error_code == 'NO_CURRENT_IPOS':
                    return {
                        'success': False,
                        'message': 'No current IPOs found for this date',
                        'error_code': error_code,
                        'suggestion': 'Check if IPOs are available for this date',
                        'date': date or datetime.now().strftime('%Y-%m-%d'),
                        'timestamp': datetime.now().isoformat()
                    }
                elif error_code == 'NO_GMP_DATA':
                    return {
                        'success': False,
                        'message': 'No GMP data available. Please fetch GMP data first.',
                        'error_code': error_code,
                        'suggestion': 'Run POST /api/gmp/fetch first to get GMP data',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'message': result.get('message', 'Current predictions failed'),
                        'error_code': error_code,
                        'error': result.get('error'),
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"GMP Controller current predictions error: {e}")
            return {
                'success': False,
                'message': 'Current predictions request failed',
                'error': str(e),
                'error_code': 'CONTROLLER_ERROR',
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_symbol_prediction(self, symbol: str, date: Optional[str] = None) -> Dict:
        """Handle individual symbol prediction request"""
        try:
            logger.info(f"Processing prediction request for symbol: {symbol}")
            
            # Input validation
            if not symbol or not symbol.strip():
                return {
                    'success': False,
                    'message': 'Symbol parameter is required',
                    'error_code': 'INVALID_SYMBOL',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Call service for business logic
            result = self.gmp_service.get_symbol_prediction(symbol, date)
            
            # Handle response
            if result.get('success'):
                return {
                    'success': True,
                    'symbol': symbol.upper(),
                    'data': result.get('data'),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                error_code = result.get('error_code', 'UNKNOWN_ERROR')
                
                # Customize response based on error type
                if error_code == 'SYMBOL_NOT_FOUND':
                    return {
                        'success': False,
                        'symbol': symbol.upper(),
                        'message': f'Symbol {symbol.upper()} not found in current IPOs',
                        'error_code': error_code,
                        'available_symbols': result.get('available_symbols', []),
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'symbol': symbol.upper(),
                        'message': result.get('message', 'Symbol prediction failed'),
                        'error_code': error_code,
                        'error': result.get('error'),
                        'timestamp': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.error(f"GMP Controller symbol prediction error for {symbol}: {e}")
            return {
                'success': False,
                'symbol': symbol.upper() if symbol else 'UNKNOWN',
                'message': 'Symbol prediction request failed',
                'error': str(e),
                'error_code': 'CONTROLLER_ERROR',
                'timestamp': datetime.now().isoformat()
            }

# Create controller instance
gmp_controller = GMPController()