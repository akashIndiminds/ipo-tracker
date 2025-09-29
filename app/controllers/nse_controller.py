# app/controllers/nse_controller.py
"""NSE Controller - Handles NSE live data requests with file storage"""

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
    
    async def get_current_ipos(self, save_data: bool = True) -> Dict[str, Any]:
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
            
            # Save data to file if requested
            if save_data and ipo_data:
                saved = self.file_storage.save_data('nse/current', ipo_data)
                logger.info(f"Current IPOs data saved to file: {saved}")
            
            # Return response
            return {
                'success': True,
                'message': f'Successfully fetched {len(ipo_data)} current IPOs',
                'count': len(ipo_data),
                'data': ipo_data,
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
    
    async def get_upcoming_ipos(self, save_data: bool = True) -> Dict[str, Any]:
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
            
            # Save data to file if requested
            if save_data and ipo_data:
                saved = self.file_storage.save_data('nse/upcoming', ipo_data)
                logger.info(f"Upcoming IPOs data saved to file: {saved}")
            
            # Return response
            return {
                'success': True,
                'message': f'Successfully fetched {len(ipo_data)} upcoming IPOs',
                'count': len(ipo_data),
                'data': ipo_data,
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
    
    async def get_all_subscriptions(self, save_data: bool = True) -> Dict[str, Any]:
        """Handle subscription data request for all current IPOs and save to file"""
        try:
            logger.info("Processing subscription data request for all current IPOs")
            
            # Get subscription data for all current IPOs
            subscription_result = self.nse_service.fetch_all_subscriptions()
            
            # Check if data available
            if not subscription_result or not subscription_result.get('data'):
                raise HTTPException(
                    status_code=503,
                    detail="NSE subscription data not available - no current IPOs found or service blocked"
                )
            
            # Save data to file if requested - SIMPLE OVERWRITE
            if save_data and subscription_result:
                saved = self.file_storage.save_data('nse/subscription', subscription_result)
                logger.info(f"Subscription data saved to file: {saved}")
            
            # Return response
            subscription_data = subscription_result['data']
            metadata = subscription_result['metadata']
            
            return {
                'success': True,
                'message': f'Successfully fetched subscription data for {metadata["successful_symbols"]} IPOs',
                'count': metadata['successful_symbols'],
                'total_symbols': metadata['total_symbols'],
                'success_rate': f"{metadata['success_rate']}%",
                'failed_symbols': metadata['failed_symbols'],
                'data': subscription_data,
                'metadata': metadata,
                'saved_to_file': save_data and subscription_result,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE_API'
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