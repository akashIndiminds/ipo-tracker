# app/services/nse_service.py
"""Enhanced NSE Service - With Lot Size & Issue Size Calculation"""

import logging
import math
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from .nse_scraper import nse_scraper

logger = logging.getLogger(__name__)

class NSEService:
    """Enhanced NSE Service with lot size and issue size calculations"""
    
    def __init__(self):
        self.scraper = nse_scraper
    
    def calculate_lot_size(self, shares_bid_list: List[int]) -> int:
        """
        Calculate lot size using smart GCD approach with standard lot size detection
        """
        if not shares_bid_list:
            return 0
        
        # Filter out zeros and get unique values
        valid_bids = sorted(set([bid for bid in shares_bid_list if bid > 0]))
        
        if not valid_bids:
            return 0
        
        # Find GCD of all bids
        gcd_value = valid_bids[0]
        for bid in valid_bids[1:]:
            gcd_value = math.gcd(gcd_value, bid)
        
        if gcd_value < 10:
            return 0
        
        # Standard IPO lot sizes in India
        standard_lots = [10, 12, 14, 15, 18, 20, 24, 25, 30, 35, 40, 45, 50, 
                        60, 65, 70, 75, 80, 90, 100, 110, 114, 115, 120, 125, 
                        130, 140, 150, 160, 175, 180, 190, 200, 220, 225, 228, 
                        230, 240, 250, 260, 270, 280, 285, 300]
        
        # Check if GCD is already a standard lot size
        if gcd_value in standard_lots:
            return gcd_value
        
        # Check if GCD is a multiple of a standard lot size
        # Try to find the actual lot size by checking divisors
        possible_lots = []
        for std_lot in standard_lots:
            if std_lot > gcd_value:
                break
            if gcd_value % std_lot == 0:
                # Verify this lot size works for most bids
                matching_bids = sum(1 for bid in valid_bids if bid % std_lot == 0)
                if matching_bids >= len(valid_bids) * 0.8:  # 80% bids should match
                    possible_lots.append(std_lot)
        
        # Return the largest possible lot size that matches
        if possible_lots:
            return possible_lots[-1]
        
        # If nothing matches, check if GCD/2 is standard
        if gcd_value % 2 == 0:
            half_gcd = gcd_value // 2
            if half_gcd in standard_lots:
                # Verify half works
                matching_bids = sum(1 for bid in valid_bids if bid % half_gcd == 0)
                if matching_bids >= len(valid_bids) * 0.8:
                    return half_gcd
        
        return gcd_value
    
    def extract_price_from_range(self, price_range: str) -> Dict[str, float]:
        """
        Extract min and max prices from string like 'Rs.181 to Rs.191'
        Returns: {'min': 181.0, 'max': 191.0}
        """
        try:
            # Remove 'Rs.' and extra spaces
            clean_price = price_range.replace('Rs.', '').replace('Rs', '')
            
            # Extract numbers using regex
            numbers = re.findall(r'\d+\.?\d*', clean_price)
            
            if len(numbers) >= 2:
                return {
                    'min': float(numbers[0]),
                    'max': float(numbers[1])
                }
            elif len(numbers) == 1:
                price = float(numbers[0])
                return {'min': price, 'max': price}
            
        except Exception as e:
            logger.warning(f"Price extraction error: {e}")
        
        return {'min': 0.0, 'max': 0.0}
    
    def calculate_issue_size_rupees(self, shares: int, price_range: str) -> Dict[str, Any]:
        """
        Calculate issue size in rupees (crores)
        Returns both min and max issue sizes
        """
        prices = self.extract_price_from_range(price_range)
        
        if prices['max'] > 0 and shares > 0:
            min_size = (shares * prices['min']) / 10000000  # Convert to crores
            max_size = (shares * prices['max']) / 10000000
            
            return {
                'min_crores': round(min_size, 2),
                'max_crores': round(max_size, 2),
                'display': f"₹{round(max_size, 2)} Cr",
                'min_price': prices['min'],
                'max_price': prices['max']
            }
        
        return {
            'min_crores': 0,
            'max_crores': 0,
            'display': 'N/A',
            'min_price': 0,
            'max_price': 0
        }
    
    def enrich_ipo_with_subscription_data(self, ipo_data: Dict, subscription_data: Dict) -> Dict:
        """
        Enrich IPO data with lot size from subscription data
        """
        symbol = ipo_data.get('symbol')
        
        if not symbol or symbol not in subscription_data:
            return ipo_data
        
        sub_data = subscription_data[symbol]
        
        # Extract all shares_bid values from categories
        shares_bid_list = []
        for category, data in sub_data.get('categories', {}).items():
            bid = data.get('shares_bid', 0)
            if bid > 0:
                shares_bid_list.append(bid)
        
        # Calculate lot size
        lot_size = self.calculate_lot_size(shares_bid_list)
        
        # Add to IPO data
        ipo_data['lot_size'] = lot_size
        ipo_data['lot_size_calculated'] = True
        
        return ipo_data
    
    def fetch_current_ipos(self) -> List[Dict]:
        """Fetch and process current IPOs with enhanced data"""
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
    
    def fetch_enriched_current_ipos(self) -> List[Dict]:
        """
        Fetch current IPOs enriched with lot size from subscription data
        This combines both endpoints for complete information
        """
        logger.info("Fetching enriched current IPOs with lot size...")
        
        # Get current IPOs
        current_ipos = self.fetch_current_ipos()
        
        if not current_ipos:
            return []
        
        # Get subscription data
        symbols = [ipo.get('symbol') for ipo in current_ipos if ipo.get('symbol')]
        subscription_result = self.fetch_all_subscriptions(symbols)
        subscription_data = subscription_result.get('data', {})
        
        # Enrich IPOs with lot size
        enriched_ipos = []
        for ipo in current_ipos:
            enriched_ipo = self.enrich_ipo_with_subscription_data(ipo, subscription_data)
            enriched_ipos.append(enriched_ipo)
        
        logger.info(f"Enriched {len(enriched_ipos)} IPOs with lot size data")
        return enriched_ipos
    
    def fetch_all_subscriptions(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Fetch subscription data for all current IPOs or specific symbols"""
        logger.info("Fetching subscription data for all current IPOs...")
        
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
            
            # Skip header row
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
                
                processed['categories'][category] = category_data
                
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
        """Process raw IPO data with enhanced calculations"""
        processed = []
        
        for item in raw_data:
            try:
                symbol = str(item.get('symbol', '')).strip()
                company_name = str(item.get('companyName', '')).strip()
                shares_offered = self._safe_int(item.get('noOfSharesOffered', 0))
                price_range = str(item.get('issuePrice', '')).strip()
                
                # Calculate issue size in rupees
                issue_size_info = self.calculate_issue_size_rupees(shares_offered, price_range)
                
                processed_item = {
                    'symbol': symbol,
                    'company_name': company_name,
                    'series': str(item.get('series', 'EQ')).strip(),
                    'issue_start_date': str(item.get('issueStartDate', '')).strip(),
                    'issue_end_date': str(item.get('issueEndDate', '')).strip(),
                    'issue_price': price_range,
                    'issue_price_min': issue_size_info['min_price'],
                    'issue_price_max': issue_size_info['max_price'],
                    'issue_size_shares': shares_offered,
                    'issue_size_min_crores': issue_size_info['min_crores'],
                    'issue_size_max_crores': issue_size_info['max_crores'],
                    'issue_size_display': issue_size_info['display'],
                    'status': str(item.get('status', 'Unknown')).strip(),
                    'subscription_times': self._safe_float(item.get('noOfTime', 0)),
                    'shares_offered': shares_offered,
                    'shares_bid': self._safe_int(item.get('noOfsharesBid', 0)),
                    'is_sme': bool(item.get('isBse', '0') == '1'),
                    'category': str(item.get('category', 'Total')).strip(),
                    'lot_size': self._safe_int(item.get('lotSize', 0)),
                    'lot_size_calculated': False,
                    'face_value': str(item.get('faceValue', '')).strip()
                }
                
                if processed_item['symbol'] and processed_item['company_name']:
                    processed.append(processed_item)
                    
            except Exception as e:
                logger.warning(f"IPO processing error: {e}")
                continue
        
        logger.info(f"Processed {len(processed)} IPO records with issue size calculations")
        return processed
    
    def _safe_int(self, value) -> int:
        """Safely convert value to integer"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
                if not value:
                    return 0
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
            current_data = self.scraper.make_api_call('/ipo-current-issue')
            test_results['current_ipos'] = bool(current_data)
            
            upcoming_data = self.scraper.make_api_call('/all-upcoming-issues', {'category': 'ipo'})
            test_results['upcoming_ipos'] = bool(upcoming_data)
            
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