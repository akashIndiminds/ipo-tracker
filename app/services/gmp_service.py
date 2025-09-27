# ===================================
# SIMPLIFIED GMP SERVICE - Only 2 Sources Combined
# ===================================
# app/services/gmp_service.py

import requests
import json
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
import time
import random

logger = logging.getLogger(__name__)

class GMPService:
    """Simplified GMP Service - Only IPOWatch + InvestorGain, no NSE dependency"""
    
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
        
        # Only 2 sources
        self.sources = {
            'ipowatch': {
                'url': 'https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/',
                'backup': 'https://ipowatch.in/live-ipo-gmp-today/',
                'parser': self._parse_ipowatch
            },
            'investorgain': {
                'url': 'https://www.investorgain.com/report/live-ipo-gmp/331/all/',
                'backup': 'https://www.investorgain.com/report/live-ipo-gmp/331/ipo/',
                'parser': self._parse_investorgain_new
            }
        }
    
    def scrape_all_sources(self) -> Dict[str, Any]:
        """Scrape data from both sources separately"""
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'sources': {},
            'errors': []
        }
        
        for source_name, source_config in self.sources.items():
            try:
                logger.info(f"Scraping {source_name}...")
                
                # Try primary URL first
                data = self._scrape_source(source_config['url'], source_config['parser'])
                
                # Try backup URL if primary fails
                if not data:
                    logger.warning(f"Primary URL failed for {source_name}, trying backup...")
                    data = self._scrape_source(source_config['backup'], source_config['parser'])
                
                if data:
                    result['sources'][source_name] = {
                        'success': True,
                        'count': len(data),
                        'data': data,
                        'scraped_at': datetime.now().isoformat()
                    }
                    logger.info(f"Successfully scraped {len(data)} IPOs from {source_name}")
                else:
                    result['sources'][source_name] = {
                        'success': False,
                        'count': 0,
                        'data': {},
                        'error': f"Failed to scrape {source_name}"
                    }
                    result['errors'].append(f"Failed to scrape {source_name}")
                
                # Rate limiting
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {e}")
                result['sources'][source_name] = {
                    'success': False,
                    'count': 0,
                    'data': {},
                    'error': str(e)
                }
                result['errors'].append(f"{source_name}: {str(e)}")
        
        # Check if at least one source succeeded
        if not any(source['success'] for source in result['sources'].values()):
            result['success'] = False
        
        return result
    
    def _scrape_source(self, url: str, parser_func) -> Optional[Dict]:
        """Scrape data from a specific source"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            return parser_func(response.text)
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def _parse_ipowatch(self, html: str) -> Dict[str, Dict]:
        """Parse IPO Watch GMP data"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            gmp_data = {}
            
            # Look for the specific table class
            target_table = soup.find('figure', class_='wp-block-table is-style-regular')
            
            if target_table:
                table = target_table.find('table')
            else:
                # Fallback to any table
                table = soup.find('table')
                logger.warning("wp-block-table is-style-regular not found, using fallback")
            
            if not table:
                return {}
            
            rows = table.find_all('tr')
            logger.info(f"Found {len(rows)} rows in IPOWatch table")
            
            # Process each row (skip header)
            for i, row in enumerate(rows[1:], 1):
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 5:
                    try:
                        company_name = cells[0].get_text(strip=True)
                        gmp_text = cells[1].get_text(strip=True)
                        price_text = cells[2].get_text(strip=True)
                        gain_text = cells[3].get_text(strip=True)
                        date_text = cells[4].get_text(strip=True)
                        type_text = cells[5].get_text(strip=True) if len(cells) > 5 else 'Unknown'
                        
                        # Skip header rows
                        if company_name in ['Stock / IPO', 'Company Name', 'IPO Name']:
                            continue
                        
                        # Extract values
                        symbol = self._extract_symbol(company_name)
                        gmp_value = self._extract_number(gmp_text)
                        issue_price = self._extract_number(price_text)
                        listing_gain = self._extract_number(gain_text)
                        
                        # Store if we have valid data
                        if symbol and symbol != 'UNKNOWN':
                            gmp_data[symbol] = {
                                'company_name': company_name,
                                'symbol': symbol,
                                'gmp': f"₹{gmp_value}" if gmp_value else "₹0",
                                'gmp_value': gmp_value if gmp_value else 0,
                                'issue_price': f"₹{issue_price}" if issue_price else "₹0",
                                'issue_price_value': issue_price if issue_price else 0,
                                'estimated_listing_price': f"₹{(issue_price + gmp_value)}" if issue_price and gmp_value else "₹0",
                                'estimated_gain_percent': f"{listing_gain}%" if listing_gain else "0%",
                                'estimated_gain_value': listing_gain if listing_gain else 0,
                                'ipo_date': date_text,
                                'ipo_type': type_text,
                                'source': 'ipowatch',
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                    except Exception as e:
                        logger.warning(f"Error parsing row {i} in IPOWatch: {e}")
                        continue
            
            logger.info(f"Parsed {len(gmp_data)} IPOs from IPOWatch")
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error parsing IPOWatch data: {e}")
            return {}
    
    def _parse_investorgain_new(self, html: str) -> Dict[str, Dict]:
        """Parse InvestorGain GMP data"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            gmp_data = {}
            
            # Look for the specific table wrapper
            table_wrapper = soup.find('div', class_='table-responsive position-relative table-wrapper')
            
            if not table_wrapper:
                # Fallback to any table
                table_wrapper = soup.find('div', class_='table-responsive')
                logger.warning("table-responsive position-relative table-wrapper not found, using fallback")
            
            if not table_wrapper:
                return {}
            
            table = table_wrapper.find('table')
            if not table:
                return {}
            
            rows = table.find_all('tr')
            logger.info(f"Found {len(rows)} rows in InvestorGain table")
            
            # Process each row (skip header)
            for i, row in enumerate(rows[1:], 1):
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 8:  # At least 8 columns expected
                    try:
                        # Extract data based on column structure
                        company_name = cells[0].get_text(strip=True)
                        gmp_text = cells[1].get_text(strip=True)
                        rating_text = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                        sub_text = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                        gmp_range_text = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                        price_text = cells[5].get_text(strip=True) if len(cells) > 5 else ''
                        ipo_size_text = cells[6].get_text(strip=True) if len(cells) > 6 else ''
                        lot_text = cells[7].get_text(strip=True) if len(cells) > 7 else ''
                        open_date = cells[8].get_text(strip=True) if len(cells) > 8 else ''
                        close_date = cells[9].get_text(strip=True) if len(cells) > 9 else ''
                        boa_date = cells[10].get_text(strip=True) if len(cells) > 10 else ''
                        listing_date = cells[11].get_text(strip=True) if len(cells) > 11 else ''
                        updated_on = cells[12].get_text(strip=True) if len(cells) > 12 else ''
                        anchor = cells[13].get_text(strip=True) if len(cells) > 13 else ''
                        
                        # Skip header rows
                        if company_name in ['Name', 'Company Name', 'IPO Name']:
                            continue
                        
                        # Extract values
                        symbol = self._extract_symbol(company_name)
                        gmp_value = self._extract_number(gmp_text)
                        issue_price = self._extract_number(price_text)
                        gmp_percent = self._extract_percentage(gmp_text)
                        lot_size = self._extract_number(lot_text)
                        
                        # Store if we have valid data
                        if symbol and symbol != 'UNKNOWN':
                            gmp_data[symbol] = {
                                'company_name': company_name,
                                'symbol': symbol,
                                'gmp': f"₹{gmp_value}" if gmp_value else "₹--",
                                'gmp_value': gmp_value if gmp_value else 0,
                                'gmp_percent': f"{gmp_percent}%" if gmp_percent else "0%",
                                'gmp_percent_value': gmp_percent if gmp_percent else 0,
                                'rating': rating_text,
                                'subscription': sub_text,
                                'gmp_range': gmp_range_text,
                                'price': f"₹{issue_price}" if issue_price else "₹0",
                                'price_value': issue_price if issue_price else 0,
                                'ipo_size': ipo_size_text,
                                'lot_size': lot_size if lot_size else 0,
                                'open_date': open_date,
                                'close_date': close_date,
                                'boa_date': boa_date,
                                'listing_date': listing_date,
                                'updated_on': updated_on,
                                'anchor': anchor,
                                'estimated_listing_price': f"₹{(issue_price + gmp_value)}" if issue_price and gmp_value else "₹0",
                                'source': 'investorgain',
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                    except Exception as e:
                        logger.warning(f"Error parsing row {i} in InvestorGain: {e}")
                        continue
            
            logger.info(f"Parsed {len(gmp_data)} IPOs from InvestorGain")
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error parsing InvestorGain data: {e}")
            return {}
    
    def save_source_data(self, source_data: Dict) -> Dict:
        """Save scraped data from both sources separately"""
        try:
            from ..utils.file_storage import file_storage
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            saved_sources = []
            
            for source_name, source_info in source_data['sources'].items():
                if source_info['success'] and source_info['data']:
                    # Save individual source data
                    file_path = f"gmp/{source_name}/current-ipo-{current_date}.json"
                    file_storage.save_data(file_path, source_info['data'])
                    saved_sources.append(source_name)
                    logger.info(f"Saved {source_name} data to {file_path}")
            
            return {
                'success': True,
                'date': current_date,
                'saved_sources': saved_sources,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error saving source data: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_combined_gmp_data(self, date: Optional[str] = None) -> Dict:
        """Create combined GMP data from both sources - NO NSE dependency"""
        try:
            from ..utils.file_storage import file_storage
            
            target_date = date or datetime.now().strftime('%Y-%m-%d')
            
            # Load GMP data from both sources
            ipowatch_data = file_storage.load_data(f"gmp/ipowatch/current-ipo-{target_date}.json") or {}
            investorgain_data = file_storage.load_data(f"gmp/investorgain/current-ipo-{target_date}.json") or {}
            
            # Combine data - no duplicates
            combined_data = {}
            all_symbols = set(list(ipowatch_data.keys()) + list(investorgain_data.keys()))
            
            for symbol in all_symbols:
                # Priority: InvestorGain > IPOWatch (more detailed data)
                if symbol in investorgain_data:
                    combined_data[symbol] = investorgain_data[symbol].copy()
                    
                    # Add IPOWatch data as additional info if available
                    if symbol in ipowatch_data:
                        combined_data[symbol]['ipowatch_data'] = ipowatch_data[symbol]
                        combined_data[symbol]['available_in'] = ['investorgain', 'ipowatch']
                    else:
                        combined_data[symbol]['available_in'] = ['investorgain']
                
                elif symbol in ipowatch_data:
                    combined_data[symbol] = ipowatch_data[symbol].copy()
                    combined_data[symbol]['available_in'] = ['ipowatch']
            
            # Create final result
            final_result = {
                'date': target_date,
                'timestamp': datetime.now().isoformat(),
                'total_unique_ipos': len(combined_data),
                'source_counts': {
                    'ipowatch_total': len(ipowatch_data),
                    'investorgain_total': len(investorgain_data),
                    'combined_unique': len(combined_data)
                },
                'sources_available': [],
                'gmp_data': combined_data
            }
            
            # Track available sources
            if ipowatch_data:
                final_result['sources_available'].append('ipowatch')
            if investorgain_data:
                final_result['sources_available'].append('investorgain')
            
            # Save combined data
            file_storage.save_data(f"gmp-combined-{target_date}.json", final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error creating combined GMP data: {e}")
            return {
                'date': target_date,
                'error': str(e),
                'success': False
            }
    
    def fetch_current_gmp(self) -> Dict:
        """Fetch current GMP data from both sources and combine"""
        try:
            # Scrape both sources
            source_data = self.scrape_all_sources()
            
            if not source_data['success']:
                return source_data
            
            # Save source data separately
            save_result = self.save_source_data(source_data)
            
            # Create combined data
            combined_data = self.create_combined_gmp_data()
            
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'total_sources': len(source_data['sources']),
                'successful_sources': len([s for s in source_data['sources'].values() if s['success']]),
                'source_data': source_data,
                'save_result': save_result,
                'combined_data': combined_data,
                'period': 'current'
            }
            
        except Exception as e:
            logger.error(f"Error fetching current GMP: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_gmp_prediction(self, symbol: str, current_ipo_data: Dict, date: Optional[str] = None) -> Dict:
        """Get GMP data for symbol from combined data"""
        try:
            from ..utils.file_storage import file_storage
            symbol_upper = symbol.upper()
            target_date = date or datetime.now().strftime('%Y-%m-%d')
            
            # Load combined data for the date
            combined_data = file_storage.load_data(f'gmp-combined-{target_date}.json')
            
            if combined_data and symbol_upper in combined_data.get('gmp_data', {}):
                result = combined_data['gmp_data'][symbol_upper]
                result['has_data'] = True
                result['source'] = 'Combined GMP'
                result['date'] = target_date
                return result
            else:
                # Try to create fresh data if current date
                if not date or date == datetime.now().strftime('%Y-%m-%d'):
                    # Scrape fresh data
                    self.fetch_current_gmp()
                    
                    # Try loading again
                    combined_data = file_storage.load_data(f'gmp-combined-{target_date}.json')
                    if combined_data and symbol_upper in combined_data.get('gmp_data', {}):
                        result = combined_data['gmp_data'][symbol_upper]
                        result['has_data'] = True
                        result['source'] = 'Combined GMP'
                        result['date'] = target_date
                        return result
                
                return self._no_gmp_prediction(symbol)
            
        except Exception as e:
            logger.error(f"GMP prediction error for {symbol}: {e}")
            return self._no_gmp_prediction(symbol)
    
    def _no_gmp_prediction(self, symbol: str) -> Dict:
        """Return when no GMP data available"""
        return {
            'symbol': symbol,
            'source': 'Combined GMP',
            'has_data': False,
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_symbol(self, company_name: str) -> str:
        """Extract symbol from company name"""
        if not company_name:
            return 'UNKNOWN'
            
        # Remove common suffixes and extract symbol
        name = company_name.upper().strip()
        
        # Remove common words
        remove_words = ['LIMITED', 'LTD', 'PRIVATE', 'PVT', 'COMPANY', 'CORP', 'CORPORATION', 'INC', 'IPO']
        for word in remove_words:
            name = name.replace(word, '')
        
        # Clean and extract meaningful symbol
        name = re.sub(r'[^A-Z0-9\s]', '', name).strip()
        
        # Take first few words as symbol
        words = name.split()
        if len(words) >= 2:
            return ''.join(words[:2])[:12]  # Limit to 12 chars
        elif len(words) == 1:
            return words[0][:12]
        else:
            return 'UNKNOWN'
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text"""
        if not text or text.strip() in ['-', '', '₹-', '-%', '--', '₹--']:
            return None
        
        try:
            # Remove currency symbols and extra characters
            clean_text = re.sub(r'[₹%,\s]', '', text.strip())
            
            # Handle negative numbers
            if clean_text.startswith('-'):
                # Check if it's just a dash or actual negative
                if len(clean_text) > 1:
                    return -float(clean_text[1:])
                else:
                    return None
            
            # Extract number
            number_match = re.search(r'[\d.]+', clean_text)
            if number_match:
                return float(number_match.group())
            
            return None
            
        except Exception:
            return None
    
    def _extract_percentage(self, text: str) -> Optional[float]:
        """Extract percentage from text"""
        if not text:
            return None
        
        try:
            # Look for percentage in parentheses
            percent_match = re.search(r'\(([\d.-]+)%\)', text)
            if percent_match:
                return float(percent_match.group(1))
            
            # Look for standalone percentage
            percent_match = re.search(r'([\d.-]+)%', text)
            if percent_match:
                return float(percent_match.group(1))
            
            return None
            
        except Exception:
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'session'):
                self.session.close()
            logger.info("GMP service cleanup completed")
        except Exception as e:
            logger.error(f"GMP service cleanup error: {e}")

# Create service instance
gmp_service = GMPService()