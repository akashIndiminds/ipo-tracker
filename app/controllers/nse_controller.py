# app/controllers/nse_controller.py
"""IPO Controller - Handles NSE live data requests with file storage"""

from typing import Dict, Any
import logging
from datetime import datetime
from fastapi import HTTPException

from ..services.nse_service import nse_service
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class NSEController:
    """NSE Controller - Handles HTTP requests and responses with data storage"""
    
    def __init__(self):
        self.nse_service = nse_service
        self.file_storage = file_storage
    
    async def get_current_ipos(self, include_gmp: bool = False, save_data: bool = True) -> Dict[str, Any]:
        """Handle current IPOs request and save to file"""
        try:
            logger.info("Processing current IPOs request")
            
            # Get data from NSE service
            ipo_data = self.nse_service.fetch_current_ipos()
            
            # Check if data available
            if not ipo_data:
                raise HTTPException(
                    status_code=503,
                    detail="NSE data not available - service may be down or blocked"
                )
            
            # Save data to file if requested - Fixed path
            if save_data and ipo_data:
                saved = self.file_storage.save_data('nse/current', ipo_data)
                logger.info(f"Data saved to file: {saved}")
            
            # Return response
            return {
                'success': True,
                'message': f'Successfully fetched {len(ipo_data)} current IPOs',
                'count': len(ipo_data),
                'data': ipo_data,
                'include_gmp': include_gmp,
                'saved_to_file': save_data and ipo_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE_API'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - current IPOs: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch current IPOs: {str(e)}"
            )
    
    async def get_upcoming_ipos(self, include_gmp: bool = False, save_data: bool = True) -> Dict[str, Any]:
        """Handle upcoming IPOs request and save to file"""
        try:
            logger.info("Processing upcoming IPOs request")
            
            # Get data from NSE service
            ipo_data = self.nse_service.fetch_upcoming_ipos()
            
            # Check if data available
            if not ipo_data:
                raise HTTPException(
                    status_code=503,
                    detail="NSE data not available - service may be down or blocked"
                )
            
            # Save data to file if requested - Fixed path
            if save_data and ipo_data:
                saved = self.file_storage.save_data('nse/upcoming', ipo_data)
                logger.info(f"Data saved to file: {saved}")
            
            # Return response
            return {
                'success': True,
                'message': f'Successfully fetched {len(ipo_data)} upcoming IPOs',
                'count': len(ipo_data),
                'data': ipo_data,
                'include_gmp': include_gmp,
                'saved_to_file': save_data and ipo_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE_API'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - upcoming IPOs: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch upcoming IPOs: {str(e)}"
            )
    
    async def get_market_status(self, save_data: bool = True) -> Dict[str, Any]:
        """Handle market status request and save to file"""
        try:
            logger.info("Processing market status request")
            
            # Get data from NSE service
            market_data = self.nse_service.fetch_market_status()
            
            # Check if data available
            if not market_data:
                raise HTTPException(
                    status_code=503,
                    detail="NSE market data not available"
                )
            
            # Save data to file if requested - Fixed path
            if save_data and market_data:
                saved = self.file_storage.save_data('nse/market_status', market_data)
                logger.info(f"Data saved to file: {saved}")
            
            # Return response
            return {
                'success': True,
                'message': f'Successfully fetched market status',
                'count': len(market_data),
                'data': market_data,
                'saved_to_file': save_data and market_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE_API'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - market status: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch market status: {str(e)}"
            )
    
    async def get_ipo_active_category(self, symbol: str, save_data: bool = True) -> Dict[str, Any]:
        """Handle IPO active category request and save to file"""
        try:
            logger.info(f"Processing active category request for symbol: {symbol}")
            
            # Get data from NSE service
            category_data = self.nse_service.fetch_ipo_active_category(symbol)
            
            # Check if data available
            if not category_data:
                raise HTTPException(
                    status_code=503,
                    detail=f"NSE active category data not available for symbol: {symbol}"
                )
            
            # Save data to file if requested - Fixed path and structure
            if save_data and category_data:
                # Load existing subscription data
                existing_data = self.file_storage.load_data('nse/subscription')
                if existing_data and 'data' in existing_data:
                    # Update existing data
                    existing_data['data'][symbol] = category_data
                    existing_data['metadata']['timestamp'] = datetime.now().isoformat()
                else:
                    # Create new structure
                    existing_data = {symbol: category_data}
                
                # Save updated data
                saved = self.file_storage.save_data('nse/subscription', existing_data)
                logger.info(f"Data saved to file: {saved}")
            
            # Return response
            return {
                'success': True,
                'message': f'Successfully fetched active category for {symbol}',
                'symbol': symbol,
                'data': category_data,
                'saved_to_file': save_data and category_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE_API'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - active category for {symbol}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch active category for {symbol}: {str(e)}"
            )
    
    async def test_nse_connection(self) -> Dict[str, Any]:
        """Handle NSE connection test request"""
        try:
            logger.info("Processing connection test request")
            
            # Test connection via service
            test_results = self.nse_service.test_connection()
            
            # Generate recommendations
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
            
            # Force refresh session
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
    
    async def fetch_and_save_all_data(self) -> Dict[str, Any]:
        """Fetch all NSE data and save to files"""
        try:
            logger.info("Fetching and saving all NSE data")
            
            results = {
                'current_ipos': {'success': False, 'count': 0, 'saved': False},
                'upcoming_ipos': {'success': False, 'count': 0, 'saved': False},
                'market_status': {'success': False, 'count': 0, 'saved': False}
            }
            
            # Fetch current IPOs
            try:
                current_data = self.nse_service.fetch_current_ipos()
                if current_data:
                    results['current_ipos']['success'] = True
                    results['current_ipos']['count'] = len(current_data)
                    results['current_ipos']['saved'] = self.file_storage.save_data('nse/current', current_data)
            except Exception as e:
                logger.error(f"Failed to fetch current IPOs: {e}")
            
            # Fetch upcoming IPOs
            try:
                upcoming_data = self.nse_service.fetch_upcoming_ipos()
                if upcoming_data:
                    results['upcoming_ipos']['success'] = True
                    results['upcoming_ipos']['count'] = len(upcoming_data)
                    results['upcoming_ipos']['saved'] = self.file_storage.save_data('nse/upcoming', upcoming_data)
            except Exception as e:
                logger.error(f"Failed to fetch upcoming IPOs: {e}")
            
            # Fetch market status
            try:
                market_data = self.nse_service.fetch_market_status()
                if market_data:
                    results['market_status']['success'] = True
                    results['market_status']['count'] = len(market_data)
                    results['market_status']['saved'] = self.file_storage.save_data('nse/market_status', market_data)
            except Exception as e:
                logger.error(f"Failed to fetch market status: {e}")
            
            # Calculate success rate
            total_attempts = 3
            successful_fetches = sum(1 for r in results.values() if r['success'])
            successful_saves = sum(1 for r in results.values() if r['saved'])
            
            return {
                'success': successful_fetches > 0,
                'message': f'Batch operation completed: {successful_fetches}/{total_attempts} endpoints successful',
                'results': results,
                'summary': {
                    'total_endpoints': total_attempts,
                    'successful_fetches': successful_fetches,
                    'successful_saves': successful_saves,
                    'fetch_success_rate': round((successful_fetches / total_attempts) * 100, 1),
                    'save_success_rate': round((successful_saves / total_attempts) * 100, 1)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Controller error - batch fetch: {e}")
            return {
                'success': False,
                'message': f'Batch operation failed: {str(e)}',
                'error': 'BATCH_FETCH_FAILED',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_test_recommendations(self, test_results: dict) -> list:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if test_results['overall_status'] == 'excellent':
            recommendations.append("NSE connection is excellent - all endpoints working")
        elif test_results['overall_status'] == 'good':
            recommendations.append("NSE connection is good - most endpoints working")
        elif test_results['overall_status'] == 'partial':
            recommendations.append("NSE connection is partial - some endpoints blocked")
            recommendations.append("Try refreshing session or wait a few minutes")
        else:
            recommendations.append("NSE connection failed completely")
            recommendations.append("Check internet connectivity")
            recommendations.append("NSE servers may be down")
            recommendations.append("Try again after some time")
            recommendations.append("NSE may be blocking requests")
        
        return recommendations

# Create controller instance
nse_controller = NSEController()