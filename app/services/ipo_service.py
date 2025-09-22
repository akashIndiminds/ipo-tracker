# app/services/ipo_service.py
"""
IPO Business Logic Service
"""

from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
from app.services.nse_scraper import NSEScraper

logger = logging.getLogger(__name__)

class IPOService:
    """
    IPO Business Logic and Data Processing
    """
    
    def __init__(self):
        self.scraper = NSEScraper()
    
    def get_current_ipos(self, include_gmp: bool = True) -> Dict[str, Any]:
        """Get current IPOs with processing"""
        try:
            # Fetch raw data
            raw_data = self.scraper.get_current_ipos()
            
            # Process data
            processed_data = self._process_ipo_data(raw_data)
            
            # Add GMP if requested
            if include_gmp:
                gmp_data = self.scraper.get_gmp_data()
                processed_data = self._merge_gmp_data(processed_data, gmp_data)
            
            return {
                'success': True,
                'count': len(processed_data),
                'data': processed_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting current IPOs: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def get_upcoming_ipos(self, include_gmp: bool = True) -> Dict[str, Any]:
        """Get upcoming IPOs with processing"""
        try:
            # Fetch raw data
            raw_data = self.scraper.get_upcoming_ipos()
            
            # Process data
            processed_data = self._process_ipo_data(raw_data)
            
            # Add GMP if requested
            if include_gmp:
                gmp_data = self.scraper.get_gmp_data()
                processed_data = self._merge_gmp_data(processed_data, gmp_data)
            
            return {
                'success': True,
                'count': len(processed_data),
                'data': processed_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting upcoming IPOs: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def get_past_ipos(self, days: int = 30) -> Dict[str, Any]:
        """Get past IPOs with processing"""
        try:
            # Fetch raw data
            raw_data = self.scraper.get_past_ipos(days)
            
            # Process data
            processed_data = self._process_ipo_data(raw_data)
            
            return {
                'success': True,
                'count': len(processed_data),
                'data': processed_data,
                'days_back': days,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting past IPOs: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def get_ipo_summary(self) -> Dict[str, Any]:
        """Get complete IPO summary"""
        try:
            current = self.scraper.get_current_ipos()
            upcoming = self.scraper.get_upcoming_ipos()
            past = self.scraper.get_past_ipos(30)
            gmp = self.scraper.get_gmp_data()
            
            return {
                'success': True,
                'summary': {
                    'current_count': len(current),
                    'upcoming_count': len(upcoming),
                    'past_count': len(past),
                    'total_active': len(current) + len(upcoming),
                    'gmp_tracked': len(gmp)
                },
                'current_ipos': self._process_ipo_data(current)[:5],
                'upcoming_ipos': self._process_ipo_data(upcoming)[:5],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting IPO summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _process_ipo_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Process and clean IPO data"""
        processed = []
        
        for item in raw_data:
            try:
                processed_item = {
                    'symbol': item.get('symbol', ''),
                    'company_name': item.get('companyName', ''),
                    'series': item.get('series', ''),
                    'issue_start_date': item.get('issueStartDate', ''),
                    'issue_end_date': item.get('issueEndDate', ''),
                    'issue_price': item.get('issuePrice', ''),
                    'issue_size': item.get('issueSize', ''),
                    'status': item.get('status', ''),
                    'subscription_times': item.get('noOfTime', ''),
                    'shares_offered': item.get('noOfSharesOffered', ''),
                    'shares_bid': item.get('noOfsharesBid', '')
                }
                
                # Add calculated fields
                processed_item.update(self._calculate_metrics(processed_item))
                
                processed.append(processed_item)
                
            except Exception as e:
                logger.warning(f"Error processing IPO item: {e}")
                continue
        
        return processed
    
    def _calculate_metrics(self, ipo: Dict) -> Dict:
        """Calculate additional metrics"""
        metrics = {}
        
        # Subscription status
        sub_times = ipo.get('subscription_times', '')
        if sub_times and self._is_number(sub_times):
            sub_rate = float(sub_times)
            metrics['subscription_status'] = "Oversubscribed" if sub_rate > 1 else "Undersubscribed"
            metrics['subscription_level'] = self._get_subscription_level(sub_rate)
        
        return metrics
    
    def _merge_gmp_data(self, ipo_data: List[Dict], gmp_data: List[Dict]) -> List[Dict]:
        """Merge GMP data with IPO data"""
        # Create GMP lookup
        gmp_lookup = {}
        for gmp in gmp_data:
            company = gmp.get('company_name', '').upper()
            gmp_lookup[company] = gmp
        
        # Merge data
        for ipo in ipo_data:
            company = ipo.get('company_name', '').upper()
            
            # Try exact match
            if company in gmp_lookup:
                ipo['gmp'] = gmp_lookup[company].get('gmp', 0)
                ipo['estimated_listing_gain'] = gmp_lookup[company].get('estimated_listing_gain', 0)
            else:
                # Try partial match
                for gmp_company, gmp_info in gmp_lookup.items():
                    if company in gmp_company or gmp_company in company:
                        ipo['gmp'] = gmp_info.get('gmp', 0)
                        ipo['estimated_listing_gain'] = gmp_info.get('estimated_listing_gain', 0)
                        break
        
        return ipo_data
    
    def _is_number(self, text: str) -> bool:
        """Check if text is a number"""
        try:
            float(text)
            return True
        except:
            return False
    
    def _get_subscription_level(self, rate: float) -> str:
        """Get subscription level description"""
        if rate >= 10:
            return "Heavily Oversubscribed"
        elif rate >= 5:
            return "Highly Oversubscribed"
        elif rate >= 2:
            return "Well Subscribed"
        elif rate >= 1:
            return "Fully Subscribed"
        else:
            return "Undersubscribed"