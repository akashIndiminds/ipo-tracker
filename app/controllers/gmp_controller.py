# app/controllers/gmp_controller.py

from typing import Dict, Optional
import logging
from datetime import datetime
from ..services.gmp_service import gmp_service
from ..utils.file_storage import file_storage

logger = logging.getLogger(__name__)

class GMPController:
    """Simplified GMP Controller - handles only GMP data from 2 sources"""
    
    async def fetch_gmp_data(self) -> Dict:
        """Fetch current GMP data from both sources and create combined data"""
        try:
            result = gmp_service.fetch_current_gmp()
            
            if result['success']:
                return {
                    'success': True,
                    'message': f"Successfully fetched GMP data from {result['successful_sources']}/{result['total_sources']} sources",
                    'total_sources': result['total_sources'],
                    'successful_sources': result['successful_sources'],
                    'timestamp': result['timestamp'],
                    'period': 'current',
                    'sources_scraped': list(result['source_data'].get('sources', {}).keys()),
                    'total_unique_ipos': result.get('combined_data', {}).get('total_unique_ipos', 0)
                }
            
            return {
                'success': False,
                'message': 'Failed to fetch GMP data from sources',
                'errors': result.get('errors', [])
            }
            
        except Exception as e:
            logger.error(f"GMP Controller fetch error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_gmp_prediction(self, symbol: str, ipo_data: Dict, date: Optional[str] = None) -> Dict:
        """Get GMP data for symbol with date support"""
        try:
            prediction = gmp_service.get_gmp_prediction(symbol, {}, date)
            
            # Save individual prediction
            save_date = date or datetime.now().strftime('%Y-%m-%d')
            file_storage.save_data(f"gmp/predictions/{symbol}_{save_date}", prediction)
            
            return prediction
            
        except Exception as e:
            logger.error(f"GMP prediction error for {symbol}: {e}")
            return {
                'symbol': symbol,
                'source': 'Combined GMP',
                'has_data': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def scrape_all_sources(self) -> Dict:
        """Scrape data from both GMP sources separately"""
        try:
            # Scrape both sources
            source_data = gmp_service.scrape_all_sources()
            
            if not source_data['success']:
                return {
                    'success': False,
                    'message': 'Failed to scrape GMP sources',
                    'errors': source_data.get('errors', [])
                }
            
            # Save source data separately
            save_result = gmp_service.save_source_data(source_data)
            
            # Count successful sources
            successful_sources = [name for name, data in source_data['sources'].items() if data['success']]
            total_ipos = sum(data['count'] for data in source_data['sources'].values() if data['success'])
            
            return {
                'success': True,
                'message': f'Successfully scraped {len(successful_sources)} sources with {total_ipos} total IPOs',
                'timestamp': source_data['timestamp'],
                'date': source_data['date'],
                'total_sources': len(source_data['sources']),
                'successful_sources': len(successful_sources),
                'sources_scraped': successful_sources,
                'total_ipos': total_ipos,
                'source_details': {
                    name: {
                        'success': data['success'],
                        'count': data['count'],
                        'scraped_at': data.get('scraped_at')
                    } for name, data in source_data['sources'].items()
                },
                'save_result': save_result
            }
            
        except Exception as e:
            logger.error(f"GMP sources scraping error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_combined_gmp_data(self, date: str) -> Dict:
        """Create combined GMP data for specific date"""
        try:
            combined_data = gmp_service.create_combined_gmp_data(date)
            
            if 'error' in combined_data:
                return {
                    'success': False,
                    'message': f'Failed to create combined GMP data for {date}',
                    'error': combined_data['error'],
                    'date': date
                }
            
            return {
                'success': True,
                'message': f'Successfully created combined GMP data for {date}',
                'timestamp': combined_data['timestamp'],
                'date': date,
                'total_unique_ipos': combined_data.get('total_unique_ipos', 0),
                'source_counts': combined_data.get('source_counts', {}),
                'sources_available': combined_data.get('sources_available', []),
                'data_summary': self._create_data_summary(combined_data.get('gmp_data', {}))
            }
            
        except Exception as e:
            logger.error(f"Combined GMP data error for {date}: {e}")
            return {
                'success': False,
                'error': str(e),
                'date': date
            }
    
    def _create_data_summary(self, gmp_data: Dict) -> Dict:
        """Create summary of GMP data"""
        summary = {
            'total_ipos': len(gmp_data),
            'source_distribution': {
                'only_ipowatch': 0,
                'only_investorgain': 0,
                'both_sources': 0
            },
            'gmp_stats': {
                'positive_gmp': 0,
                'negative_gmp': 0,
                'zero_gmp': 0,
                'no_gmp_data': 0
            }
        }
        
        for symbol, data in gmp_data.items():
            # Count source distribution
            available_in = data.get('available_in', [])
            if len(available_in) == 2:
                summary['source_distribution']['both_sources'] += 1
            elif 'ipowatch' in available_in:
                summary['source_distribution']['only_ipowatch'] += 1
            elif 'investorgain' in available_in:
                summary['source_distribution']['only_investorgain'] += 1
            
            # Count GMP categories
            gmp_value = data.get('gmp_value', 0)
            if gmp_value > 0:
                summary['gmp_stats']['positive_gmp'] += 1
            elif gmp_value < 0:
                summary['gmp_stats']['negative_gmp'] += 1
            elif gmp_value == 0:
                summary['gmp_stats']['zero_gmp'] += 1
            else:
                summary['gmp_stats']['no_gmp_data'] += 1
        
        return summary
    
    async def get_source_data(self, source: str, date: Optional[str] = None) -> Dict:
        """Get data from specific source for date"""
        try:
            target_date = date or datetime.now().strftime('%Y-%m-%d')
            
            if source not in ['ipowatch', 'investorgain']:
                return {
                    'success': False,
                    'error': f'Invalid source: {source}. Available sources: ipowatch, investorgain'
                }
            
            source_data = file_storage.load_data(f"gmp/{source}/current-ipo-{target_date}.json")
            
            if source_data:
                return {
                    'success': True,
                    'source': source,
                    'date': target_date,
                    'total_ipos': len(source_data),
                    'data': source_data
                }
            else:
                return {
                    'success': False,
                    'message': f'No {source} data found for {target_date}',
                    'source': source,
                    'date': target_date
                }
                
        except Exception as e:
            logger.error(f"Error getting {source} data for {date}: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': source,
                'date': target_date
            }
    
    async def get_cached_combined_data(self, date: str) -> Dict:
        """Get cached combined GMP data for date"""
        try:
            combined_data = file_storage.load_data(f'gmp-combined-{date}.json')
            
            if combined_data:
                return {
                    'success': True,
                    'message': f'Found cached combined data for {date}',
                    'date': date,
                    'total_unique_ipos': combined_data.get('total_unique_ipos', 0),
                    'sources_available': combined_data.get('sources_available', []),
                    'timestamp': combined_data.get('timestamp'),
                    'data': combined_data
                }
            else:
                return {
                    'success': False,
                    'message': f'No cached combined data found for {date}',
                    'date': date
                }
                
        except Exception as e:
            logger.error(f"Error getting cached combined data for {date}: {e}")
            return {
                'success': False,
                'error': str(e),
                'date': date
            }

# Create controller instance
gmp_controller = GMPController()