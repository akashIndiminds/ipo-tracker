# app/controllers/final_controller.py - FIXED VERSION

from typing import Dict, List
import logging
from datetime import datetime
from ..services.final_prediction import final_prediction_service
from ..controllers.gmp_controller import gmp_controller
from ..controllers.math_controller import math_controller
from ..controllers.ai_controller import ai_controller
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class FinalController:
    """Final Prediction Controller - Uses STORED data, no live API calls"""
    
    async def get_final_prediction(self, symbol: str, date: str = None) -> Dict:
        """Generate intelligent final prediction for a single IPO"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Starting final prediction for {symbol} on {date}")
            
            # Load stored current IPO data
            stored_current = file_storage.load_data("nse/current", date)
            
            if not stored_current or 'data' not in stored_current:
                return {
                    'success': False,
                    'error': f'No stored current IPO data found for date: {date}',
                    'symbol': symbol,
                    'date': date,
                    'suggestion': f'First fetch current IPOs: GET /api/ipo/current',
                    'timestamp': datetime.now().isoformat()
                }
            
            current_ipos = stored_current['data']
            
            # Find the specific IPO
            ipo_data = None
            for ipo in current_ipos:
                if ipo['symbol'].upper() == symbol.upper():
                    ipo_data = ipo
                    break
            
            if not ipo_data:
                available_symbols = [ipo['symbol'] for ipo in current_ipos]
                return {
                    'success': False,
                    'error': f'IPO {symbol} not found in stored data for {date}',
                    'symbol': symbol,
                    'date': date,
                    'available_ipos': available_symbols,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Get GMP prediction
            gmp_result = await gmp_controller.get_symbol_prediction(symbol, date)
            
            # FIXED: Properly extract GMP data from nested structure
            if gmp_result.get('success') and gmp_result.get('data'):
                # Extract the actual gmp_data from nested structure
                ipo_gmp_data = gmp_result['data']
                
                if 'gmp_data' in ipo_gmp_data:
                    gmp_pred = ipo_gmp_data['gmp_data']
                    
                    # Ensure has_data flag is set correctly
                    if gmp_pred.get('found'):
                        gmp_pred['has_data'] = True
                        
                        # Set expected_gain_percent if not present
                        if 'expected_gain_percent' not in gmp_pred:
                            if 'listing_gain' in gmp_pred and gmp_pred['listing_gain'] is not None:
                                gmp_pred['expected_gain_percent'] = gmp_pred['listing_gain']
                            else:
                                gmp_pred['expected_gain_percent'] = 0
                        
                        logger.info(f"✅ GMP data found for {symbol}: gain={gmp_pred.get('expected_gain_percent', 0)}%")
                    else:
                        gmp_pred['has_data'] = False
                        gmp_pred['expected_gain_percent'] = 0
                        logger.info(f"❌ No GMP data available for {symbol}")
                else:
                    gmp_pred = {'has_data': False, 'found': False, 'expected_gain_percent': 0}
                    logger.info(f"⚠️ GMP data structure missing for {symbol}")
            else:
                gmp_pred = {'has_data': False, 'found': False, 'expected_gain_percent': 0}
                logger.info(f"❌ GMP fetch failed for {symbol}")
            
            # Get Math prediction
            math_result = await math_controller.get_prediction_by_symbol_and_date(symbol, date)
            math_pred = math_result.get('prediction', {}) if math_result.get('success') else {}
            
            # Get AI prediction
            ai_result = await ai_controller.get_prediction_by_symbol_and_date(symbol, date)
            ai_pred = ai_result.get('prediction', {}) if ai_result.get('success') else {}
            
            # Combine all predictions
            final_pred = final_prediction_service.combine_predictions(
                gmp_pred, math_pred, ai_pred, ipo_data
            )
            
            # Save prediction
            save_path = f"predictions/final_prediction/{date}"
            save_success = file_storage.save_data(save_path, final_pred, symbol)
            
            if save_success:
                logger.info(f"Saved: data/{save_path}/{symbol}.json")
                final_pred['storage_path'] = f'data/{save_path}/{symbol}.json'
            
            final_pred['success'] = True
            return final_pred
            
        except Exception as e:
            logger.error(f"Final prediction error for {symbol}: {e}", exc_info=True)
            return {
                'success': False,
                'symbol': symbol,
                'date': date,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_all_ipos(self, date: str = None) -> Dict:
        """Batch process all current IPOs using stored data"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"Starting batch processing for {date}")
            
            # Load stored current IPOs
            stored_current = file_storage.load_data("nse/current", date)
            
            if not stored_current or 'data' not in stored_current:
                return {
                    'success': False,
                    'error': f'No stored current IPO data for {date}',
                    'date': date,
                    'suggestion': 'First fetch: GET /api/ipo/current',
                    'timestamp': datetime.now().isoformat()
                }
            
            current_ipos = stored_current['data']
            logger.info(f"Loaded {len(current_ipos)} IPOs")
            
            # Check/generate predictions if needed
            gmp_stored = file_storage.load_data("predictions/gmp", date)
            if not gmp_stored:
                await gmp_controller.fetch_gmp_data()
            
            math_stored = file_storage.load_data("predictions/math", date)
            if not math_stored:
                await math_controller.predict_all_by_date(date)
            
            ai_stored = file_storage.load_data("predictions/ai", date)
            if not ai_stored:
                await ai_controller.predict_all_current_ipos(date)
            
            # Process each IPO
            results = []
            success_count = 0
            fail_count = 0
            
            for ipo in current_ipos:
                symbol = ipo.get('symbol', '')
                if not symbol:
                    continue
                
                try:
                    final_pred = await self.get_final_prediction(symbol, date)
                    
                    if final_pred.get('success'):
                        results.append({
                            'symbol': symbol,
                            'company': ipo.get('company_name'),
                            'recommendation': final_pred.get('final_recommendation'),
                            'consensus': final_pred.get('consensus_strength'),
                            'expected_gain': final_pred.get('expected_gain_percent'),
                            'listing_price': final_pred.get('expected_listing_price'),
                            'risk': final_pred.get('overall_risk_level'),
                            'confidence': final_pred.get('overall_confidence'),
                            'has_gmp': final_pred.get('has_gmp_data', False),
                            'status': 'success'
                        })
                        success_count += 1
                    else:
                        results.append({
                            'symbol': symbol,
                            'error': final_pred.get('error'),
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
            
            # Generate summary
            summary_data = self._generate_batch_summary(results, date)
            
            # Save summary
            batch_path = f"predictions/final_prediction/{date}"
            file_storage.save_data(batch_path, summary_data, "batch_summary")
            
            return {
                'success': True,
                'date': date,
                'summary': {
                    'total': len(results),
                    'success': success_count,
                    'failed': fail_count,
                    'success_rate': round((success_count / len(results)) * 100, 1) if results else 0
                },
                'results': results,
                'top_picks': summary_data.get('top_picks', []),
                'storage_path': f'data/{batch_path}/',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}", exc_info=True)
            return {
                'success': False,
                'date': date,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_batch_summary(self, results: List[Dict], date: str) -> Dict:
        """Generate intelligent batch summary with rankings"""
        strong_buys = []
        buys = []
        moderate_buys = []
        holds = []
        avoids = []
        
        for r in results:
            if r.get('status') != 'success':
                continue
            
            rec = r.get('recommendation', '')
            if rec == 'STRONG_BUY':
                strong_buys.append(r)
            elif rec == 'BUY':
                buys.append(r)
            elif rec == 'MODERATE_BUY':
                moderate_buys.append(r)
            elif rec == 'HOLD':
                holds.append(r)
            else:
                avoids.append(r)
        
        strong_buys.sort(key=lambda x: x.get('expected_gain', 0), reverse=True)
        buys.sort(key=lambda x: x.get('expected_gain', 0), reverse=True)
        
        top_picks = strong_buys[:3] + buys[:2]
        avoid_list = avoids + [h for h in holds if h.get('risk') in ['HIGH', 'MEDIUM-HIGH']]
        
        total_successful = len([r for r in results if r.get('status') == 'success'])
        bullish_count = len(strong_buys) + len(buys)
        
        if total_successful > 0:
            if bullish_count / total_successful >= 0.6:
                market_sentiment = "BULLISH"
            elif bullish_count / total_successful >= 0.4:
                market_sentiment = "NEUTRAL"
            else:
                market_sentiment = "BEARISH"
        else:
            market_sentiment = "UNKNOWN"
        
        return {
            'date': date,
            'timestamp': datetime.now().isoformat(),
            'total_ipos_analyzed': total_successful,
            'market_sentiment': market_sentiment,
            'distribution': {
                'strong_buy': len(strong_buys),
                'buy': len(buys),
                'moderate_buy': len(moderate_buys),
                'hold': len(holds),
                'avoid': len(avoids)
            },
            'top_picks': top_picks,
            'avoid_list': avoid_list,
            'all_results': results
        }
    
    async def get_stored_final_prediction(self, symbol: str, date: str = None) -> Dict:
        """Get stored final prediction for a symbol"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            load_path = f"predictions/final_prediction/{date}"
            stored_data = file_storage.load_data(load_path, symbol)
            
            if not stored_data:
                return {
                    'success': False,
                    'message': f'No final prediction found for {symbol} on {date}',
                    'symbol': symbol,
                    'date': date,
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'success': True,
                'data': stored_data.get('data'),
                'metadata': stored_data.get('metadata'),
                'symbol': symbol,
                'date': date,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error loading stored prediction for {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'date': date,
                'timestamp': datetime.now().isoformat()
            }
    
    async def get_batch_summary(self, date: str = None) -> Dict:
        """Get batch summary for a date"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            load_path = f"predictions/final_prediction/{date}"
            stored_data = file_storage.load_data(load_path, "batch_summary")
            
            if not stored_data:
                return {
                    'success': False,
                    'message': f'No batch summary found for {date}',
                    'date': date,
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'success': True,
                'data': stored_data.get('data'),
                'metadata': stored_data.get('metadata'),
                'date': date,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error loading batch summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'date': date,
                'timestamp': datetime.now().isoformat()
            }

# Create controller instance
final_controller = FinalController()