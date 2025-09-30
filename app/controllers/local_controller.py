# app/controllers/local_controller.py
"""Local Controller - Serves locally stored IPO data with subscription details"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from fastapi import HTTPException

from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class LocalController:
    """Local Controller - Serves IPO data from JSON files"""
    
    def __init__(self):
        self.file_storage = file_storage
    
    async def get_current_ipos(self, date: str = None) -> Dict[str, Any]:
        """
        Get current IPOs with subscription data (Groww style)
        
        Returns IPO details with subscription breakdown like:
        QIB: 0.77x | NII: 0.45x | Retail: 0.67x | Total: 0.69x
        """
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"📊 Loading current IPOs with subscription data for: {date}")
            
            # Load current IPO data
            current_data = self.file_storage.load_data('nse/current', date)
            if not current_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No current IPO data found for {date}"
                )
            
            # Load subscription data
            subscription_data = self.file_storage.load_data('nse/subscription', date)
            
            # Extract IPOs list
            ipos = current_data.get('data', [])
            if not ipos:
                return {
                    'success': True,
                    'message': 'No current IPOs available',
                    'date': date,
                    'count': 0,
                    'data': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Process each IPO with subscription data
            enriched_ipos = []
            for ipo in ipos:
                symbol = ipo.get('symbol', '')
                
                # Get subscription details for this IPO
                subscription_info = self._get_subscription_for_symbol(
                    symbol, 
                    subscription_data
                )
                
                # Combine IPO + Subscription data
                enriched_ipo = {
                    'symbol': symbol,
                    'company_name': ipo.get('company_name', ''),
                    'issue_price': ipo.get('issue_price', ''),
                    'issue_size': ipo.get('issue_size', ''),
                    'lot_size': ipo.get('lot_size', 0),
                    'issue_start_date': ipo.get('issue_start_date', ''),
                    'issue_end_date': ipo.get('issue_end_date', ''),
                    'status': ipo.get('status', ''),
                    'series': ipo.get('series', ''),
                    
                    # Subscription data (Groww style)
                    'subscription': subscription_info
                }
                
                enriched_ipos.append(enriched_ipo)
            
            return {
                'success': True,
                'message': f'Loaded {len(enriched_ipos)} current IPOs with subscription data',
                'date': date,
                'count': len(enriched_ipos),
                'data': enriched_ipos,
                'source': 'LOCAL_STORAGE',
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error loading current IPOs: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load current IPOs: {str(e)}"
            )
    
    async def get_upcoming_ipos(self, date: str = None) -> Dict[str, Any]:
        """Get upcoming IPOs from stored data"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"📅 Loading upcoming IPOs for: {date}")
            
            # Load upcoming IPO data
            upcoming_data = self.file_storage.load_data('nse/upcoming', date)
            if not upcoming_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No upcoming IPO data found for {date}"
                )
            
            ipos = upcoming_data.get('data', [])
            
            # Process upcoming IPOs (no subscription data needed)
            processed_ipos = []
            for ipo in ipos:
                processed_ipo = {
                    'symbol': ipo.get('symbol', ''),
                    'company_name': ipo.get('company_name', ''),
                    'issue_price': ipo.get('issue_price', ''),
                    'issue_size': ipo.get('issue_size', ''),
                    'lot_size': ipo.get('lot_size', 0),
                    'issue_start_date': ipo.get('issue_start_date', ''),
                    'issue_end_date': ipo.get('issue_end_date', ''),
                    'status': ipo.get('status', ''),
                    'series': ipo.get('series', '')
                }
                processed_ipos.append(processed_ipo)
            
            return {
                'success': True,
                'message': f'Loaded {len(processed_ipos)} upcoming IPOs',
                'date': date,
                'count': len(processed_ipos),
                'data': processed_ipos,
                'source': 'LOCAL_STORAGE',
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error loading upcoming IPOs: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load upcoming IPOs: {str(e)}"
            )
    
    async def get_subscription_data(self, date: str = None) -> Dict[str, Any]:
        """Get raw subscription data for all IPOs"""
        try:
            if not date:
                date = datetime.now().strftime("%Y-%m-%d")
            
            logger.info(f"📈 Loading subscription data for: {date}")
            
            # Load subscription data
            subscription_data = self.file_storage.load_data('nse/subscription', date)
            if not subscription_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No subscription data found for {date}"
                )
            
            # Extract subscription details
            data = subscription_data.get('data', {})
            metadata = data.get('metadata', {})
            subscription_dict = data.get('data', {})
            
            return {
                'success': True,
                'message': f'Loaded subscription data for {len(subscription_dict)} IPOs',
                'date': date,
                'count': len(subscription_dict),
                'data': subscription_dict,
                'metadata': metadata,
                'source': 'LOCAL_STORAGE',
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error loading subscription data: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load subscription data: {str(e)}"
            )
    
    def _get_subscription_for_symbol(self, symbol: str, subscription_data: Dict) -> Dict:
        """
        Extract subscription data for a specific symbol
        Returns Groww-style format:
        {
            'qib': '0.77x',
            'nii': '0.45x', 
            'retail': '0.67x',
            'total': '0.69x',
            'has_data': True
        }
        """
        if not subscription_data:
            return self._empty_subscription()
        
        try:
            # Navigate nested structure
            data = subscription_data.get('data', {})
            sub_dict = data.get('data', {})
            
            # Get symbol-specific data
            symbol_data = sub_dict.get(symbol)
            if not symbol_data:
                return self._empty_subscription()
            
            categories = symbol_data.get('categories', {})
            
            # Extract subscription times for each category
            qib = self._extract_subscription(
                categories.get('Qualified Institutional Buyers(QIBs)', {})
            )
            
            nii = self._extract_subscription(
                categories.get('Non Institutional Investors', {})
            )
            
            retail = self._extract_subscription(
                categories.get('Retail Individual Investors(RIIs)', {})
            )
            
            total = symbol_data.get('total_subscription', 0)
            
            return {
                'qib': f"{qib:.2f}x" if qib > 0 else "0.00x",
                'nii': f"{nii:.2f}x" if nii > 0 else "0.00x",
                'retail': f"{retail:.2f}x" if retail > 0 else "0.00x",
                'total': f"{total:.2f}x" if total > 0 else "0.00x",
                'qib_numeric': qib,
                'nii_numeric': nii,
                'retail_numeric': retail,
                'total_numeric': total,
                'has_data': True,
                'display': f"QIB: {qib:.2f}x | NII: {nii:.2f}x | Retail: {retail:.2f}x | Total: {total:.2f}x"
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Error extracting subscription for {symbol}: {e}")
            return self._empty_subscription()
    
    def _extract_subscription(self, category_data: Dict) -> float:
        """Extract subscription times from category data"""
        try:
            sub_times = category_data.get('subscription_times', 0)
            return float(sub_times) if sub_times else 0.0
        except:
            return 0.0
    
    def _empty_subscription(self) -> Dict:
        """Return empty subscription data structure"""
        return {
            'qib': '0.00x',
            'nii': '0.00x',
            'retail': '0.00x',
            'total': '0.00x',
            'qib_numeric': 0.0,
            'nii_numeric': 0.0,
            'retail_numeric': 0.0,
            'total_numeric': 0.0,
            'has_data': False,
            'display': 'No subscription data available'
        }

# Create controller instance
local_controller = LocalController()