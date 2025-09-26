# app/controllers/gmp_history_controller.py
"""GMP History Controller - Handles GMP history data requests"""


from typing import Dict, Any, List 
import logging
from datetime import datetime
from fastapi import HTTPException

from ..services.gmp_history_service import gmp_history_service

logger = logging.getLogger(__name__)

class GMPHistoryController:
    """GMP History Controller - Handles GMP history HTTP requests"""
    
    def __init__(self):
        self.gmp_history_service = gmp_history_service
    
    async def fetch_and_store_gmp_history(self) -> Dict[str, Any]:
        """Fetch and store last 3 months GMP data"""
        try:
            logger.info("Processing GMP history fetch and store request")
            
            # Call service to fetch and store data
            result = self.gmp_history_service.fetch_and_store_gmp_history()
            
            if not result.get('success'):
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to fetch and store GMP history: {result.get('message', 'Unknown error')}"
                )
            
            return {
                'success': True,
                'message': result['message'],
                'data_summary': result.get('data_summary', {}),
                'storage_info': {
                    'storage_success': result.get('storage_success', False),
                    'file_type': 'gmp_history_3months',
                    'file_format': 'JSON'
                },
                'processing_info': {
                    'filter_applied': 'Last 3 months only',
                    'source': 'ipowatch.in',
                    'data_structure': 'Symbol-based JSON format'
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - GMP history fetch and store: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch and store GMP history: {str(e)}"
            )
    
    async def get_stored_gmp_history(self) -> Dict[str, Any]:
        """Get stored GMP history data"""
        try:
            logger.info("Processing get stored GMP history request")
            
            result = self.gmp_history_service.get_stored_gmp_history()
            
            if not result.get('success'):
                raise HTTPException(
                    status_code=404,
                    detail=result.get('message', 'No GMP history data found')
                )
            
            data = result.get('data', {})
            metadata = result.get('metadata', {})
            
            return {
                'success': True,
                'message': 'GMP history data retrieved successfully',
                'data_info': {
                    'total_ipos': metadata.get('total_ipos', 0),
                    'collection_date': metadata.get('collection_date'),
                    'date_range': metadata.get('date_range', {}),
                    'source': metadata.get('source'),
                    'data_type': metadata.get('data_type')
                },
                'gmp_data': data.get('ipos', {}),
                'metadata': metadata,
                'retrieved_at': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - get stored GMP history: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve GMP history data: {str(e)}"
            )
    
    async def get_gmp_summary(self) -> Dict[str, Any]:
        """Get summary of stored GMP history data"""
        try:
            logger.info("Processing GMP history summary request")
            
            result = self.gmp_history_service.get_stored_gmp_history()
            
            if not result.get('success'):
                raise HTTPException(
                    status_code=404,
                    detail="No GMP history data found. Please fetch data first."
                )
            
            data = result.get('data', {})
            ipos = data.get('ipos', {})
            metadata = result.get('metadata', {})
            
            # Calculate summary statistics
            summary_stats = self._calculate_summary_statistics(ipos)
            
            return {
                'success': True,
                'message': f'GMP history summary generated for {len(ipos)} IPOs',
                'summary_statistics': summary_stats,
                'data_info': {
                    'total_ipos': len(ipos),
                    'collection_date': metadata.get('collection_date'),
                    'date_range': metadata.get('date_range', {}),
                    'source': metadata.get('source')
                },
                'top_performers': self._get_top_performers(ipos, 5),
                'timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - GMP summary: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate GMP summary: {str(e)}"
            )
    
    async def search_ipo_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """Search for specific IPO by symbol"""
        try:
            logger.info(f"Processing IPO search request for symbol: {symbol}")
            
            result = self.gmp_history_service.get_stored_gmp_history()
            
            if not result.get('success'):
                raise HTTPException(
                    status_code=404,
                    detail="No GMP history data found. Please fetch data first."
                )
            
            data = result.get('data', {})
            ipos = data.get('ipos', {})
            
            # Search for IPO
            symbol_upper = symbol.upper()
            found_ipo = None
            matched_symbol = None
            
            # Exact match first
            if symbol_upper in ipos:
                found_ipo = ipos[symbol_upper]
                matched_symbol = symbol_upper
            else:
                # Partial match
                for ipo_symbol, ipo_data in ipos.items():
                    if symbol_upper in ipo_symbol or ipo_symbol in symbol_upper:
                        found_ipo = ipo_data
                        matched_symbol = ipo_symbol
                        break
            
            if not found_ipo:
                raise HTTPException(
                    status_code=404,
                    detail=f"IPO with symbol '{symbol}' not found in stored data"
                )
            
            return {
                'success': True,
                'message': f'IPO found for symbol: {symbol}',
                'searched_symbol': symbol,
                'matched_symbol': matched_symbol,
                'ipo_data': found_ipo,
                'search_timestamp': datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Controller error - search IPO by symbol {symbol}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to search IPO by symbol: {str(e)}"
            )
    
    def _calculate_summary_statistics(self, ipos: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics from IPO data"""
        
        if not ipos:
            return {
                'total_ipos': 0,
                'avg_gmp': 0,
                'avg_expected_gain': 0,
                'positive_gmp_count': 0,
                'negative_gmp_count': 0
            }
        
        gmp_values = []
        expected_gains = []
        positive_gmp = 0
        negative_gmp = 0
        
        for symbol, ipo_data in ipos.items():
            gmp_info = ipo_data.get('gmp_info', {})
            
            gmp_amount = gmp_info.get('gmp_amount')
            expected_gain = gmp_info.get('expected_listing_gain_percent')
            
            if gmp_amount is not None:
                gmp_values.append(gmp_amount)
                if gmp_amount > 0:
                    positive_gmp += 1
                elif gmp_amount < 0:
                    negative_gmp += 1
            
            if expected_gain is not None:
                expected_gains.append(expected_gain)
        
        return {
            'total_ipos': len(ipos),
            'avg_gmp': round(sum(gmp_values) / len(gmp_values), 2) if gmp_values else 0,
            'avg_expected_gain': round(sum(expected_gains) / len(expected_gains), 2) if expected_gains else 0,
            'positive_gmp_count': positive_gmp,
            'negative_gmp_count': negative_gmp,
            'neutral_gmp_count': len(ipos) - positive_gmp - negative_gmp,
            'positive_gmp_percentage': round((positive_gmp / len(ipos)) * 100, 1) if ipos else 0,
            'gmp_range': {
                'min_gmp': min(gmp_values) if gmp_values else 0,
                'max_gmp': max(gmp_values) if gmp_values else 0
            },
            'gain_range': {
                'min_gain': min(expected_gains) if expected_gains else 0,
                'max_gain': max(expected_gains) if expected_gains else 0
            }
        }
    
    def _get_top_performers(self, ipos: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing IPOs by expected gain"""
        
        performers = []
        
        for symbol, ipo_data in ipos.items():
            basic_info = ipo_data.get('basic_info', {})
            gmp_info = ipo_data.get('gmp_info', {})
            
            expected_gain = gmp_info.get('expected_listing_gain_percent')
            
            if expected_gain is not None:
                performers.append({
                    'symbol': symbol,
                    'company_name': basic_info.get('company_name'),
                    'expected_gain_percent': expected_gain,
                    'gmp_amount': gmp_info.get('gmp_amount'),
                    'issue_price': ipo_data.get('pricing_info', {}).get('issue_price'),
                    'estimated_listing_price': gmp_info.get('estimated_listing_price')
                })
        
        # Sort by expected gain (descending)
        performers.sort(key=lambda x: x['expected_gain_percent'] or 0, reverse=True)
        
        return performers[:limit]

# Create controller instance
gmp_history_controller = GMPHistoryController()