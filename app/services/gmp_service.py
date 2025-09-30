# app/services/gmp_service.py - COMPLETE FIXED VERSION

import requests
import json
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
import time
import random

logger = logging.getLogger(__name__)

class GMPService:
    """Fixed GMP Service - Correct storage in data/predictions/gmp/"""
    
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
        
        # GMP sources
        self.sources = {
            'ipowatch': {
                'url': 'https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/',
                'backup': 'https://ipowatch.in/live-ipo-gmp-today/',
                'parser': self._parse_ipowatch_corrected
            },
            'investorgain': {
                'url': 'https://www.investorgain.com/report/live-ipo-gmp/331/all/',
                'backup': 'https://www.investorgain.com/report/live-ipo-gmp/331/ipo/',
                'parser': self._parse_investorgain_corrected
            }
        }
    
    def fetch_current_gmp(self) -> Dict:
        """Fetch GMP data for CURRENT IPOs only - FIXED STORAGE"""
        try:
            logger.info("Starting GMP data scraping for current IPOs...")
            
            # First get current IPOs list
            current_ipos = self._get_current_ipos_from_storage(datetime.now().strftime('%Y-%m-%d'))
            
            if not current_ipos:
                return {
                    'success': False,
                    'message': 'No current IPOs found - cannot filter GMP data',
                    'timestamp': datetime.now().isoformat()
                }
            
            logger.info(f"Current IPOs found: {[(ipo.get('symbol'), ipo.get('company_name')) for ipo in current_ipos]}")
            
            # Scrape all sources
            scrape_result = self.scrape_all_sources()
            
            if scrape_result['success_count'] == 0:
                return {
                    'success': False,
                    'message': 'Failed to scrape GMP data from any source',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Filter scraped data for current IPOs
            filtered_result = self._filter_for_current_ipos_simple(scrape_result, current_ipos)
            
            # FIXED: Save to data/predictions/gmp/ instead of data/gmp_current/
            from ..utils.file_storage import file_storage
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Use correct path: predictions/gmp
            save_success = file_storage.save_data("predictions/gmp", filtered_result, current_date)
            
            if save_success:
                total_filtered = sum(len(source.get('data', [])) for source in filtered_result['sources'].values() if source.get('success'))
                logger.info(f"✅ GMP data saved to data/predictions/gmp/{current_date}.json")
                return {
                    'success': True,
                    'timestamp': filtered_result['timestamp'],
                    'total_sources': filtered_result['total_sources'],
                    'successful_sources': filtered_result['success_count'],
                    'current_ipos_count': len(current_ipos),
                    'matched_gmp_entries': total_filtered,
                    'message': f'Found GMP data for {total_filtered} entries from current IPOs',
                    'storage_path': f'data/predictions/gmp/{current_date}.json'
                }
            else:
                return {
                    'success': False,
                    'message': 'Failed to save filtered GMP data',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"GMP scraping error: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'GMP data scraping failed',
                'timestamp': datetime.now().isoformat()
            }
    
    def get_current_predictions(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Get all current IPOs with their GMP data - FIXED LOADING PATH"""
        try:
            from ..utils.file_storage import file_storage
            
            current_date = target_date or datetime.now().strftime('%Y-%m-%d')
            
            # Get current IPOs from stored NSE data
            current_ipos = self._get_current_ipos_from_storage(current_date)
            
            if not current_ipos:
                return {
                    'success': False,
                    'message': 'No current IPOs found in stored data',
                    'error_code': 'NO_CURRENT_IPOS'
                }
            
            # FIXED: Load from data/predictions/gmp/ instead of data/gmp_current/
            gmp_filtered = file_storage.load_data("predictions/gmp", current_date)
            
            if not gmp_filtered:
                return {
                    'success': False,
                    'message': 'No GMP data found. Please fetch GMP data first.',
                    'error_code': 'NO_GMP_DATA',
                    'expected_path': f'data/predictions/gmp/{current_date}.json'
                }
            
            # Match all current IPOs with GMP data
            predictions = {}
            
            for ipo in current_ipos:
                symbol = ipo.get('symbol', '')
                
                # Find matching GMP data
                gmp_match = self._find_gmp_for_symbol_simple(symbol, ipo.get('company_name', ''), gmp_filtered)
                
                # Store IPO data with matched GMP info
                predictions[symbol] = {
                    'symbol': symbol,
                    'company_name': ipo.get('company_name', ''),
                    'issue_price': ipo.get('issue_price', ''),
                    'issue_start_date': ipo.get('issue_start_date', ''),
                    'issue_end_date': ipo.get('issue_end_date', ''),
                    'subscription_times': ipo.get('subscription_times', 0),
                    'status': ipo.get('status', ''),
                    'gmp_data': gmp_match,
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'success': True,
                'date': current_date,
                'total_current_ipos': len(current_ipos),
                'predictions': predictions,
                'timestamp': datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Current predictions error: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'RETRIEVAL_FAILED'
            }
    
    def get_symbol_prediction(self, symbol: str, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Get prediction for specific symbol"""
        try:
            current_date = target_date or datetime.now().strftime('%Y-%m-%d')
            symbol_upper = symbol.upper()
            
            # Get all current predictions
            current_predictions = self.get_current_predictions(current_date)
            
            if not current_predictions.get('success'):
                return {
                    'success': False,
                    'symbol': symbol_upper,
                    'message': current_predictions.get('message', 'Failed to get current predictions'),
                    'error_code': current_predictions.get('error_code', 'PREDICTION_FAILED')
                }
            
            predictions = current_predictions.get('predictions', {})
            
            if symbol_upper in predictions:
                return {
                    'success': True,
                    'data': predictions[symbol_upper]
                }
            else:
                return {
                    'success': False,
                    'symbol': symbol_upper,
                    'message': f'Symbol {symbol_upper} not found in current IPOs',
                    'error_code': 'SYMBOL_NOT_FOUND',
                    'available_symbols': list(predictions.keys())[:10]
                }
                
        except Exception as e:
            logger.error(f"Symbol prediction error for {symbol}: {e}")
            return {
                'success': False,
                'symbol': symbol.upper(),
                'error': str(e),
                'error_code': 'RETRIEVAL_FAILED'
            }
    
    def _create_matching_map(self, current_ipos: List[Dict]) -> Dict[str, Dict]:
        """Create a mapping of various name formats to IPO data"""
        matching_map = {}
        
        for ipo in current_ipos:
            symbol = ipo.get('symbol', '').upper()
            company_name = ipo.get('company_name', '')
            
            matching_data = {
                'symbol': symbol,
                'company_name': company_name,
                'ipo_data': ipo
            }
            
            # Add various matching keys
            matching_map[symbol] = matching_data
            
            first_word = company_name.split()[0].upper() if company_name else ""
            if first_word and len(first_word) > 2:
                matching_map[first_word] = matching_data
            
            clean_name = company_name.replace('Limited', '').replace('Ltd', '').strip()
            if clean_name:
                first_clean_word = clean_name.split()[0].upper()
                if first_clean_word and len(first_clean_word) > 2:
                    matching_map[first_clean_word] = matching_data
        
        return matching_map
    
    def _match_gmp_to_ipo(self, gmp_company_name: str, matching_map: Dict[str, Dict]) -> Optional[str]:
        """Match a GMP company name to an IPO symbol"""
        gmp_upper = gmp_company_name.upper()
        
        for key, data in matching_map.items():
            symbol = data['symbol']
            gmp_clean = gmp_upper.replace(' ', '').replace('-', '').replace('_', '')
            if symbol in gmp_clean:
                return symbol
        
        gmp_first_word = gmp_company_name.split()[0].upper() if gmp_company_name else ""
        if gmp_first_word in matching_map:
            return matching_map[gmp_first_word]['symbol']
        
        gmp_main = gmp_company_name.split('Limited')[0].split('Ltd')[0].strip()
        gmp_main_upper = gmp_main.upper()
        
        for key, data in matching_map.items():
            if key in gmp_main_upper:
                return data['symbol']
            
            ipo_name_upper = data['company_name'].upper()
            if gmp_main_upper in ipo_name_upper or ipo_name_upper in gmp_main_upper:
                return data['symbol']
        
        return None
    
    def _filter_for_current_ipos_simple(self, scrape_result: Dict, current_ipos: List[Dict]) -> Dict:
        """Filter scraped GMP data for current IPOs"""
        filtered_result = {
            'timestamp': scrape_result['timestamp'],
            'sources': {},
            'success_count': 0,
            'total_sources': scrape_result['total_sources']
        }
        
        matching_map = self._create_matching_map(current_ipos)
        
        logger.info(f"Created matching map with {len(matching_map)} keys")
        
        for source_name, source_data in scrape_result['sources'].items():
            filtered_entries = []
            
            if source_data.get('success') and source_data.get('data'):
                logger.info(f"Processing {source_name} with {len(source_data['data'])} entries")
                
                for gmp_entry in source_data['data']:
                    company_name = gmp_entry.get('company_name', '')
                    matched_symbol = self._match_gmp_to_ipo(company_name, matching_map)
                    
                    if matched_symbol:
                        gmp_entry['matched_symbol'] = matched_symbol
                        filtered_entries.append(gmp_entry)
                        logger.info(f"✓ Matched: {company_name} => {matched_symbol}")
                
                filtered_result['sources'][source_name] = {
                    'success': True,
                    'count': len(filtered_entries),
                    'data': filtered_entries,
                    'url': source_data.get('url', ''),
                    'original_count': len(source_data.get('data', []))
                }
                
                if len(filtered_entries) > 0:
                    filtered_result['success_count'] += 1
                    
                logger.info(f"{source_name}: Filtered {len(filtered_entries)} from {len(source_data.get('data', []))} entries")
            else:
                filtered_result['sources'][source_name] = source_data
        
        return filtered_result
    
    def _find_gmp_for_symbol_simple(self, symbol: str, company_name: str, gmp_filtered: Dict) -> Dict:
        """Search for GMP data for a symbol"""
        try:
            symbol_upper = symbol.upper()
            
            if 'data' in gmp_filtered:
                gmp_data = gmp_filtered['data']
                
                if 'sources' in gmp_data:
                    for source_name, source_data in gmp_data.get('sources', {}).items():
                        if source_data.get('success') and source_data.get('data'):
                            for gmp_item in source_data['data']:
                                if gmp_item.get('matched_symbol') == symbol_upper:
                                    return {
                                        'found': True,
                                        'source': source_name,
                                        'match_type': 'symbol_match',
                                        'company_match': gmp_item.get('company_name'),
                                        'gmp': gmp_item.get('gmp'),
                                        'gmp_text': gmp_item.get('gmp_text', gmp_item.get('gmp')),
                                        'ipo_price': gmp_item.get('ipo_price'),
                                        'listing_gain_percent': gmp_item.get('listing_gain_percent'),
                                        'listing_gain': gmp_item.get('listing_gain'),
                                        'gmp_raw_data': gmp_item
                                    }
            
            elif 'sources' in gmp_filtered:
                for source_name, source_data in gmp_filtered.get('sources', {}).items():
                    if source_data.get('success') and source_data.get('data'):
                        for gmp_item in source_data['data']:
                            if gmp_item.get('matched_symbol') == symbol_upper:
                                return {
                                    'found': True,
                                    'source': source_name,
                                    'match_type': 'symbol_match',
                                    'company_match': gmp_item.get('company_name'),
                                    'gmp': gmp_item.get('gmp'),
                                    'gmp_text': gmp_item.get('gmp_text', gmp_item.get('gmp')),
                                    'ipo_price': gmp_item.get('ipo_price'),
                                    'listing_gain_percent': gmp_item.get('listing_gain_percent'),
                                    'listing_gain': gmp_item.get('listing_gain'),
                                    'gmp_raw_data': gmp_item
                                }
            
            return {
                'found': False,
                'message': f'No GMP data found for {symbol} ({company_name})'
            }
            
        except Exception as e:
            logger.error(f"Error finding GMP for symbol {symbol}: {e}")
            return {
                'found': False,
                'error': str(e)
            }
    
    def _get_current_ipos_from_storage(self, date: str) -> List[Dict]:
        """Get current IPOs from stored NSE data"""
        try:
            from ..utils.file_storage import file_storage
            
            logger.info(f"Loading current IPOs for date: {date}")
            stored_data = file_storage.load_data("nse/current", date)
            
            if not stored_data:
                logger.error(f"No stored data found for nse/current/{date}")
                return []
            
            if stored_data and stored_data.get('data'):
                all_ipos = stored_data['data']
                logger.info(f"Total IPOs found: {len(all_ipos)}")
                
                current_ipos = [
                    ipo for ipo in all_ipos 
                    if ipo.get('status', '').lower() == 'active'
                ]
                
                logger.info(f"Active IPOs found: {len(current_ipos)}")
                return current_ipos
            else:
                logger.error("No 'data' key found in stored file")
                return []
            
        except Exception as e:
            logger.error(f"Error loading current IPOs: {e}")
            return []
    
    def scrape_all_sources(self) -> Dict[str, Any]:
        """Scrape data from all GMP sources"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'success_count': 0,
            'total_sources': len(self.sources)
        }
        
        for source_name, source_config in self.sources.items():
            try:
                logger.info(f"Scraping {source_name}...")
                html_content = self._make_request(source_config['url'])
                
                if not html_content and 'backup' in source_config:
                    logger.info(f"Trying backup URL for {source_name}")
                    html_content = self._make_request(source_config['backup'])
                
                if html_content:
                    parsed_data = source_config['parser'](html_content)
                    
                    results['sources'][source_name] = {
                        'success': True,
                        'count': len(parsed_data),
                        'data': parsed_data,
                        'url': source_config['url']
                    }
                    results['success_count'] += 1
                    logger.info(f"Success {source_name}: {len(parsed_data)} entries")
                else:
                    results['sources'][source_name] = {
                        'success': False,
                        'error': 'Failed to fetch data',
                        'url': source_config['url']
                    }
                    logger.error(f"Failed {source_name}: No HTML content")
                    
            except Exception as e:
                results['sources'][source_name] = {
                    'success': False,
                    'error': str(e),
                    'url': source_config.get('url', 'unknown')
                }
                logger.error(f"Error {source_name}: {e}")
        
        return results
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Make HTTP request with retries"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    time.sleep(random.uniform(2, 5))
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"Request failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Request error (attempt {attempt + 1}): {e}")
                time.sleep(random.uniform(3, 6))
        
        return None
    
    def _parse_ipowatch_corrected(self, html_content: str) -> List[Dict]:
        """Parse IPOWatch data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            gmp_data = []
            tables = soup.find_all('table')
            
            for table in tables:
                header_row = table.find('tr')
                if not header_row:
                    continue
                
                header_cells = header_row.find_all(['th', 'td'])
                if len(header_cells) >= 5:
                    header_texts = [cell.get_text(strip=True) for cell in header_cells]
                    
                    if any('GMP' in text for text in header_texts):
                        rows = table.find_all('tr')[1:]
                        
                        for row in rows:
                            cells = row.find_all(['td'])
                            if len(cells) < 5:
                                continue
                            
                            try:
                                cell_texts = [cell.get_text(strip=True) for cell in cells]
                                company_name = cell_texts[0] if len(cell_texts) > 0 else ""
                                
                                if not company_name or len(company_name) < 3:
                                    continue
                                
                                gmp_text = cell_texts[1] if len(cell_texts) > 1 else ""
                                ipo_price = cell_texts[2] if len(cell_texts) > 2 else ""
                                listing_gain = cell_texts[3] if len(cell_texts) > 3 else ""
                                
                                gmp_value = self._extract_numeric_value(gmp_text)
                                price_value = self._extract_numeric_value(ipo_price)
                                gain_value = self._extract_percentage(listing_gain)
                                
                                if gmp_text and (gmp_text.startswith('₹') or gmp_text == '-'):
                                    entry = {
                                        'company_name': company_name,
                                        'gmp': gmp_value,
                                        'gmp_text': gmp_text,
                                        'ipo_price': price_value,
                                        'listing_gain_percent': listing_gain,
                                        'listing_gain': gain_value,
                                        'source': 'ipowatch'
                                    }
                                    gmp_data.append(entry)
                                    
                            except Exception as e:
                                continue
                        
                        if gmp_data:
                            break
            
            logger.info(f"IPOWatch: Successfully parsed {len(gmp_data)} entries")
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error parsing IPOWatch data: {e}")
            return []
    
    def _parse_investorgain_corrected(self, html_content: str) -> List[Dict]:
        """Parse InvestorGain data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            gmp_data = []
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                header_row = rows[0]
                header_text = header_row.get_text(strip=True).lower()
                
                if 'gmp' in header_text or 'name' in header_text:
                    for row in rows[1:]:
                        cells = row.find_all(['td'])
                        if len(cells) < 2:
                            continue
                        
                        try:
                            cell_texts = []
                            for cell in cells:
                                text = cell.get_text(strip=True)
                                text = re.sub(r'[🔥❌✅▲▼→↑]', '', text)
                                text = re.sub(r'\s+', ' ', text).strip()
                                cell_texts.append(text)
                            
                            company_name = cell_texts[0] if len(cell_texts) > 0 else ""
                            company_name = re.sub(r'\s*(IPO|BSE|SME|U)\s*$', '', company_name).strip()
                            
                            if not company_name or len(company_name) < 3:
                                continue
                            
                            gmp_text = cell_texts[1] if len(cell_texts) > 1 else ""
                            price = cell_texts[5] if len(cell_texts) > 5 else ""
                            
                            gmp_value = self._extract_numeric_value(gmp_text)
                            price_value = self._extract_numeric_value(price)
                            
                            if gmp_text and gmp_text != '--':
                                entry = {
                                    'company_name': company_name,
                                    'gmp': gmp_value,
                                    'gmp_text': gmp_text,
                                    'price': price_value,
                                    'source': 'investorgain'
                                }
                                gmp_data.append(entry)
                                
                        except Exception as e:
                            continue
                    
                    if gmp_data:
                        break
            
            logger.info(f"InvestorGain: Successfully parsed {len(gmp_data)} entries")
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error parsing InvestorGain data: {e}")
            return []
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract numeric value from text"""
        try:
            if not text or text == '-' or text == '--':
                return None
            
            cleaned = text.replace('₹', '').replace(',', '').strip()
            
            if '(' in cleaned and ')' in cleaned:
                cleaned = re.sub(r'\([^)]*\)', '', cleaned).strip()
            
            if not cleaned or cleaned == '-':
                return None
            
            match = re.search(r'[-+]?\d*\.?\d+', cleaned)
            if match:
                return float(match.group())
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting numeric value from '{text}': {e}")
            return None
    
    def _extract_percentage(self, text: str) -> Optional[float]:
        """Extract percentage value from text"""
        try:
            if not text or text == '-' or text == '-%':
                return None
            
            cleaned = text.replace('%', '').strip()
            match = re.search(r'[-+]?\d*\.?\d+', cleaned)
            if match:
                return float(match.group())
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting percentage from '{text}': {e}")
            return None

# Create service instance
gmp_service = GMPService()