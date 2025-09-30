# app/controllers/nse_controller.py
"""Enhanced NSE Controller - With Lot Size & Issue Size in existing endpoints"""

from typing import Dict, Any
import logging
from datetime import datetime
from fastapi import HTTPException

from ..services.nse_service import nse_service
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class NSEController:
    """Enhanced NSE Controller - existing endpoints with enriched data"""
    
    def __init__(self):
        self.nse_service = nse_service
        self.file_storage = file_storage
    
    async def get_current_ipos(self, save_data: bool = True) -> Dict[str, Any]:
        """
        Handle current IPOs request with automatic lot size enrichment
        Automatically fetches subscription data to calculate lot size
        """
        try:
            logger.info("Processing current IPOs request with automatic enrichment")
            
            # STEP 1: Fetch basic IPO data
            ipo_data = self.nse_service.fetch_current_ipos()
            
            if not ipo_data:
                raise HTTPException(
                    status_code=503,
                    detail="NSE data not available - service may be down or blocked"
                )
            
            # STEP 2: Fetch subscription data to calculate lot size
            logger.info("Fetching subscription data for lot size calculation...")
            symbols = [ipo.get('symbol') for ipo in ipo_data if ipo.get('symbol')]
            subscription_result = self.nse_service.fetch_all_subscriptions(symbols)
            subscription_data = subscription_result.get('data', {})
            
            # STEP 3: Enrich each IPO with lot size
            enriched_count = 0
            for ipo in ipo_data:
                symbol = ipo.get('symbol')
                if symbol and symbol in subscription_data:
                    sub_data = subscription_data[symbol]
                    
                    # Extract all shares_bid values
                    shares_bid_list = []
                    for category_data in sub_data.get('categories', {}).values():
                        bid = category_data.get('shares_bid', 0)
                        if bid > 0:
                            shares_bid_list.append(bid)
                    
                    # Calculate and add lot size
                    if shares_bid_list:
                        lot_size = self.nse_service.calculate_lot_size(shares_bid_list)
                        ipo['lot_size'] = lot_size
                        ipo['lot_size_calculated'] = True
                        enriched_count += 1
                        logger.info(f"Calculated lot size for {symbol}: {lot_size}")
            
            logger.info(f"Successfully enriched {enriched_count}/{len(ipo_data)} IPOs with lot size")
            
            # STEP 4: Save enriched data
            if save_data and ipo_data:
                saved = self.file_storage.save_data('nse/current', ipo_data)
                logger.info(f"Enriched current IPOs data saved to file: {saved}")
            
            return {
                'success': True,
                'message': f'Successfully fetched {len(ipo_data)} current IPOs ({enriched_count} with lot size)',
                'count': len(ipo_data),
                'enriched_count': enriched_count,
                'data': ipo_data,
                'saved_to_file': save_data and ipo_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE_API',
                'features': [
                    'Issue size in crores calculated',
                    f'Lot size calculated for {enriched_count} IPOs',
                    'Price range extracted (min/max)'
                ]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - current IPOs: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch current IPOs: {str(e)}"
            )
    
    async def get_upcoming_ipos(self, save_data: bool = True) -> Dict[str, Any]:
        """Handle upcoming IPOs request with issue size calculation"""
        try:
            logger.info("Processing upcoming IPOs request")
            
            # Fetch upcoming IPOs (with issue size calculated)
            ipo_data = self.nse_service.fetch_upcoming_ipos()
            
            if not ipo_data:
                raise HTTPException(
                    status_code=503,
                    detail="NSE data not available - service may be down or blocked"
                )
            
            # Save data to file
            if save_data and ipo_data:
                saved = self.file_storage.save_data('nse/upcoming', ipo_data)
                logger.info(f"Upcoming IPOs data saved to file: {saved}")
            
            return {
                'success': True,
                'message': f'Successfully fetched {len(ipo_data)} upcoming IPOs',
                'count': len(ipo_data),
                'data': ipo_data,
                'saved_to_file': save_data and ipo_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE_API',
                'note': 'Lot size not available for upcoming IPOs (no subscription data yet)'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - upcoming IPOs: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch upcoming IPOs: {str(e)}"
            )
    
    async def get_all_subscriptions(self, save_data: bool = True) -> Dict[str, Any]:
        """
        Handle subscription data request for all current IPOs
        Now includes lot size calculation for each IPO
        """
        try:
            logger.info("Processing subscription data request with lot size calculation")
            
            # Get subscription data
            subscription_result = self.nse_service.fetch_all_subscriptions()
            
            if not subscription_result or not subscription_result.get('data'):
                raise HTTPException(
                    status_code=503,
                    detail="NSE subscription data not available"
                )
            
            # Calculate lot size for each IPO in subscription data
            subscription_data = subscription_result['data']
            
            for symbol, data in subscription_data.items():
                categories = data.get('categories', {})
                shares_bid_list = [
                    cat_data.get('shares_bid', 0) 
                    for cat_data in categories.values() 
                    if cat_data.get('shares_bid', 0) > 0
                ]
                
                # Calculate and add lot size
                lot_size = self.nse_service.calculate_lot_size(shares_bid_list)
                data['lot_size'] = lot_size
                data['lot_size_source'] = 'calculated_from_bids'
            
            # Save enriched subscription data
            if save_data and subscription_result:
                saved = self.file_storage.save_data('nse/subscription', subscription_result)
                logger.info(f"Subscription data with lot size saved to file: {saved}")
            
            metadata = subscription_result['metadata']
            
            return {
                'success': True,
                'message': f'Successfully fetched subscription data with lot size for {metadata["successful_symbols"]} IPOs',
                'count': metadata['successful_symbols'],
                'total_symbols': metadata['total_symbols'],
                'success_rate': f"{metadata['success_rate']}%",
                'failed_symbols': metadata['failed_symbols'],
                'data': subscription_data,
                'metadata': metadata,
                'saved_to_file': save_data and subscription_result,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE_API',
                'features': [
                    'Lot size calculated using GCD algorithm',
                    'Category-wise subscription details',
                    'Real-time subscription times'
                ]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - subscription data: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch subscription data: {str(e)}"
            )
    
    async def test_nse_connection(self) -> Dict[str, Any]:
        """Handle NSE connection test request"""
        try:
            logger.info("Processing connection test request")
            
            test_results = self.nse_service.test_connection()
            recommendations = self._get_test_recommendations(test_results)
            
            return {
                'success': test_results['overall_status'] not in ['failed'],
                'message': f'NSE connection test: {test_results["overall_status"]}',
                'test_results': test_results,
                'recommendations': recommendations,
                'session_info': self.nse_service.get_session_info(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Controller error - connection test: {e}")
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}',
                'error': 'TEST_FAILED',
                'timestamp': datetime.now().isoformat()
            }
    
    async def refresh_session(self) -> Dict[str, Any]:
        """Handle session refresh request"""
        try:
            logger.info("Processing session refresh request")
            
            success = self.nse_service.force_refresh()
            
            return {
                'success': success,
                'message': 'NSE session refreshed successfully' if success else 'Failed to refresh NSE session',
                'session_info': self.nse_service.get_session_info(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Controller error - session refresh: {e}")
            return {
                'success': False,
                'message': f'Session refresh failed: {str(e)}',
                'error': 'REFRESH_FAILED',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_test_recommendations(self, test_results: dict) -> list:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if test_results['overall_status'] == 'excellent':
            recommendations.append("NSE connection is excellent - all endpoints working")
        elif test_results['overall_status'] == 'partial':
            recommendations.append("NSE connection is partial - some endpoints working")
            recommendations.append("Try refreshing session or wait a few minutes")
        else:
            recommendations.append("NSE connection failed completely")
            recommendations.append("Check internet connectivity")
            recommendations.append("NSE servers may be down or blocking requests")
            recommendations.append("Try refreshing session")
        
        return recommendations

# Create controller instance
nse_controller = NSEController()