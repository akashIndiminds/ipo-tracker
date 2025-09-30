# app/services/nse_service.py
"""NSE Service - Business Logic for IPO Data Processing"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
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
    
    def fetch_all_subscriptions(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Fetch subscription data for all current IPOs or specific symbols"""
        logger.info("Fetching subscription data for all current IPOs...")
        
        # If no symbols provided, get them from current IPOs
        if not symbols:
            current_ipos = self.fetch_current_ipos()
            symbols = [ipo.get('symbol') for ipo in current_ipos if ipo.get('symbol')]
            logger.info(f"Found {len(symbols)} symbols from current IPOs: {symbols}")
        
        if not symbols:
            logger.warning("No symbols found to fetch subscription data")
            return {}
        
        subscription_data = {}
        failed_symbols = []
        
        for symbol in symbols:
            try:
                logger.info(f"Fetching subscription data for {symbol}")
                raw_data = self.scraper.make_api_call('/ipo-active-category', {'symbol': symbol})
                
                if raw_data:
                    processed_data = self._process_subscription_data(raw_data, symbol)
                    subscription_data[symbol] = processed_data
                    logger.info(f"Successfully processed subscription data for {symbol}")
                else:
                    failed_symbols.append(symbol)
                    logger.warning(f"No subscription data received for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error fetching subscription data for {symbol}: {e}")
                failed_symbols.append(symbol)
        
        # Return structured data
        result = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_symbols': len(symbols),
                'successful_symbols': len(subscription_data),
                'failed_symbols': failed_symbols,
                'success_rate': round((len(subscription_data) / len(symbols)) * 100, 1) if symbols else 0
            },
            'data': subscription_data
        }
        
        logger.info(f"Subscription data fetch completed: {len(subscription_data)}/{len(symbols)} successful")
        return result
    
    def _process_subscription_data(self, raw_data: Dict, symbol: str) -> Dict:
        """Process subscription data from NSE API response"""
        try:
            processed = {
                'symbol': symbol,
                'update_time': raw_data.get('updateTime', ''),
                'categories': {},
                'total_subscription': 0.0,
                'fetched_at': datetime.now().isoformat()
            }
            
            data_list = raw_data.get('dataList', [])
            if not data_list:
                return processed
            
            # Skip header row (first item)
            for item in data_list[1:]:
                if not isinstance(item, dict):
                    continue
                    
                sr_no = str(item.get('srNo', '')).strip()
                category = str(item.get('category', '')).strip()
                shares_offered = item.get('noOfShareOffered', '')
                shares_bid = item.get('noOfSharesBid', '')
                subscription_times = item.get('noOfTotalMeant', '')
                
                if not category:
                    continue
                
                # Process subscription times
                subscription_float = self._safe_float(subscription_times)
                
                category_data = {
                    'sr_no': sr_no,
                    'shares_offered': self._safe_int(shares_offered),
                    'shares_bid': self._safe_int(shares_bid),
                    'subscription_times': subscription_float,
                    'shares_offered_raw': str(shares_offered),
                    'shares_bid_raw': str(shares_bid),
                    'subscription_raw': str(subscription_times)
                }
                
                # Store category data
                processed['categories'][category] = category_data
                
                # Update total subscription for main categories
                if category == 'Total':
                    processed['total_subscription'] = subscription_float
            
            logger.info(f"Processed {len(processed['categories'])} categories for {symbol}")
            return processed
            
        except Exception as e:
            logger.error(f"Subscription data processing error for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'fetched_at': datetime.now().isoformat()
            }
    
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
                }
                
                if processed_item['symbol'] and processed_item['company_name']:
                    processed.append(processed_item)
                    
            except Exception as e:
                logger.warning(f"IPO processing error: {e}")
                continue
        
        logger.info(f"Processed {len(processed)} IPO records")
        return processed
    
    def _safe_int(self, value) -> int:
        """Safely convert value to integer"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
                if not value:
                    return 0
                # Handle scientific notation
                if 'E' in value.upper() or 'e' in value:
                    return int(float(value))
                return int(float(value))
            return int(float(value)) if value else 0
        except:
            return 0
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
                if not value:
                    return 0.0
                return float(value)
            return float(value) if value else 0.0
        except:
            return 0.0
    
    def test_connection(self) -> Dict[str, Any]:
        """Test NSE API connectivity"""
        logger.info("Testing NSE connection...")
        
        test_results = {
            'homepage': False,
            'current_ipos': False,
            'upcoming_ipos': False,
            'overall_status': 'failed',
            'tested_at': datetime.now().isoformat()
        }
        
        try:
            # Test current IPOs endpoint
            current_data = self.scraper.make_api_call('/ipo-current-issue')
            test_results['current_ipos'] = bool(current_data)
            
            # Test upcoming IPOs endpoint  
            upcoming_data = self.scraper.make_api_call('/all-upcoming-issues', {'category': 'ipo'})
            test_results['upcoming_ipos'] = bool(upcoming_data)
            
            # Determine overall status
            successful_tests = sum([
                test_results['current_ipos'],
                test_results['upcoming_ipos']
            ])
            
            if successful_tests == 2:
                test_results['overall_status'] = 'excellent'
            elif successful_tests == 1:
                test_results['overall_status'] = 'partial'
            else:
                test_results['overall_status'] = 'failed'
                
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            test_results['error'] = str(e)
        
        return test_results
    
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