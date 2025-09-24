# app/services/nse_service.py
"""NSE Service - Business Logic for IPO Data Processing"""

import logging
from typing import Dict, List, Optional, Any
from .nse_scraper import nse_scraper

logger = logging.getLogger(__name__)

class NSEService:
    """NSE Service - Handles business logic for IPO data"""
    
    def __init__(self):
        self.scraper = nse_scraper
    
    def fetch_current_ipos(self) -> List[Dict]:
        """Fetch and process current IPOs"""
        logger.info("Fetching current IPOs...")
        
        raw_data = self.scraper.make_api_call('/ipo-current-issue')
        
        if raw_data:
            if isinstance(raw_data, list):
                return self._process_ipo_data(raw_data)
            elif isinstance(raw_data, dict):
                return self._process_ipo_data([raw_data])
        
        logger.warning("No current IPO data received")
        return []
    
    def fetch_upcoming_ipos(self) -> List[Dict]:
        """Fetch and process upcoming IPOs"""
        logger.info("Fetching upcoming IPOs...")
        
        raw_data = self.scraper.make_api_call('/all-upcoming-issues', {'category': 'ipo'})
        
        if raw_data:
            if isinstance(raw_data, list):
                return self._process_ipo_data(raw_data)
            elif isinstance(raw_data, dict):
                return self._process_ipo_data([raw_data])
        
        logger.warning("No upcoming IPO data received")
        return []
    
    def fetch_market_status(self) -> List[Dict]:
        """Fetch and process market status"""
        logger.info("Fetching market status...")
        
        raw_data = self.scraper.make_api_call('/marketStatus')
        
        if raw_data:
            if isinstance(raw_data, list):
                return self._process_market_data(raw_data)
            elif isinstance(raw_data, dict):
                return self._process_market_data([raw_data])
        
        logger.warning("No market status data received")
        return []
    
    def fetch_ipo_active_category(self, symbol: str) -> Dict:
        """Fetch IPO active category data for specific symbol"""
        logger.info(f"Fetching active category for symbol: {symbol}")
        
        raw_data = self.scraper.make_api_call('/ipo-active-category', {'symbol': symbol})
        
        if raw_data:
            return self._process_active_category_data(raw_data, symbol)
        
        logger.warning(f"No active category data for symbol: {symbol}")
        return {}
    
    def _process_ipo_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Process raw IPO data into standardized format"""
        processed = []
        
        for item in raw_data:
            try:
                processed_item = {
                    'symbol': str(item.get('symbol', '')).strip(),
                    'company_name': str(item.get('companyName', '')).strip(),
                    'series': str(item.get('series', 'EQ')).strip(),
                    'issue_start_date': str(item.get('issueStartDate', '')).strip(),
                    'issue_end_date': str(item.get('issueEndDate', '')).strip(),
                    'issue_price': str(item.get('issuePrice', '')).strip(),
                    'issue_size': str(item.get('issueSize', '0')).strip(),
                    'status': str(item.get('status', 'Unknown')).strip(),
                    'subscription_times': self._safe_float(item.get('noOfTime', 0)),
                    'shares_offered': self._safe_int(item.get('noOfSharesOffered', 0)),
                    'shares_bid': self._safe_int(item.get('noOfsharesBid', 0)),
                    'is_sme': bool(item.get('isBse', '0') == '1'),
                    'category': str(item.get('category', 'Total')).strip(),
                    'lot_size': self._safe_int(item.get('lotSize', 0)),
                    'face_value': str(item.get('faceValue', '')).strip(),
                    'raw_data': item  # Store original data
                }
                
                if processed_item['symbol'] and processed_item['company_name']:
                    processed.append(processed_item)
                    
            except Exception as e:
                logger.warning(f"IPO processing error: {e}")
                continue
        
        logger.info(f"Processed {len(processed)} IPO records")
        return processed
    
    def _process_market_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Process raw market status data"""
        processed = []
        
        for item in raw_data:
            try:
                processed_item = {
                    'market': str(item.get('market', '')).strip(),
                    'market_status': str(item.get('marketStatus', '')).strip(),
                    'trade_date': str(item.get('tradeDate', '')).strip(),
                    'index': str(item.get('index', '')).strip(),
                    'raw_data': item
                }
                
                if processed_item['market']:
                    processed.append(processed_item)
                    
            except Exception as e:
                logger.warning(f"Market data processing error: {e}")
                continue
        
        logger.info(f"Processed {len(processed)} market records")
        return processed
    
    def _process_active_category_data(self, raw_data: Dict, symbol: str) -> Dict:
        """Process IPO active category data with bid information"""
        try:
            processed = {
                'symbol': symbol,
                'company_name': str(raw_data.get('companyName', '')).strip(),
                'issue_price': str(raw_data.get('issuePrice', '')).strip(),
                'issue_size': str(raw_data.get('issueSize', '')).strip(),
                'status': str(raw_data.get('status', 'Unknown')).strip(),
                'total_subscription': self._safe_float(raw_data.get('totalSubscription', 0)),
                'categories': {},
                'raw_data': raw_data
            }
            
            # Process category-wise subscription data
            categories = raw_data.get('categories', [])
            if isinstance(categories, list):
                for category in categories:
                    cat_name = str(category.get('category', '')).strip()
                    if cat_name:
                        processed['categories'][cat_name] = {
                            'subscription_times': self._safe_float(category.get('subscriptionTimes', 0)),
                            'shares_offered': self._safe_int(category.get('sharesOffered', 0)),
                            'shares_bid': self._safe_int(category.get('sharesBid', 0)),
                            'applications': self._safe_int(category.get('applications', 0)),
                            'amount': str(category.get('amount', '')).strip()
                        }
            
            logger.info(f"Processed active category data for {symbol}")
            return processed
            
        except Exception as e:
            logger.error(f"Active category processing error for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'raw_data': raw_data
            }
    
    def _safe_int(self, value) -> int:
        """Safely convert value to integer"""
        try:
            if isinstance(value, str):
                # Handle scientific notation
                if 'E' in value.upper() or 'e' in value:
                    return int(float(value))
                # Remove commas and convert
                return int(float(value.replace(',', '')))
            return int(float(value)) if value else 0
        except:
            return 0
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if isinstance(value, str):
                return float(value.replace(',', ''))
            return float(value) if value else 0.0
        except:
            return 0.0
    
    def test_connection(self) -> Dict[str, Any]:
        """Test NSE connection and all endpoints"""
        logger.info("Testing NSE connection...")
        
        results = {
            'session_creation': False,
            'current_ipos': False,
            'upcoming_ipos': False,
            'market_status': False,
            'overall_status': 'failed',
            'working_endpoints': [],
            'failed_endpoints': []
        }
        
        # Test session
        if self.scraper.force_refresh():
            results['session_creation'] = True
            results['working_endpoints'].append('session_init')
        else:
            results['failed_endpoints'].append('session_init')
        
        # Test endpoints if session is working
        if results['session_creation'] and not self.scraper._is_blocked():
            
            # Test current IPOs
            try:
                current_data = self.fetch_current_ipos()
                if current_data:
                    results['current_ipos'] = True
                    results['working_endpoints'].append('current_ipos')
                else:
                    results['failed_endpoints'].append('current_ipos')
            except Exception as e:
                logger.error(f"Current IPOs test failed: {e}")
                results['failed_endpoints'].append('current_ipos')
            
            # Test upcoming IPOs
            try:
                upcoming_data = self.fetch_upcoming_ipos()
                if upcoming_data:
                    results['upcoming_ipos'] = True
                    results['working_endpoints'].append('upcoming_ipos')
                else:
                    results['failed_endpoints'].append('upcoming_ipos')
            except Exception as e:
                logger.error(f"Upcoming IPOs test failed: {e}")
                results['failed_endpoints'].append('upcoming_ipos')
            
            # Test market status
            try:
                market_data = self.fetch_market_status()
                if market_data:
                    results['market_status'] = True
                    results['working_endpoints'].append('market_status')
                else:
                    results['failed_endpoints'].append('market_status')
            except Exception as e:
                logger.error(f"Market status test failed: {e}")
                results['failed_endpoints'].append('market_status')
        
        # Determine overall status
        working_count = len(results['working_endpoints'])
        if working_count >= 3:
            results['overall_status'] = 'excellent'
        elif working_count >= 2:
            results['overall_status'] = 'good'
        elif working_count >= 1:
            results['overall_status'] = 'partial'
        else:
            results['overall_status'] = 'failed'
        
        return results
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return self.scraper.get_session_info()
    
    def force_refresh(self):
        """Force refresh session"""
        return self.scraper.force_refresh()
    
    def cleanup(self):
        """Cleanup resources"""
        return self.scraper.cleanup()

# Create service instance
nse_service = NSEService()