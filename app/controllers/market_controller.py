# app/controllers/ipo_controller.py
from fastapi import HTTPException
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import asyncio

# Import the session-managed scraper
from app.services.nse_scraper import NSEScraper
from app.services.data_processor import DataProcessor

logger = logging.getLogger(__name__)

class IPOController:
    """Session-aware IPO Controller"""
    
    def __init__(self):
        self.nse_scraper = NSEScraper()
        self.data_processor = DataProcessor()
    
    async def get_current_ipos(self, include_gmp: bool = False) -> Dict[str, Any]:
        """Get current active IPOs from NSE only"""
        try:
            logger.info("📈 Controller: Fetching current IPOs (NSE only)")
            
            # Fetch IPO data from NSE only
            ipo_data = self.nse_scraper.get_current_ipos()
            
            # Process and clean data
            processed_data = self.data_processor.clean_ipo_data(ipo_data)
            
            # Check if we got real NSE data
            is_real_data = any("Demo Data" not in str(item.get('status', '')) for item in processed_data)
            
            # Get session info for debugging
            session_info = self.nse_scraper.get_session_info()
            
            return {
                'success': True,
                'message': f'Successfully fetched {len(processed_data)} current IPOs from NSE',
                'count': len(processed_data),
                'data': processed_data,
                'is_real_data': is_real_data,
                'data_source': 'NSE API' if is_real_data else 'Demo Data',
                'session_info': session_info,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE API Only'
            }
            
        except Exception as e:
            logger.error(f"❌ Controller error in current IPOs: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch current IPOs: {str(e)}"
            )
    
    async def get_upcoming_ipos(self, include_gmp: bool = False) -> Dict[str, Any]:
        """Get upcoming IPOs from NSE only"""
        try:
            logger.info("🔮 Controller: Fetching upcoming IPOs (NSE only)")
            
            # Fetch IPO data from NSE only
            ipo_data = self.nse_scraper.get_upcoming_ipos()
            
            # Process and clean data
            processed_data = self.data_processor.clean_ipo_data(ipo_data)
            
            # Check if we got real NSE data
            is_real_data = any("Demo" not in str(item.get('status', '')) for item in processed_data)
            
            # Get session info
            session_info = self.nse_scraper.get_session_info()
            
            return {
                'success': True,
                'message': f'Successfully fetched {len(processed_data)} upcoming IPOs from NSE',
                'count': len(processed_data),
                'data': processed_data,
                'is_real_data': is_real_data,
                'data_source': 'NSE API' if is_real_data else 'Demo Data',
                'session_info': session_info,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE API Only'
            }
            
        except Exception as e:
            logger.error(f"❌ Controller error in upcoming IPOs: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch upcoming IPOs: {str(e)}"
            )
    
    async def get_past_ipos(self, days_back: int = 30) -> Dict[str, Any]:
        """Get past IPOs from NSE only"""
        try:
            logger.info(f"📊 Controller: Fetching past IPOs (NSE only - last {days_back} days)")
            
            # Validate input
            days_back = max(1, min(days_back, 90))
            
            # Fetch IPO data from NSE only
            ipo_data = self.nse_scraper.get_past_ipos(days_back)
            
            # Process and clean data
            processed_data = self.data_processor.clean_ipo_data(ipo_data)
            
            return {
                'success': True,
                'message': f'Successfully fetched {len(processed_data)} past IPOs from NSE',
                'count': len(processed_data),
                'data': processed_data,
                'days_back': days_back,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE API Only'
            }
            
        except Exception as e:
            logger.error(f"❌ Controller error in past IPOs: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch past IPOs: {str(e)}"
            )
    
    async def get_ipo_summary(self, include_gmp: bool = False) -> Dict[str, Any]:
        """Get comprehensive IPO summary from NSE only"""
        try:
            logger.info("📋 Controller: Generating IPO summary (NSE only)")
            
            # Fetch all data from NSE only
            current_data = self.nse_scraper.get_current_ipos()
            upcoming_data = self.nse_scraper.get_upcoming_ipos()
            past_data = self.nse_scraper.get_past_ipos(30)
            
            # Process data
            current_clean = self.data_processor.clean_ipo_data(current_data)
            upcoming_clean = self.data_processor.clean_ipo_data(upcoming_data)
            past_clean = self.data_processor.clean_ipo_data(past_data)
            
            # Create summary
            summary_data = self.data_processor.format_ipo_summary(
                current_clean, upcoming_clean, past_clean, None  # No GMP data
            )
            
            # Get session info
            session_info = self.nse_scraper.get_session_info()
            
            return {
                'success': True,
                'message': 'IPO summary generated successfully (NSE only)',
                'summary': summary_data,
                'session_info': session_info,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE API Only'
            }
            
        except Exception as e:
            logger.error(f"❌ Controller error in IPO summary: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate IPO summary: {str(e)}"
            )
    
    async def search_ipos(self, query: str, category: str = "all", include_gmp: bool = False) -> Dict[str, Any]:
        """Search IPOs by company name or symbol from NSE only"""
        try:
            logger.info(f"🔍 Controller: Searching IPOs (NSE only) - Query: '{query}', Category: '{category}'")
            
            # Validate query
            if len(query.strip()) < 2:
                raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
            
            all_ipos = []
            
            # Fetch data based on category from NSE only
            if category in ["current", "all"]:
                current_data = self.nse_scraper.get_current_ipos()
                all_ipos.extend(self.data_processor.clean_ipo_data(current_data))
            
            if category in ["upcoming", "all"]:
                upcoming_data = self.nse_scraper.get_upcoming_ipos()
                all_ipos.extend(self.data_processor.clean_ipo_data(upcoming_data))
            
            if category in ["past", "all"]:
                past_data = self.nse_scraper.get_past_ipos(60)
                all_ipos.extend(self.data_processor.clean_ipo_data(past_data))
            
            # Perform search
            query_lower = query.lower().strip()
            search_results = [
                ipo for ipo in all_ipos
                if (query_lower in ipo.get('company_name', '').lower() or
                    query_lower in ipo.get('symbol', '').lower())
            ]
            
            return {
                'success': True,
                'message': f'Found {len(search_results)} IPOs matching "{query}" (NSE only)',
                'query': query,
                'category': category,
                'count': len(search_results),
                'data': search_results,
                'timestamp': datetime.now().isoformat(),
                'source': 'NSE API Only'
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Controller error in search: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to search IPOs: {str(e)}"
            )
    
    async def test_nse_connection(self) -> Dict[str, Any]:
        """Test NSE API connectivity with session info"""
        try:
            logger.info("🧪 Controller: Testing NSE connection with session management")
            
            test_results = {}
            
            # Get current session info
            session_info = self.nse_scraper.get_session_info()
            test_results['session_info'] = session_info
            
            # Test current IPOs
            try:
                current_data = self.nse_scraper.get_current_ipos()
                is_real = any("Demo Data" not in str(item.get('status', '')) for item in current_data)
                test_results['current_ipos'] = {
                    'status': 'success' if current_data else 'empty',
                    'count': len(current_data) if current_data else 0,
                    'is_real_data': is_real
                }
            except Exception as e:
                test_results['current_ipos'] = {
                    'status': 'failed',
                    'error': str(e)
                }
            
            # Test upcoming IPOs
            try:
                upcoming_data = self.nse_scraper.get_upcoming_ipos()
                is_real = any("Demo" not in str(item.get('status', '')) for item in upcoming_data)
                test_results['upcoming_ipos'] = {
                    'status': 'success' if upcoming_data else 'empty',
                    'count': len(upcoming_data) if upcoming_data else 0,
                    'is_real_data': is_real
                }
            except Exception as e:
                test_results['upcoming_ipos'] = {
                    'status': 'failed',
                    'error': str(e)
                }
            
            # Test market indices
            try:
                indices_data = self.nse_scraper.get_market_indices()
                test_results['market_indices'] = {
                    'status': 'success' if indices_data else 'empty',
                    'count': len(indices_data) if indices_data else 0
                }
            except Exception as e:
                test_results['market_indices'] = {
                    'status': 'failed',
                    'error': str(e)
                }
            
            # Calculate success rate
            success_count = sum(1 for result in test_results.values() 
                              if isinstance(result, dict) and result.get('status') == 'success')
            total_tests = len([k for k in test_results.keys() if k != 'session_info'])
            success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
            
            return {
                'success': True,
                'message': f'NSE connection test: {success_count}/{total_tests} services working',
                'success_rate': round(success_rate, 1),
                'test_results': test_results,
                'recommendations': self._get_session_recommendations(session_info, success_rate),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Controller error in connection test: {e}")
            return {
                'success': False,
                'message': 'NSE connection test failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def refresh_nse_session(self) -> Dict[str, Any]:
        """Manually refresh NSE session"""
        try:
            logger.info("🔄 Controller: Manual NSE session refresh")
            
            success = self.nse_scraper.refresh_session()
            session_info = self.nse_scraper.get_session_info()
            
            return {
                'success': success,
                'message': 'NSE session refreshed successfully' if success else 'Failed to refresh NSE session',
                'session_info': session_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Controller error in session refresh: {e}")
            return {
                'success': False,
                'message': 'Session refresh failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_session_recommendations(self, session_info: Dict, success_rate: float) -> List[str]:
        """Get recommendations based on session status"""
        recommendations = []
        
        if not session_info.get('session_active'):
            recommendations.append("🔄 NSE session is inactive - automatic refresh will be attempted")
        
        session_age = session_info.get('session_age_seconds', 0)
        if session_age > 300:  # 5 minutes
            recommendations.append("⏰ NSE session is getting old - may need refresh soon")
        
        expires_in = session_info.get('session_expires_in_seconds', 0)
        if expires_in < 60 and expires_in > 0:
            recommendations.append("⚠️ NSE session expires in less than 1 minute")
        
        if success_rate < 50:
            recommendations.append("🔧 Low success rate - try manual session refresh")
        
        last_request = session_info.get('last_request_seconds_ago', 0)
        if last_request > 180:  # 3 minutes
            recommendations.append("🕒 No recent API calls - session may have expired")
        
        if not recommendations:
            recommendations.append("✅ NSE session is healthy and active")
        
        return recommendations
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.nse_scraper.cleanup()
            logger.info("🧹 IPO Controller cleaned up")
        except:
            pass


# Create controller instance
ipo_controller = IPOController()