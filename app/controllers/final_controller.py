# app/controllers/final_controller.py - FIXED with proper storage

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
    """Final Controller - combines all predictions with proper storage"""
    
    async def get_final_prediction(self, symbol: str, date: str = None) -> Dict:
        """Get combined prediction from all sources for a symbol"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Generating final prediction for {symbol} on {date}")
            
            # Get NSE data
            current_result = await nse_controller.get_current_ipos()
            if not current_result['success']:
                return {
                    'success': False,
                    'error': 'Failed to fetch NSE data',
                    'symbol': symbol,
                    'date': date
                }
            
            # Find IPO
            ipo_data = None
            for ipo in current_result['data']:
                if ipo['symbol'].upper() == symbol.upper():
                    ipo_data = ipo
                    break
            
            if not ipo_data:
                return {
                    'success': False,
                    'error': f'IPO {symbol} not found',
                    'symbol': symbol,
                    'date': date
                }
            
            # Get subscription data
            from ..services.nse_service import nse_service
            sub_result = nse_service.fetch_all_subscriptions([symbol])
            subscription_data = sub_result.get('data', {}).get(symbol) if sub_result else None
            
            # Get all predictions independently
            gmp_result = await gmp_controller.get_symbol_prediction(symbol, date)
            gmp_pred = gmp_result.get('data') if gmp_result.get('success') else {}
            
            math_result = await math_controller.get_prediction_by_symbol_and_date(symbol, date)
            math_pred = math_result.get('prediction') if math_result.get('success') else {}
            
            ai_result = await ai_controller.get_prediction_by_symbol_and_date(symbol, date)
            ai_pred = ai_result.get('prediction') if ai_result.get('success') else {}
            
            # Combine predictions
            final_pred = final_prediction_service.combine_predictions(
                gmp_pred, math_pred, ai_pred, ipo_data
            )
            
            # Add metadata
            final_pred['date'] = date
            final_pred['generated_at'] = datetime.now().isoformat()
            
            # Save final prediction to data/predictions/final_prediction/{date}/{symbol}.json
            save_path = f"predictions/final_prediction/{date}"
            save_success = file_storage.save_data(save_path, final_pred, symbol)
            
            if save_success:
                logger.info(f"✅ Final prediction saved: data/predictions/final_prediction/{date}/{symbol}.json")
            
            final_pred['success'] = True
            final_pred['storage_path'] = f'data/predictions/final_prediction/{date}/{symbol}.json'
            
            return final_pred
            
        except Exception as e:
            logger.error(f"Final prediction error for {symbol}: {e}")
            return {
                'success': False,
                'symbol': symbol,
                'date': date,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_all_ipos(self, date: str = None) -> Dict:
        """Process all current IPOs and generate final predictions"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Starting batch IPO processing for date: {date}")
            
            # Step 1: Fetch current IPOs
            current_result = await nse_controller.get_current_ipos()
            if not current_result['success']:
                return {
                    'success': False,
                    'error': 'Failed to fetch current IPOs',
                    'date': date
                }
            
            current_ipos = current_result['data']
            logger.info(f"Found {len(current_ipos)} current IPOs")
            
            # Step 2: Fetch GMP data (once for all)
            gmp_result = await gmp_controller.fetch_gmp_data()
            logger.info(f"GMP fetch: {gmp_result.get('message', 'completed')}")
            
            # Step 3: Generate predictions for each source
            symbols = [ipo.get('symbol') for ipo in current_ipos if ipo.get('symbol')]
            
            # Generate Math predictions for all
            await math_controller.predict_all_by_date(date)
            logger.info("Math predictions generated")
            
            # Generate AI predictions for all
            await ai_controller.predict_all_current_ipos(date)
            logger.info("AI predictions generated")
            
            # Step 4: Process each IPO
            results = []
            success_count = 0
            fail_count = 0
            
            for ipo in current_ipos:
                symbol = ipo.get('symbol', '')
                if not symbol:
                    continue
                
                logger.info(f"Processing final prediction for {symbol}")
                
                try:
                    # Get final prediction (which combines all 3)
                    final_pred = await self.get_final_prediction(symbol, date)
                    
                    if final_pred.get('success'):
                        results.append({
                            'symbol': symbol,
                            'company': ipo.get('company_name'),
                            'recommendation': final_pred.get('final_recommendation'),
                            'expected_gain': final_pred.get('expected_gain_percent'),
                            'risk': final_pred.get('risk_level'),
                            'listing_price': final_pred.get('expected_listing_price'),
                            'status': 'success'
                        })
                        success_count += 1
                    else:
                        results.append({
                            'symbol': symbol,
                            'error': final_pred.get('error', 'Unknown error'),
                            'status': 'failed'
                        })
                        fail_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    results.append({
                        'symbol': symbol,
                        'error': str(e),
                        'status': 'failed'
                    })
                    fail_count += 1
            
            # Save batch summary to data/predictions/final_prediction/{date}/batch_summary.json
            batch_data = {
                'date': date,
                'timestamp': datetime.now().isoformat(),
                'total_processed': len(results),
                'success': success_count,
                'failed': fail_count,
                'success_rate': round((success_count / len(results)) * 100, 1) if results else 0,
                'results': results
            }
            
            batch_path = f"predictions/final_prediction/{date}"
            file_storage.save_data(batch_path, batch_data, "batch_summary")
            
            logger.info(f"✅ Batch summary saved: data/predictions/final_prediction/{date}/batch_summary.json")
            
            return {
                'success': True,
                'date': date,
                'summary': {
                    'total': len(results),
                    'success': success_count,
                    'failed': fail_count,
                    'success_rate': batch_data['success_rate']
                },
                'results': results,
                'storage_path': f'data/predictions/final_prediction/{date}/',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return {
                'success': False,
                'date': date,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_stored_final_prediction(self, symbol: str, date: str = None) -> Dict:
        """Get stored final prediction for a symbol"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Load from data/predictions/final_prediction/{date}/{symbol}.json
            load_path = f"predictions/final_prediction/{date}"
            stored_data = file_storage.load_data(load_path, symbol)
            
            if not stored_data:
                return {
                    'success': False,
                    'message': f'No final prediction found for {symbol} on {date}',
                    'symbol': symbol,
                    'date': date,
                    'suggestion': 'Generate prediction first using POST /api/predict/{symbol}'
                }
            
            return {
                'success': True,
                'data': stored_data.get('data'),
                'metadata': stored_data.get('metadata'),
                'symbol': symbol,
                'date': date
            }
            
        except Exception as e:
            logger.error(f"Error loading stored prediction for {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'date': date
            }

final_controller = FinalController()