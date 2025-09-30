# app/controllers/math_controller.py

from typing import Dict, List, Optional
import logging
from datetime import datetime
from ..services.math_prediction import math_prediction_service
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class MathController:
    """Math Controller - handles request/response for all math prediction endpoints"""
    
    async def predict_all_by_date(self, date: str) -> Dict:
        """
        Method 1: Generate predictions for ALL IPOs on a given date
        Used by: POST /api/math/predict/{date}
        """
        try:
            # Load current IPO data for the date
            current_data = file_storage.load_data("nse/current", date)
            if not current_data or 'data' not in current_data:
                return {
                    'success': False,
                    'error': f'No IPO data found for date: {date}',
                    'date': date,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Load subscription data for the date
            subscription_data = file_storage.load_data("nse/subscription", date)
            subscription_map = {}
            
            # Extract subscription map correctly from nested structure
            if subscription_data and 'data' in subscription_data:
                inner_data = subscription_data['data']
                if 'data' in inner_data and isinstance(inner_data['data'], dict):
                    subscription_map = inner_data['data']
                    logger.info(f"Loaded subscription data for {len(subscription_map)} symbols")
            
            # Generate predictions for each IPO
            predictions = []
            total_ipos = len(current_data['data'])
            successful = 0
            failed = 0
            
            for ipo in current_data['data']:
                try:
                    symbol = ipo['symbol']
                    # Get symbol-specific subscription data
                    sub_data = subscription_map.get(symbol, None)
                    
                    if sub_data:
                        logger.info(f"Found subscription data for {symbol}: {sub_data.get('total_subscription', 0)}x")
                    else:
                        logger.warning(f"No subscription data found for {symbol}")
                    
                    # Call prediction service
                    prediction = math_prediction_service.predict(ipo, sub_data)
                    predictions.append(prediction)
                    successful += 1
                    
                except Exception as e:
                    logger.error(f"Failed to predict {ipo.get('symbol')}: {e}")
                    failed += 1
            
            # Prepare response
            result = {
                'success': True,
                'date': date,
                'summary': {
                    'total_ipos': total_ipos,
                    'successful_predictions': successful,
                    'failed_predictions': failed
                },
                'predictions': predictions,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save predictions - overwrites existing file for the same date
            save_success = file_storage.save_data("predictions/math", result, date)
            logger.info(f"Predictions saved successfully: {save_success}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in predict_all_by_date: {e}")
            return {
                'success': False,
                'error': str(e),
                'date': date,
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_all_predictions_by_date(self, date: str) -> Dict:
        """
        Method 2: Get ALL saved predictions for a date
        Used by: GET /api/math/predictions/{date}
        """
        try:
            # Load saved predictions
            saved_predictions = file_storage.load_data("predictions/math", date)
            
            if not saved_predictions:
                return {
                    'success': False,
                    'error': f'No predictions found for date: {date}. Generate predictions first using POST /api/math/predict/{date}',
                    'date': date,
                    'timestamp': datetime.now().isoformat()
                }
            
            return saved_predictions
            
        except Exception as e:
            logger.error(f"Error in get_all_predictions_by_date: {e}")
            return {
                'success': False,
                'error': str(e),
                'date': date,
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_prediction_by_symbol_and_date(self, symbol: str, date: str) -> Dict:
        """
        Method 3: Get prediction for ONE specific symbol and date
        Used by: GET /api/math/prediction/{symbol}/{date}
        """
        try:
            symbol = symbol.upper()
            
            # First try to get from saved predictions
            all_predictions = file_storage.load_data("predictions/math", date)
            
            if all_predictions and 'predictions' in all_predictions:
                # Search for the symbol in saved predictions
                for pred in all_predictions['predictions']:
                    if pred.get('symbol') == symbol:
                        return {
                            'success': True,
                            'prediction': pred,
                            'source': 'cached',
                            'timestamp': datetime.now().isoformat()
                        }
            
            # If not found in saved predictions, generate fresh
            logger.info(f"Prediction not found in cache, generating fresh for {symbol}")
            
            # Load IPO data
            current_data = file_storage.load_data("nse/current", date)
            if not current_data or 'data' not in current_data:
                return {
                    'success': False,
                    'error': f'No IPO data found for date: {date}',
                    'symbol': symbol,
                    'date': date,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Find the specific IPO
            ipo_data = None
            for ipo in current_data['data']:
                if ipo['symbol'] == symbol:
                    ipo_data = ipo
                    break
            
            if not ipo_data:
                return {
                    'success': False,
                    'error': f'IPO with symbol {symbol} not found on {date}',
                    'symbol': symbol,
                    'date': date,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Load subscription data
            subscription_data_all = file_storage.load_data("nse/subscription", date)
            subscription_data = None
            
            # Extract symbol-specific subscription data from nested structure
            if subscription_data_all and 'data' in subscription_data_all:
                inner_data = subscription_data_all['data']
                if 'data' in inner_data and isinstance(inner_data['data'], dict):
                    symbol_subs = inner_data['data']
                    subscription_data = symbol_subs.get(symbol, None)
                    
                    if subscription_data:
                        logger.info(f"Found subscription data for {symbol}: {subscription_data.get('total_subscription', 0)}x")
                    else:
                        logger.warning(f"No subscription data found for {symbol}")
            
            # Generate prediction
            prediction = math_prediction_service.predict(ipo_data, subscription_data)
            
            return {
                'success': True,
                'prediction': prediction,
                'source': 'fresh',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in get_prediction_by_symbol_and_date: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'date': date,
                'timestamp': datetime.now().isoformat()
            }

math_controller = MathController()