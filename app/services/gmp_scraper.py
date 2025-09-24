# app/services/gmp_scraper.py
"""GMP Scraper - Grey Market Premium Data Extraction"""

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

class GMPScraper:
    """GMP Scraper for extracting Grey Market Premium data"""
    
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
        
        # GMP Sources
        self.sources = {
            'ipowatch': {
                'url': 'https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/',
                'backup': 'https://ipowatch.in/live-ipo-gmp-today/',
                'parser': self._parse_ipowatch
            },
            'investorgain': {
                'url': 'https://www.investorgain.com/report/live-ipo-gmp/331/',
                'backup': 'https://www.investorgain.com/report/live-ipo-gmp/331/ipo/',
                'parser': self._parse_investorgain
            },
            'chittorgarh': {
                'url': 'https://www.chittorgarh.com/ipo_grey_market_premium.asp',
                'backup': 'https://www.chittorgarh.com/ipo/',
                'parser': self._parse_chittorgarh
            }
        }
    
    def scrape_gmp_data(self) -> Dict[str, Any]:
        """Scrape GMP data from multiple sources"""
        gmp_data = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'sources_scraped': [],
            'total_ipos': 0,
            'data': {},
            'errors': []
        }
        
        for source_name, source_config in self.sources.items():
            try:
                logger.info(f"Scraping GMP data from {source_name}...")
                
                # Try primary URL first
                data = self._scrape_source(source_config['url'], source_config['parser'])
                
                # Try backup URL if primary fails
                if not data:
                    logger.warning(f"Primary URL failed for {source_name}, trying backup...")
                    data = self._scrape_source(source_config['backup'], source_config['parser'])
                
                if data:
                    gmp_data['sources_scraped'].append(source_name)
                    for symbol, ipo_gmp in data.items():
                        if symbol not in gmp_data['data']:
                            gmp_data['data'][symbol] = {
                                'symbol': symbol,
                                'sources': {},
                                'consensus_gmp': 0,
                                'consensus_gain': 0,
                                'reliability_score': 0
                            }
                        
                        gmp_data['data'][symbol]['sources'][source_name] = ipo_gmp
                    
                    logger.info(f"Successfully scraped {len(data)} IPOs from {source_name}")
                else:
                    logger.error(f"Failed to scrape data from {source_name}")
                    gmp_data['errors'].append(f"Failed to scrape {source_name}")
                
                # Rate limiting
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {e}")
                gmp_data['errors'].append(f"{source_name}: {str(e)}")
        
        # Calculate consensus GMP
        self._calculate_consensus_gmp(gmp_data['data'])
        gmp_data['total_ipos'] = len(gmp_data['data'])
        
        return gmp_data
    
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
            
            # Look for tables with GMP data
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # Check if this is the GMP table by looking at headers
                header_row = rows[0]
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                
                # Look for GMP-related headers
                gmp_indicators = ['gmp', 'premium', 'grey', 'market', 'gain', 'listing']
                if any(indicator in ' '.join(headers) for indicator in gmp_indicators):
                    
                    # Process data rows
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 4:
                            try:
                                company_name = cells[0].get_text(strip=True)
                                gmp_text = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                                price_text = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                                gain_text = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                                
                                # Extract symbol from company name
                                symbol = self._extract_symbol(company_name)
                                
                                # Extract numeric values
                                gmp_value = self._extract_number(gmp_text)
                                issue_price = self._extract_number(price_text)
                                listing_gain = self._extract_number(gain_text)
                                
                                # Store if we have valid data
                                if symbol and gmp_value is not None:
                                    gmp_data[symbol] = {
                                        'company_name': company_name,
                                        'symbol': symbol,
                                        'gmp': gmp_value,
                                        'issue_price': issue_price if issue_price else 0,
                                        'estimated_listing_price': (issue_price + gmp_value) if issue_price and gmp_value else 0,
                                        'estimated_gain_percent': listing_gain if listing_gain else 0,
                                        'source': 'ipowatch',
                                        'scraped_at': datetime.now().isoformat()
                                    }
                                    
                            except Exception as e:
                                logger.warning(f"Error parsing row in IPOWatch: {e}")
                                continue
            
            # If no data found in tables, try alternative parsing
            if not gmp_data:
                gmp_data = self._parse_ipowatch_alternative(soup)
            
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error parsing IPOWatch data: {e}")
            return {}
    
    def _parse_ipowatch_alternative(self, soup) -> Dict[str, Dict]:
        """Alternative parsing method for IPOWatch"""
        try:
            gmp_data = {}
            
            # Look for div containers or other structures
            containers = soup.find_all(['div', 'section'], class_=lambda x: x and ('gmp' in x.lower() or 'ipo' in x.lower()))
            
            for container in containers:
                # Look for text patterns that match GMP data
                text_content = container.get_text()
                
                # Pattern: Company Name GMP: ₹X Gain: Y%
                gmp_pattern = r'([A-Z][A-Za-z\s&]+?)\s+GMP[:\s]+₹?(\d+)\s+.*?(\d+\.?\d*)%'
                matches = re.findall(gmp_pattern, text_content)
                
                for match in matches:
                    company_name, gmp_value, gain_percent = match
                    symbol = self._extract_symbol(company_name.strip())
                    
                    if symbol:
                        gmp_data[symbol] = {
                            'company_name': company_name.strip(),
                            'symbol': symbol,
                            'gmp': float(gmp_value),
                            'issue_price': 0,
                            'estimated_listing_price': 0,
                            'estimated_gain_percent': float(gain_percent),
                            'source': 'ipowatch',
                            'scraped_at': datetime.now().isoformat()
                        }
            
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error in alternative IPOWatch parsing: {e}")
            return {}
    
    def _parse_investorgain(self, html: str) -> Dict[str, Dict]:
        """Parse InvestorGain GMP data"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            gmp_data = {}
            
            # Look for GMP table
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # Process rows
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 5:
                        try:
                            company_name = cells[0].get_text(strip=True)
                            issue_price_text = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                            gmp_text = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                            estimated_price_text = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                            gain_text = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                            
                            symbol = self._extract_symbol(company_name)
                            gmp_value = self._extract_number(gmp_text)
                            issue_price = self._extract_number(issue_price_text)
                            estimated_price = self._extract_number(estimated_price_text)
                            listing_gain = self._extract_number(gain_text)
                            
                            if symbol and gmp_value is not None:
                                gmp_data[symbol] = {
                                    'company_name': company_name,
                                    'symbol': symbol,
                                    'gmp': gmp_value,
                                    'issue_price': issue_price if issue_price else 0,
                                    'estimated_listing_price': estimated_price if estimated_price else 0,
                                    'estimated_gain_percent': listing_gain if listing_gain else 0,
                                    'source': 'investorgain',
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                        except Exception as e:
                            logger.warning(f"Error parsing row in InvestorGain: {e}")
                            continue
            
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error parsing InvestorGain data: {e}")
            return {}
    
    def _parse_chittorgarh(self, html: str) -> Dict[str, Dict]:
        """Parse Chittorgarh GMP data"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            gmp_data = {}
            
            # Look for GMP data in tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 4:
                        try:
                            company_name = cells[0].get_text(strip=True)
                            price_band = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                            gmp_text = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                            estimated_text = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                            gain_text = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                            
                            symbol = self._extract_symbol(company_name)
                            gmp_value = self._extract_number(gmp_text)
                            issue_price = self._extract_max_price(price_band)
                            estimated_price = self._extract_number(estimated_text)
                            listing_gain = self._extract_number(gain_text)
                            
                            if symbol and gmp_value is not None:
                                gmp_data[symbol] = {
                                    'company_name': company_name,
                                    'symbol': symbol,
                                    'gmp': gmp_value,
                                    'issue_price': issue_price if issue_price else 0,
                                    'estimated_listing_price': estimated_price if estimated_price else 0,
                                    'estimated_gain_percent': listing_gain if listing_gain else 0,
                                    'source': 'chittorgarh',
                                    'scraped_at': datetime.now().isoformat()
                                }
                                
                        except Exception as e:
                            logger.warning(f"Error parsing row in Chittorgarh: {e}")
                            continue
            
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error parsing Chittorgarh data: {e}")
            return {}
    
    def _extract_symbol(self, company_name: str) -> str:
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
            return ''.join(words[:2])[:10]
        elif len(words) == 1:
            return words[0][:10]
        else:
            return 'UNKNOWN'
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text"""
        if not text or text.strip() == '-' or text.strip() == '':
            return None
        
        try:
            # Remove currency symbols and extra characters
            clean_text = re.sub(r'[₹%,\s]', '', text.strip())
            
            # Handle negative numbers
            if clean_text.startswith('-'):
                return -float(clean_text[1:])
            
            # Extract number
            number_match = re.search(r'[\d.]+', clean_text)
            if number_match:
                return float(number_match.group())
            
            return None
            
        except Exception:
            return None
    
    def _extract_max_price(self, price_band: str) -> Optional[float]:
        """Extract maximum price from price band (e.g., '100-120' -> 120)"""
        if not price_band:
            return None
        
        try:
            # Look for price range pattern
            prices = re.findall(r'[\d.]+', price_band)
            if len(prices) >= 2:
                return float(prices[-1])  # Return max price
            elif len(prices) == 1:
                return float(prices[0])
            
            return None
            
        except Exception:
            return None
    
    def _calculate_consensus_gmp(self, gmp_data: Dict):
        """Calculate consensus GMP from multiple sources"""
        for symbol, data in gmp_data.items():
            sources = data['sources']
            
            if len(sources) == 0:
                continue
            
            # Calculate weighted average GMP
            gmp_values = []
            gains = []
            
            for source_name, source_data in sources.items():
                if source_data.get('gmp') is not None:
                    gmp_values.append(source_data['gmp'])
                
                if source_data.get('estimated_gain_percent') is not None:
                    gains.append(source_data['estimated_gain_percent'])
            
            # Calculate consensus
            if gmp_values:
                data['consensus_gmp'] = round(sum(gmp_values) / len(gmp_values), 2)
            
            if gains:
                data['consensus_gain'] = round(sum(gains) / len(gains), 2)
            
            # Calculate reliability score based on number of sources and consistency
            data['reliability_score'] = self._calculate_reliability_score(sources, gmp_values)
    
    def _calculate_reliability_score(self, sources: Dict, gmp_values: List[float]) -> int:
        """Calculate reliability score based on sources and consistency"""
        try:
            # Base score from number of sources
            base_score = min(len(sources) * 25, 100)  # Max 100 for 4+ sources
            
            # Consistency bonus
            if len(gmp_values) > 1:
                # Calculate standard deviation
                mean_gmp = sum(gmp_values) / len(gmp_values)
                variance = sum((x - mean_gmp) ** 2 for x in gmp_values) / len(gmp_values)
                std_dev = variance ** 0.5
                
                # Lower standard deviation means higher consistency
                if mean_gmp > 0:
                    consistency_factor = max(0.5, 1 - (std_dev / mean_gmp))
                    base_score *= consistency_factor
            
            return min(100, max(0, int(base_score)))
            
        except Exception:
            return min(len(sources) * 20, 80)  # Fallback calculation
    
    def get_cached_gmp_data(self) -> Optional[Dict]:
        """Get cached GMP data if available and recent"""
        try:
            from ..utils.file_storage import file_storage
            
            # Try to load recent GMP data
            gmp_data = file_storage.load_data('latest_gmp_data')
            
            if gmp_data and 'data' in gmp_data:
                # Check if data is recent (within last 2 hours)
                timestamp_str = gmp_data['data'].get('timestamp', '')
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                    
                    if age_hours < 2:  # Use cached data if less than 2 hours old
                        logger.info("Using cached GMP data")
                        return gmp_data['data']
            
            return None
            
        except Exception as e:
            logger.warning(f"Error loading cached GMP data: {e}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, 'session'):
                self.session.close()
            logger.info("GMP scraper cleanup completed")
        except Exception as e:
            logger.error(f"GMP scraper cleanup error: {e}")

# Create scraper instance
gmp_scraper = GMPScraper()