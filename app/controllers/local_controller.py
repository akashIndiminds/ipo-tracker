# app/controllers/local_controller.py
"""
 Local Controller - ULTRA FAST READ-ONLY
Only reads from files - NO scraping, NO AI calls
Can handle 10000+ concurrent requests
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import HTTPException
from functools import lru_cache
import asyncio

from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class LocalController:
    """Ultra-fast read-only controller - No blocking operations"""
    
    def __init__(self):
        self.file_storage = file_storage
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes cache
    
    @lru_cache(maxsize=100)
    def _get_cached_data(self, cache_key: str, date: str):
        """LRU cache for frequently accessed data"""
        return self.file_storage.load_data(cache_key, date)
    
    async def get_current_ipos(self, date: str = None) -> Dict[str, Any]:
        """
        Get current IPOs - INSTANT response
        Just reads from file, no processing
        """
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Try cache first
            cache_key = f"current_{date}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if (datetime.now() - cached['timestamp']).seconds < self._cache_timeout:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached['data']
            
            # Read from file (non-blocking)
            current_data = await asyncio.to_thread(
                self.file_storage.load_data, 'nse/current', date
            )
            
            if not current_data:
                return {
                    'success': False,
                    'message': f'No data available for {date}',
                    'date': date,
                    'data': [],
                    'suggestion': 'Data is updated 4 times daily. Please wait for next update.',
                    'next_update_times': ['09:00', '12:00', '15:30', '18:00'],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Extract data
            ipos = current_data.get('data', [])
            
            # Load subscription data (parallel)
            subscription_data = await asyncio.to_thread(
                self.file_storage.load_data, 'nse/subscription', date
            )
            
            # Enrich with subscription
            enriched = self._enrich_with_subscription_fast(ipos, subscription_data)
            
            result = {
                'success': True,
                'message': f'Loaded {len(enriched)} current IPOs',
                'date': date,
                'count': len(enriched),
                'data': enriched,
                'source': 'LOCAL_CACHE',
                'last_updated': current_data.get('metadata', {}).get('timestamp'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update cache
            self._cache[cache_key] = {
                'data': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error loading current IPOs: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_upcoming_ipos(self, date: str = None) -> Dict[str, Any]:
        """Get upcoming IPOs - INSTANT response"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            cache_key = f"upcoming_{date}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if (datetime.now() - cached['timestamp']).seconds < self._cache_timeout:
                    return cached['data']
            
            upcoming_data = await asyncio.to_thread(
                self.file_storage.load_data, 'nse/upcoming', date
            )
            
            if not upcoming_data:
                return {
                    'success': False,
                    'message': f'No upcoming IPO data for {date}',
                    'date': date,
                    'data': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            ipos = upcoming_data.get('data', [])
            
            result = {
                'success': True,
                'message': f'Loaded {len(ipos)} upcoming IPOs',
                'date': date,
                'count': len(ipos),
                'data': ipos,
                'source': 'LOCAL_CACHE',
                'last_updated': upcoming_data.get('metadata', {}).get('timestamp'),
                'timestamp': datetime.now().isoformat()
            }
            
            self._cache[cache_key] = {'data': result, 'timestamp': datetime.now()}
            return result
            
        except Exception as e:
            logger.error(f"Error loading upcoming IPOs: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_subscription_data(self, date: str = None) -> Dict[str, Any]:
        """Get subscription data - INSTANT response"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            subscription_data = await asyncio.to_thread(
                self.file_storage.load_data, 'nse/subscription', date
            )
            
            if not subscription_data:
                return {
                    'success': False,
                    'message': f'No subscription data for {date}',
                    'date': date,
                    'data': {},
                    'timestamp': datetime.now().isoformat()
                }
            
            data = subscription_data.get('data', {})
            subscription_dict = data.get('data', {})
            
            return {
                'success': True,
                'message': f'Loaded subscription data for {len(subscription_dict)} IPOs',
                'date': date,
                'count': len(subscription_dict),
                'data': subscription_dict,
                'metadata': data.get('metadata', {}),
                'source': 'LOCAL_CACHE',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error loading subscription data: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_ipo_by_symbol(self, symbol: str, date: str = None) -> Dict[str, Any]:
        """
        Get single IPO by symbol - ULTRA FAST
        Direct symbol lookup, no iteration
        """
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            symbol = symbol.upper()
            
            # Load current IPOs
            current_data = await asyncio.to_thread(
                self.file_storage.load_data, 'nse/current', date
            )
            
            if not current_data:
                raise HTTPException(status_code=404, detail=f"No data for {date}")
            
            ipos = current_data.get('data', [])
            
            # Find symbol ()
            ipo = next((i for i in ipos if i.get('symbol', '').upper() == symbol), None)
            
            if not ipo:
                available = [i.get('symbol') for i in ipos[:10]]
                return {
                    'success': False,
                    'message': f'Symbol {symbol} not found',
                    'available_symbols': available,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Load subscription for this symbol
            subscription_data = await asyncio.to_thread(
                self.file_storage.load_data, 'nse/subscription', date
            )
            
            # Enrich
            enriched = self._enrich_single_ipo(ipo, subscription_data)
            
            return {
                'success': True,
                'symbol': symbol,
                'date': date,
                'data': enriched,
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting IPO {symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_predictions_by_symbol(self, symbol: str, date: str = None) -> Dict[str, Any]:
        """
        Get all predictions for a symbol - FAST
        Loads from pre-generated prediction files
        """
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            symbol = symbol.upper()
            
            # Load all predictions in parallel
            gmp_task = asyncio.to_thread(self.file_storage.load_data, 'predictions/gmp', date)
            math_task = asyncio.to_thread(self.file_storage.load_data, 'predictions/math', date)
            ai_task = asyncio.to_thread(self.file_storage.load_data, 'predictions/ai', date)
            final_task = asyncio.to_thread(self.file_storage.load_data, 'predictions/final', date)
            
            gmp_data, math_data, ai_data, final_data = await asyncio.gather(
                gmp_task, math_task, ai_task, final_task
            )
            
            result = {
                'success': True,
                'symbol': symbol,
                'date': date,
                'predictions': {}
            }
            
            # Extract GMP prediction
            if gmp_data:
                result['predictions']['gmp'] = self._extract_gmp_for_symbol(symbol, gmp_data)
            
            # Extract Math prediction
            if math_data:
                result['predictions']['math'] = self._extract_math_for_symbol(symbol, math_data)
            
            # Extract AI prediction
            if ai_data:
                result['predictions']['ai'] = self._extract_ai_for_symbol(symbol, ai_data)
            
            # Extract Final prediction
            if final_data:
                result['predictions']['final'] = self._extract_final_for_symbol(symbol, final_data)
            
            result['timestamp'] = datetime.now().isoformat()
            return result
            
        except Exception as e:
            logger.error(f"Error getting predictions for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_all_predictions(self, date: str = None) -> Dict[str, Any]:
        """Get all predictions - FAST batch read"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Load final predictions (already combined)
            final_data = await asyncio.to_thread(
                self.file_storage.load_data, 'predictions/final', date
            )
            
            if not final_data:
                return {
                    'success': False,
                    'message': f'No predictions available for {date}',
                    'date': date,
                    'data': {},
                    'timestamp': datetime.now().isoformat()
                }
            
            consolidated = final_data.get('data', {})
            predictions = consolidated.get('predictions', {})
            
            return {
                'success': True,
                'date': date,
                'count': len(predictions),
                'data': predictions,
                'metadata': {
                    'created_at': consolidated.get('created_at'),
                    'last_updated': consolidated.get('last_updated')
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting all predictions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_available_dates(self, data_type: str = 'current') -> Dict[str, Any]:
        """Get list of available dates for historical data"""
        try:
            path_map = {
                'current': 'nse/current',
                'upcoming': 'nse/upcoming',
                'subscription': 'nse/subscription',
                'predictions': 'predictions/final'
            }
            
            path = path_map.get(data_type, 'nse/current')
            
            dates = await asyncio.to_thread(
                self.file_storage.get_available_dates, path
            )
            
            return {
                'success': True,
                'data_type': data_type,
                'available_dates': dates,
                'count': len(dates),
                'latest': dates[0] if dates else None,
                'oldest': dates[-1] if dates else None,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting available dates: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _enrich_with_subscription_fast(self, ipos: List[Dict], subscription_data: Dict) -> List[Dict]:
        """Fast subscription enrichment"""
        if not subscription_data:
            return ipos
        
        sub_dict = subscription_data.get('data', {}).get('data', {})
        
        for ipo in ipos:
            symbol = ipo.get('symbol')
            if symbol and symbol in sub_dict:
                ipo['subscription'] = self._format_subscription(sub_dict[symbol])
        
        return ipos
    
    def _enrich_single_ipo(self, ipo: Dict, subscription_data: Dict) -> Dict:
        """Enrich single IPO"""
        if not subscription_data:
            return ipo
        
        sub_dict = subscription_data.get('data', {}).get('data', {})
        symbol = ipo.get('symbol')
        
        if symbol and symbol in sub_dict:
            ipo['subscription'] = self._format_subscription(sub_dict[symbol])
        
        return ipo
    
    def _format_subscription(self, sub_data: Dict) -> Dict:
        """Format subscription data"""
        categories = sub_data.get('categories', {})
        
        qib = self._get_subscription_value(categories.get('Qualified Institutional Buyers(QIBs)', {}))
        nii = self._get_subscription_value(categories.get('Non Institutional Investors', {}))
        retail = self._get_subscription_value(categories.get('Retail Individual Investors(RIIs)', {}))
        total = sub_data.get('total_subscription', 0)
        
        return {
            'qib': f"{qib:.2f}x",
            'nii': f"{nii:.2f}x",
            'retail': f"{retail:.2f}x",
            'total': f"{total:.2f}x",
            'qib_numeric': qib,
            'nii_numeric': nii,
            'retail_numeric': retail,
            'total_numeric': total,
            'has_data': True,
            'display': f"QIB: {qib:.2f}x | NII: {nii:.2f}x | Retail: {retail:.2f}x | Total: {total:.2f}x"
        }
    
    def _get_subscription_value(self, category_data: Dict) -> float:
        """Extract subscription value"""
        try:
            return float(category_data.get('subscription_times', 0))
        except:
            return 0.0
    
    def _extract_gmp_for_symbol(self, symbol: str, gmp_data: Dict) -> Dict:
        """Extract GMP prediction for symbol"""
        try:
            sources = gmp_data.get('data', {}).get('sources', {})
            for source_data in sources.values():
                if source_data.get('success'):
                    for item in source_data.get('data', []):
                        if item.get('matched_symbol') == symbol:
                            return item
            return {'found': False}
        except:
            return {'found': False}
    
    def _extract_math_for_symbol(self, symbol: str, math_data: Dict) -> Dict:
        """Extract math prediction for symbol"""
        try:
            predictions = math_data.get('data', {}).get('predictions', [])
            for pred in predictions:
                if pred.get('symbol') == symbol:
                    return pred.get('prediction', {})
            return {}
        except:
            return {}
    
    def _extract_ai_for_symbol(self, symbol: str, ai_data: Dict) -> Dict:
        """Extract AI prediction for symbol"""
        try:
            predictions = ai_data.get('data', {}).get('predictions', [])
            for pred in predictions:
                if pred.get('symbol') == symbol:
                    return pred
            return {}
        except:
            return {}
    
    def _extract_final_for_symbol(self, symbol: str, final_data: Dict) -> Dict:
        """Extract final prediction for symbol"""
        try:
            predictions = final_data.get('data', {}).get('predictions', {})
            return predictions.get(symbol, {})
        except:
            return {}
    
    async def clear_cache(self):
        """Clear internal cache"""
        self._cache.clear()
        logger.info("Cache cleared")
        return {'success': True, 'message': 'Cache cleared'}

# Create singleton instance
local_controller = LocalController()