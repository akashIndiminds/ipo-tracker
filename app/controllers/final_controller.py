# app/controllers/final_controller.py

from typing import Dict, List
import logging
from datetime import datetime
from ..services.final_prediction import final_prediction_service
from ..controllers.nse_controller import nse_controller
from ..controllers.gmp_controller import gmp_controller
from ..controllers.math_controller import math_controller
from ..controllers.ai_controller import ai_controller
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class FinalController:
    """Final Controller - combines all predictions"""
    
    async def get_final_prediction(self, symbol: str) -> Dict:
        """Get combined prediction from all sources"""
        try:
            # Get NSE data
            current_result = await nse_controller.get_current_ipos()
            if not current_result['success']:
                return {'error': 'Failed to fetch NSE data'}
            
            # Find IPO
            ipo_data = None
            for ipo in current_result['data']:
                if ipo['symbol'].upper() == symbol.upper():
                    ipo_data = ipo
                    break
            
            if not ipo_data:
                return {'error': f'IPO {symbol} not found'}
            
            # Get subscription data
            sub_result = await nse_controller.get_subscription_data(symbol)
            subscription_data = sub_result.get('data') if sub_result['success'] else None
            
            # Get all predictions independently
            gmp_pred = await gmp_controller.get_gmp_prediction(symbol, ipo_data)
            math_pred = await math_controller.get_prediction(ipo_data, subscription_data)
            ai_pred = await ai_controller.get_prediction(ipo_data, subscription_data)
            
            # Combine predictions
            final_pred = final_prediction_service.combine_predictions(
                gmp_pred, math_pred, ai_pred, ipo_data
            )
            
            # Save final prediction
            file_storage.save_data(f"predictions/final/{symbol}", final_pred)
            
            return final_pred
            
        except Exception as e:
            logger.error(f"Final prediction error for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e)
            }
    
    async def process_all_ipos(self) -> Dict:
        """Process all current IPOs"""
        try:
            logger.info("Starting batch IPO processing")
            
            # Step 1: Fetch current IPOs
            current_result = await nse_controller.get_current_ipos()
            if not current_result['success']:
                return {'error': 'Failed to fetch current IPOs'}
            
            current_ipos = current_result['data']
            logger.info(f"Found {len(current_ipos)} current IPOs")
            
            # Step 2: Fetch GMP data (once for all)
            gmp_result = await gmp_controller.fetch_gmp_data()
            logger.info(f"GMP fetch: {gmp_result}")
            
            # Step 3: Process each IPO
            results = []
            success_count = 0
            fail_count = 0
            
            for ipo in current_ipos:
                symbol = ipo.get('symbol', '')
                if not symbol:
                    continue
                
                logger.info(f"Processing {symbol}")
                
                try:
                    # Get subscription data
                    sub_result = await nse_controller.get_subscription_data(symbol)
                    subscription_data = sub_result.get('data') if sub_result['success'] else None
                    
                    # Get all predictions
                    gmp_pred = await gmp_controller.get_gmp_prediction(symbol, ipo)
                    math_pred = await math_controller.get_prediction(ipo, subscription_data)
                    ai_pred = await ai_controller.get_prediction(ipo, subscription_data)
                    
                    # Combine
                    final_pred = final_prediction_service.combine_predictions(
                        gmp_pred, math_pred, ai_pred, ipo
                    )
                    
                    # Save
                    file_storage.save_data(f"predictions/final/{symbol}", final_pred)
                    
                    results.append({
                        'symbol': symbol,
                        'company': ipo.get('company_name'),
                        'recommendation': final_pred.get('final_recommendation'),
                        'expected_gain': final_pred.get('expected_gain_percent'),
                        'risk': final_pred.get('risk_level'),
                        'listing_price': final_pred.get('expected_listing_price')
                    })
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    results.append({
                        'symbol': symbol,
                        'error': str(e)
                    })
                    fail_count += 1
            
            # Save batch results
            batch_data = {
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(results),
                'success': success_count,
                'failed': fail_count,
                'results': results
            }
            
            file_storage.save_data("predictions/final/batch", batch_data)
            
            return {
                'success': True,
                'summary': {
                    'total': len(results),
                    'success': success_count,
                    'failed': fail_count
                },
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

final_controller = FinalController()