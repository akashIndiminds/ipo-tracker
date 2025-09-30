# app/controllers/final_controller.py - CONSOLIDATED PREDICTIONS

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
    """Final Prediction Controller - CONSOLIDATED storage in single JSON per date"""
    
    async def get_final_prediction(self, symbol: str, date: str = None) -> Dict:
        """Generate intelligent final prediction for a single IPO"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"🎯 Starting final prediction for {symbol} on {date}")
            
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
            
            # Get predictions from all sources
            gmp_result = await gmp_controller.get_symbol_prediction(symbol, date)
            
            # Extract GMP data properly
            if gmp_result.get('success') and gmp_result.get('data'):
                ipo_gmp_data = gmp_result['data']
                
                if 'gmp_data' in ipo_gmp_data:
                    gmp_pred = ipo_gmp_data['gmp_data']
                    
                    if gmp_pred.get('found'):
                        gmp_pred['has_data'] = True
                        
                        if 'expected_gain_percent' not in gmp_pred:
                            if 'listing_gain' in gmp_pred and gmp_pred['listing_gain'] is not None:
                                gmp_pred['expected_gain_percent'] = gmp_pred['listing_gain']
                            else:
                                gmp_pred['expected_gain_percent'] = 0
                        
                        logger.info(f"✅ GMP data found for {symbol}: gain={gmp_pred.get('expected_gain_percent', 0)}%")
                    else:
                        gmp_pred['has_data'] = False
                        gmp_pred['expected_gain_percent'] = 0
                else:
                    gmp_pred = {'has_data': False, 'found': False, 'expected_gain_percent': 0}
            else:
                gmp_pred = {'has_data': False, 'found': False, 'expected_gain_percent': 0}
            
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
            
            # FIXED: Save to consolidated file (all symbols in one date file)
            success = self._save_to_consolidated_file(symbol, final_pred, date)
            
            if success:
                logger.info(f"✅ Saved {symbol} to consolidated file: data/predictions/final/{date}.json")
                final_pred['storage_info'] = {
                    'consolidated_file': f'data/predictions/final/{date}.json',
                    'symbol': symbol
                }
            
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
    
    def _save_to_consolidated_file(self, symbol: str, prediction: Dict, date: str) -> bool:
        """
        Save prediction to consolidated file
        Format: data/predictions/final/{date}.json
        Structure: {
            "metadata": {...},
            "predictions": {
                "SYMBOL1": {...},
                "SYMBOL2": {...}
            }
        }
        """
        try:
            # Load existing consolidated file
            existing_data = file_storage.load_data("predictions/final", date)
            
            if existing_data and 'data' in existing_data:
                consolidated = existing_data['data']
            else:
                # Create new consolidated structure
                consolidated = {
                    'date': date,
                    'created_at': datetime.now().isoformat(),
                    'predictions': {}
                }
            
            # Add/update this symbol's prediction
            if 'predictions' not in consolidated:
                consolidated['predictions'] = {}
            
            consolidated['predictions'][symbol.upper()] = prediction
            consolidated['last_updated'] = datetime.now().isoformat()
            consolidated['total_predictions'] = len(consolidated['predictions'])
            
            # Save back
            return file_storage.save_data("predictions/final", consolidated, date)
            
        except Exception as e:
            logger.error(f"Error saving to consolidated file: {e}")
            return False
    
    async def process_all_ipos(self, date: str = None) -> Dict:
        """Batch process all current IPOs - saves to SINGLE consolidated file"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"🚀 Starting batch processing for {date}")
            
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
            logger.info(f"📊 Processing {len(current_ipos)} IPOs")
            
            # Check/generate predictions if needed
            gmp_stored = file_storage.load_data("predictions/gmp", date)
            if not gmp_stored:
                logger.info("⏳ Generating GMP predictions...")
                await gmp_controller.fetch_gmp_data()
            
            math_stored = file_storage.load_data("predictions/math", date)
            if not math_stored:
                logger.info("⏳ Generating Math predictions...")
                await math_controller.predict_all_by_date(date)
            
            ai_stored = file_storage.load_data("predictions/ai", date)
            if not ai_stored:
                logger.info("⏳ Generating AI predictions...")
                await ai_controller.predict_all_current_ipos(date)
            
            # Process each IPO and save to consolidated file
            results = []
            success_count = 0
            fail_count = 0
            
            for ipo in current_ipos:
                symbol = ipo.get('symbol', '')
                if not symbol:
                    continue
                
                try:
                    logger.info(f"🔄 Processing {symbol}...")
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
                    logger.error(f"❌ Error processing {symbol}: {e}")
                    results.append({
                        'symbol': symbol,
                        'error': str(e),
                        'status': 'failed'
                    })
                    fail_count += 1
            
            # Generate and save batch summary
            summary_data = self._generate_batch_summary(results, date)
            self._save_batch_summary(summary_data, date)
            
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
                'storage_info': {
                    'consolidated_file': f'data/predictions/final/{date}.json',
                    'summary_file': f'data/predictions/final/{date}_summary.json'
                },
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
    
    def _save_batch_summary(self, summary_data: Dict, date: str) -> bool:
        """Save batch summary separately for quick access"""
        try:
            return file_storage.save_data("predictions/final", summary_data, f"{date}_summary")
        except Exception as e:
            logger.error(f"Error saving batch summary: {e}")
            return False
    
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
        """Get stored final prediction for a symbol from consolidated file"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # Load consolidated file
            stored_data = file_storage.load_data("predictions/final", date)
            
            if not stored_data or 'data' not in stored_data:
                return {
                    'success': False,
                    'message': f'No predictions found for {date}',
                    'symbol': symbol,
                    'date': date,
                    'suggestion': f'Generate predictions first: POST /api/predict/batch?date={date}',
                    'timestamp': datetime.now().isoformat()
                }
            
            consolidated = stored_data['data']
            predictions = consolidated.get('predictions', {})
            
            symbol_upper = symbol.upper()
            if symbol_upper in predictions:
                return {
                    'success': True,
                    'data': predictions[symbol_upper],
                    'symbol': symbol_upper,
                    'date': date,
                    'source': 'consolidated_file',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                available_symbols = list(predictions.keys())
                return {
                    'success': False,
                    'message': f'Symbol {symbol_upper} not found in predictions for {date}',
                    'symbol': symbol_upper,
                    'date': date,
                    'available_symbols': available_symbols,
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
            
            # Try to load summary file
            stored_data = file_storage.load_data("predictions/final", f"{date}_summary")
            
            if stored_data and 'data' in stored_data:
                return {
                    'success': True,
                    'data': stored_data['data'],
                    'date': date,
                    'source': 'summary_file',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Fallback: Generate summary from consolidated file
            consolidated_data = file_storage.load_data("predictions/final", date)
            
            if consolidated_data and 'data' in consolidated_data:
                predictions = consolidated_data['data'].get('predictions', {})
                
                results = []
                for symbol, pred in predictions.items():
                    results.append({
                        'symbol': symbol,
                        'recommendation': pred.get('final_recommendation'),
                        'expected_gain': pred.get('expected_gain_percent'),
                        'risk': pred.get('overall_risk_level'),
                        'status': 'success'
                    })
                
                summary = self._generate_batch_summary(results, date)
                
                return {
                    'success': True,
                    'data': summary,
                    'date': date,
                    'source': 'generated_from_consolidated',
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'success': False,
                'message': f'No predictions found for {date}',
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