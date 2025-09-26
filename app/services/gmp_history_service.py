# app/services/gmp_history_service.py
"""GMP History Service - Fetches and stores last 3 months GMP data"""

import requests
import json
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
import time
import random
from dateutil import parser

logger = logging.getLogger(__name__)

class GMPHistoryService:
    """Service to fetch and store last 3 months GMP data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # URL for IPOWatch GMP data
        self.ipowatch_url = 'https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/'
    
    def fetch_and_store_gmp_history(self) -> Dict[str, Any]:
        """Fetch GMP data and store only last 3 months data"""
        
        try:
            logger.info("Starting GMP history data fetch and storage...")
            
            # Scrape current GMP data
            scraped_data = self._scrape_ipowatch_data()
            
            if not scraped_data.get('success'):
                return {
                    'success': False,
                    'error': 'Failed to scrape GMP data',
                    'message': scraped_data.get('message', 'Unknown scraping error')
                }
            
            # Filter data for last 3 months
            filtered_data = self._filter_last_3_months(scraped_data['data'])
            
            # Format data for storage
            formatted_data = self._format_for_storage(filtered_data)
            
            # Store in file storage
            from ..utils.file_storage import file_storage
            
            storage_success = file_storage.save_data('gmp_history_3months', formatted_data)
            
            return {
                'success': True,
                'message': f'Successfully fetched and stored {len(formatted_data)} IPOs from last 3 months',
                'data_summary': {
                    'total_scraped': len(scraped_data.get('data', [])),
                    'filtered_count': len(filtered_data),
                    'stored_count': len(formatted_data),
                    'date_range': self._get_date_range_summary(filtered_data)
                },
                'storage_success': storage_success,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in GMP history service: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to fetch and store GMP history data'
            }
    
    def _scrape_ipowatch_data(self) -> Dict[str, Any]:
        """Scrape GMP data from IPOWatch"""
        
        try:
            logger.info("Scraping GMP data from IPOWatch...")
            
            response = self.session.get(self.ipowatch_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the specific table class
            target_table = soup.find('figure', class_='wp-block-table is-style-regular')
            
            if target_table:
                table = target_table.find('table')
            else:
                # Fallback to any table
                table = soup.find('table')
                logger.warning("wp-block-table is-style-regular not found, using fallback")
            
            if not table:
                return {
                    'success': False,
                    'message': 'No table found on IPOWatch page'
                }
            
            gmp_data = []
            rows = table.find_all('tr')
            
            logger.info(f"Found {len(rows)} rows in table")
            
            # Process each row (skip header)
            for i, row in enumerate(rows[1:], 1):
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 5:
                    try:
                        # Extract data from cells
                        company_name = cells[0].get_text(strip=True)
                        gmp_text = cells[1].get_text(strip=True)
                        price_text = cells[2].get_text(strip=True)
                        gain_text = cells[3].get_text(strip=True)
                        date_text = cells[4].get_text(strip=True)
                        type_text = cells[5].get_text(strip=True) if len(cells) > 5 else 'Unknown'
                        
                        # Skip header row
                        if company_name in ['Stock / IPO', 'Company Name', 'IPO Name']:
                            continue
                        
                        # Extract values
                        symbol = self._extract_symbol_from_name(company_name)
                        gmp_value = self._extract_number_from_text(gmp_text)
                        issue_price = self._extract_number_from_text(price_text)
                        listing_gain = self._extract_number_from_text(gain_text)
                        
                        # Parse date
                        parsed_date = self._parse_ipo_date(date_text)
                        
                        ipo_entry = {
                            'company_name': company_name,
                            'symbol': symbol,
                            'gmp_rupees': gmp_value,
                            'issue_price': issue_price,
                            'estimated_listing_price': (issue_price + gmp_value) if issue_price and gmp_value else None,
                            'listing_gain_percent': listing_gain,
                            'ipo_date_text': date_text,
                            'ipo_date_parsed': parsed_date.isoformat() if parsed_date else None,
                            'type': type_text,
                            'scraped_at': datetime.now().isoformat(),
                            'raw_data': {
                                'gmp_text': gmp_text,
                                'price_text': price_text,
                                'gain_text': gain_text
                            }
                        }
                        
                        gmp_data.append(ipo_entry)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing row {i}: {e}")
                        continue
            
            return {
                'success': True,
                'data': gmp_data,
                'total_scraped': len(gmp_data),
                'source_url': self.ipowatch_url
            }
            
        except Exception as e:
            logger.error(f"Error scraping IPOWatch data: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to scrape data from {self.ipowatch_url}'
            }
    
    def _filter_last_3_months(self, gmp_data: List[Dict]) -> List[Dict]:
        """Filter IPOs from last 3 months only"""
        
        three_months_ago = datetime.now() - timedelta(days=90)
        filtered_data = []
        
        logger.info(f"Filtering data from last 3 months (after {three_months_ago.strftime('%Y-%m-%d')})")
        
        for ipo in gmp_data:
            try:
                ipo_date_str = ipo.get('ipo_date_parsed')
                
                if ipo_date_str:
                    ipo_date = datetime.fromisoformat(ipo_date_str)
                    
                    # Check if IPO is within last 3 months
                    if ipo_date >= three_months_ago:
                        filtered_data.append(ipo)
                        logger.debug(f"Included: {ipo['symbol']} - {ipo_date.strftime('%Y-%m-%d')}")
                    else:
                        logger.debug(f"Excluded (too old): {ipo['symbol']} - {ipo_date.strftime('%Y-%m-%d')}")
                else:
                    # Include IPOs without parsed date (might be current/recent)
                    logger.debug(f"Included (no date): {ipo['symbol']}")
                    filtered_data.append(ipo)
                    
            except Exception as e:
                logger.warning(f"Error filtering IPO {ipo.get('symbol', 'Unknown')}: {e}")
                # Include in case of error
                filtered_data.append(ipo)
        
        logger.info(f"Filtered {len(filtered_data)} IPOs from last 3 months out of {len(gmp_data)} total")
        return filtered_data
    
    def _format_for_storage(self, filtered_data: List[Dict]) -> Dict[str, Any]:
        """Format data for JSON storage with proper structure"""
        
        formatted_data = {
            'metadata': {
                'data_type': 'gmp_history_3months',
                'collection_date': datetime.now().strftime('%Y-%m-%d'),
                'collection_timestamp': datetime.now().isoformat(),
                'total_ipos': len(filtered_data),
                'source': 'ipowatch.in',
                'filter_criteria': 'Last 3 months IPO data',
                'date_range': {
                    'from_date': (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                    'to_date': datetime.now().strftime('%Y-%m-%d')
                }
            },
            'ipos': {}
        }
        
        # Store IPOs with symbol as key
        for ipo in filtered_data:
            symbol = ipo['symbol']
            
            # Clean and structure the data
            formatted_ipo = {
                'basic_info': {
                    'company_name': ipo['company_name'],
                    'symbol': symbol,
                    'ipo_type': ipo['type'],
                    'ipo_date': ipo['ipo_date_text'],
                    'ipo_date_parsed': ipo['ipo_date_parsed']
                },
                'pricing_info': {
                    'issue_price': ipo['issue_price'],
                    'issue_price_currency': 'INR'
                },
                'gmp_info': {
                    'gmp_amount': ipo['gmp_rupees'],
                    'gmp_currency': 'INR',
                    'estimated_listing_price': ipo['estimated_listing_price'],
                    'expected_listing_gain_percent': ipo['listing_gain_percent']
                },
                'status_info': {
                    'data_last_updated': ipo['scraped_at'],
                    'is_active': True,
                    'data_source': 'ipowatch'
                },
                'raw_data': ipo.get('raw_data', {})
            }
            
            # Handle duplicate symbols by appending company name
            if symbol in formatted_data['ipos']:
                original_symbol = symbol
                counter = 1
                while symbol in formatted_data['ipos']:
                    symbol = f"{original_symbol}_{counter}"
                    counter += 1
                
                formatted_ipo['basic_info']['symbol'] = symbol
                logger.warning(f"Duplicate symbol detected, renamed {original_symbol} to {symbol}")
            
            formatted_data['ipos'][symbol] = formatted_ipo
        
        return formatted_data
    
    def _parse_ipo_date(self, date_text: str) -> Optional[datetime]:
        """Parse IPO date from various formats"""
        
        if not date_text or date_text.strip() == '-':
            return None
        
        try:
            current_year = datetime.now().year
            
            # Handle formats like "18-22 Sep", "19-23 Sep"
            if '-' in date_text and any(month in date_text for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                # Extract the end date
                parts = date_text.split('-')
                if len(parts) == 2:
                    end_date_part = parts[1].strip()
                    # Add current year
                    full_date = f"{end_date_part} {current_year}"
                    return parser.parse(full_date, dayfirst=True)
            
            # Handle other date formats
            try:
                return parser.parse(date_text, dayfirst=True)
            except:
                # Try with current year
                return parser.parse(f"{date_text} {current_year}", dayfirst=True)
            
        except Exception as e:
            logger.debug(f"Could not parse date '{date_text}': {e}")
            return None
    
    def _extract_symbol_from_name(self, company_name: str) -> str:
        """Extract symbol from company name"""
        
        if not company_name:
            return 'UNKNOWN'
        
        # Remove common suffixes and extract symbol
        name = company_name.upper().strip()
        
        # Remove common words
        remove_words = ['LIMITED', 'LTD', 'PRIVATE', 'PVT', 'COMPANY', 'CORP', 'CORPORATION', 'INC']
        for word in remove_words:
            name = name.replace(word, '')
        
        # Clean and extract meaningful symbol
        name = re.sub(r'[^A-Z0-9\s]', '', name).strip()
        
        # Take first few words as symbol
        words = name.split()
        if len(words) >= 2:
            return ''.join(words[:2])[:15]  # Limit to 15 chars
        elif len(words) == 1:
            return words[0][:15]
        else:
            return 'UNKNOWN'
    
    def _extract_number_from_text(self, text: str) -> Optional[float]:
        """Extract number from text like ₹25, 13.13%, etc."""
        
        if not text or text.strip() in ['-', '', '₹-', '-%']:
            return None
        
        try:
            # Remove currency symbols and extra characters
            clean_text = re.sub(r'[₹%,\s]', '', text.strip())
            
            # Handle negative numbers or empty
            if clean_text.startswith('-') or clean_text == '':
                return None
            
            # Extract number
            number_match = re.search(r'[\d.]+', clean_text)
            if number_match:
                return float(number_match.group())
            
            return None
            
        except Exception:
            return None
    
    def _get_date_range_summary(self, data: List[Dict]) -> Dict[str, str]:
        """Get date range summary from filtered data"""
        
        dates = []
        for ipo in data:
            if ipo.get('ipo_date_parsed'):
                try:
                    date = datetime.fromisoformat(ipo['ipo_date_parsed'])
                    dates.append(date)
                except:
                    continue
        
        if dates:
            return {
                'earliest_ipo': min(dates).strftime('%Y-%m-%d'),
                'latest_ipo': max(dates).strftime('%Y-%m-%d'),
                'total_with_dates': len(dates)
            }
        else:
            return {
                'earliest_ipo': 'N/A',
                'latest_ipo': 'N/A',
                'total_with_dates': 0
            }
    
    def get_stored_gmp_history(self) -> Dict[str, Any]:
        """Get stored GMP history data"""
        
        try:
            from ..utils.file_storage import file_storage
            
            stored_data = file_storage.load_data('gmp_history_3months')
            
            if stored_data and 'data' in stored_data:
                return {
                    'success': True,
                    'message': 'GMP history data loaded successfully',
                    'data': stored_data['data'],
                    'metadata': stored_data.get('metadata', {}),
                    'loaded_at': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'message': 'No stored GMP history data found. Please fetch data first.',
                    'data': None
                }
                
        except Exception as e:
            logger.error(f"Error loading stored GMP history: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to load stored GMP history data'
            }
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'session'):
                self.session.close()
            logger.info("GMP history service cleanup completed")
        except Exception as e:
            logger.error(f"GMP history service cleanup error: {e}")

# Create service instance
gmp_history_service = GMPHistoryService()