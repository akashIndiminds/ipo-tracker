# app/controllers/ipo_controller.py
from typing import Dict, Any
import logging
from datetime import datetime
from fastapi import HTTPException

# Fixed imports - use relative imports within app
from ..services.nse_service import nse_service

logger = logging.getLogger(__name__)

class IPOController:
    """IPO Controller - Handles HTTP requests and responses only"""
    
    def __init__(self):
        self.nse_service = nse_service
    
    async def get_current_ipos(self, include_gmp: bool = False) -> Dict[str, Any]:
        """Handle current IPOs request"""
        try:
            logger.info("📈 Controller: Processing current IPOs request")
            
            # Get data from service
            ipo_data = self.nse_service.fetch_current_ipos()
            
            # Check if data available
            if not ipo_data:
                raise HTTPException(
                    status_code=503,
                    detail="NSE data not available - service may be down or blocked"
                )
            
            # Return response
            return {
                'success': True,
                'message': f'Successfully fetched {len(ipo_data)} current IPOs',
                'count': len(ipo_data),
                'data': ipo_data,
                'include_gmp': include_gmp,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE API'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Controller error - current IPOs: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch current IPOs: {str(e)}"
            )
    
    async def get_upcoming_ipos(self, include_gmp: bool = False) -> Dict[str, Any]:
        """Handle upcoming IPOs request"""
        try:
            logger.info("🔮 Controller: Processing upcoming IPOs request")
            
            # Get data from service
            ipo_data = self.nse_service.fetch_upcoming_ipos()
            
            # Check if data available
            if not ipo_data:
                raise HTTPException(
                    status_code=503,
                    detail="NSE data not available - service may be down or blocked"
                )
            
            # Return response
            return {
                'success': True,
                'message': f'Successfully fetched {len(ipo_data)} upcoming IPOs',
                'count': len(ipo_data),
                'data': ipo_data,
                'include_gmp': include_gmp,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE API'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Controller error - upcoming IPOs: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch upcoming IPOs: {str(e)}"
            )
    
    async def get_market_status(self) -> Dict[str, Any]:
        """Handle market status request"""
        try:
            logger.info("📊 Controller: Processing market status request")
            
            # Get data from service
            market_data = self.nse_service.fetch_market_status()
            
            # Check if data available
            if not market_data:
                raise HTTPException(
                    status_code=503,
                    detail="NSE market data not available"
                )
            
            # Return response
            return {
                'success': True,
                'message': f'Successfully fetched market status',
                'count': len(market_data),
                'data': market_data,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE API'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Controller error - market status: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch market status: {str(e)}"
            )
    
    async def test_nse_connection(self) -> Dict[str, Any]:
        """Handle NSE connection test request"""
        try:
            logger.info("🧪 Controller: Processing connection test request")
            
            # Test connection via service
            test_results = self.nse_service.test_connection()
            
            # Generate recommendations
            recommendations = self._get_test_recommendations(test_results)
            
            return {
                'success': test_results['overall_status'] != 'failed',
                'message': f'NSE connection test: {test_results["overall_status"]}',
                'test_results': test_results,
                'recommendations': recommendations,
                'session_info': self.nse_service.get_session_info(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Controller error - connection test: {e}")
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}',
                'error': 'TEST_FAILED',
                'timestamp': datetime.now().isoformat()
            }
    
    async def refresh_session(self) -> Dict[str, Any]:
        """Handle session refresh request"""
        try:
            logger.info("🔄 Controller: Processing session refresh request")
            
            # Force refresh session
            success = self.nse_service.force_refresh()
            
            return {
                'success': success,
                'message': 'NSE session refreshed and cache cleared' if success else 'Failed to refresh NSE session',
                'session_info': self.nse_service.get_session_info(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Controller error - session refresh: {e}")
            return {
                'success': False,
                'message': f'Session refresh failed: {str(e)}',
                'error': 'REFRESH_FAILED',
                'timestamp': datetime.now().isoformat()
            }

    async def clear_cache(self) -> Dict[str, Any]:
        """Handle cache clear request"""
        try:
            logger.info("🗑️ Controller: Clearing cache")
            
            self.nse_service.clear_cache()
            
            return {
                'success': True,
                'message': 'Cache cleared successfully',
                'session_info': self.nse_service.get_session_info(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Controller error - cache clear: {e}")
            return {
                'success': False,
                'message': f'Cache clear failed: {str(e)}',
                'error': 'CACHE_CLEAR_FAILED',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_test_recommendations(self, test_results: dict) -> list:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if test_results['overall_status'] == 'working':
            recommendations.append("✅ NSE connection is working properly")
        elif test_results['overall_status'] == 'partial':
            recommendations.append("⚠️ NSE connection is partial - some endpoints blocked")
            recommendations.append("🔄 Try refreshing session or wait a few minutes")
        else:
            recommendations.append("❌ NSE connection failed completely")
            recommendations.append("🔧 Check internet connectivity")
            recommendations.append("🕕 NSE servers may be down")
            recommendations.append("⏰ Try again after some time")
            recommendations.append("🛡️ NSE may be blocking requests")
        
        return recommendations

# Create controller instance
ipo_controller = IPOController()