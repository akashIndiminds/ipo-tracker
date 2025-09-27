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
                    'face_value': str(item.get('faceValue', '')).strip()
                    # Removed raw_data field - no duplication
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
                    'index': str(item.get('index', '')).strip()
                    # Removed raw_data field
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
                'categories': {}
                # Removed raw_data field
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
                'error': str(e)
                # Removed raw_data field
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