# app/services/gmp_service.py
import cloudscraper
import time
import random
from datetime import datetime
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class GMPService:
    """GMP Service - Business Logic for Grey Market Premium Data"""
    
    def __init__(self):
        # CloudScraper for bypassing protection
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        
        # GMP data sources
        self.sources = [
            {
                'name': 'IPOWatch',
                'url': 'https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/',
                'parser': self._parse_ipowatch
            },
            {
                'name': 'Chittorgarh',
                'url': 'https://www.chittorgarh.com/ipo_grey_market_premium.asp',
                'parser': self._parse_chittorgarh
            }
        ]
        
        # Headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
    
    def fetch_gmp_data(self) -> List[Dict]:
        """Business logic: Fetch GMP data from multiple sources"""
        logger.info("💰 Fetching GMP data...")
        
        all_gmp_data = []
        
        for source in self.sources:
            try:
                logger.info(f"📊 Fetching from {source['name']}...")
                
                # Make request
                html_content = self._make_request(source['url'])
                
                if html_content:
                    # Parse data
                    parsed_data = source['parser'](html_content)
                    all_gmp_data.extend(parsed_data)
                    logger.info(f"✅ Got {len(parsed_data)} records from {source['name']}")
                    
                    # Delay between sources
                    time.sleep(random.uniform(1, 2))
                else:
                    logger.warning(f"⚠️ No data from {source['name']}")
                    
            except Exception as e:
                logger.error(f"❌ Error fetching from {source['name']}: {e}")
                continue
        
        # Merge and deduplicate
        merged_data = self._merge_data(all_gmp_data)
        
        logger.info(f"🎯 Final GMP records: {len(merged_data)}")
        return merged_data
    
    def _make_request(self, url: str) -> Optional[str]:
        """Make HTTP request to GMP source"""
        try:
            self.scraper.headers.update(self.headers)
            
            # Random delay
            time.sleep(random.uniform(1, 3))
            
            response = self.scraper.get(url, timeout=20)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"⚠️ Request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Request error: {e}")
            return None
    
    def _parse_ipowatch(self, html_content: str) -> List[Dict]:
        """Parse IPOWatch GMP data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            gmp_data = []
            
            # Find tables with GMP data
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                # Process data rows (skip header)
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 4:
                        try:
                            company_name = self._clean_text(cells[0].get_text())
                            gmp_text = self._clean_text(cells[1].get_text())
                            price_range = self._clean_text(cells[2].get_text())
                            listing_gain = self._clean_text(cells[3].get_text())
                            
                            # Extract numeric values
                            gmp_value = self._extract_number(gmp_text)
                            listing_gain_value = self._extract_number(listing_gain)
                            
                            if company_name and gmp_value is not None:
                                gmp_data.append({
                                    'company_name': company_name,
                                    'gmp': gmp_value,
                                    'price_range': price_range,
                                    'estimated_listing_gain': listing_gain_value,
                                    'source': 'IPOWatch',
                                    'last_updated': datetime.now().isoformat()
                                })
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Error parsing IPOWatch row: {e}")
                            continue
            
            return gmp_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing IPOWatch: {e}")
            return []
    
    def _parse_chittorgarh(self, html_content: str) -> List[Dict]:
        """Parse Chittorgarh GMP data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            gmp_data = []
            
            # Find GMP tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 5:
                        try:
                            company_name = self._clean_text(cells[0].get_text())
                            price_band = self._clean_text(cells[1].get_text())
                            gmp_text = self._clean_text(cells[2].get_text())
                            estimated_listing = self._clean_text(cells[3].get_text())
                            
                            gmp_value = self._extract_number(gmp_text)
                            listing_value = self._extract_number(estimated_listing)
                            
                            if company_name and gmp_value is not None:
                                gmp_data.append({
                                    'company_name': company_name,
                                    'gmp': gmp_value,
                                    'price_range': price_band,
                                    'estimated_listing_gain': listing_value,
                                    'source': 'Chittorgarh',
                                    'last_updated': datetime.now().isoformat()
                                })
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Error parsing Chittorgarh row: {e}")
                            continue
            
            return gmp_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing Chittorgarh: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean text data"""
        if not text:
            return ""
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', str(text).strip())
        return cleaned.replace('\n', '').replace('\r', '')
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text"""
        if not text:
            return None
        
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[₹,%\s]', '', str(text))
        
        # Extract number including negative values
        match = re.search(r'[-+]?[\d.]+', cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None
    
    def _merge_data(self, gmp_data: List[Dict]) -> List[Dict]:
        """Merge and deduplicate GMP data"""
        merged = {}
        
        for item in gmp_data:
            company_name = item.get('company_name', '').strip().upper()
            
            # Clean company name for matching
            clean_name = re.sub(r'(LIMITED|LTD|PVT|PRIVATE|\.|,|\s+)', '', company_name).strip()
            
            if clean_name in merged:
                # Merge data from multiple sources
                existing = merged[clean_name]
                
                # Average GMP if multiple sources
                if existing.get('gmp') and item.get('gmp'):
                    existing['gmp'] = round((existing['gmp'] + item['gmp']) / 2, 2)
                elif item.get('gmp'):
                    existing['gmp'] = item['gmp']
                
                # Combine sources
                sources = existing.get('sources', [])
                if item.get('source') and item['source'] not in sources:
                    sources.append(item['source'])
                existing['sources'] = sources
                
                # Update other fields if missing
                for key in ['price_range', 'estimated_listing_gain']:
                    if not existing.get(key) and item.get(key):
                        existing[key] = item[key]
            else:
                # New entry
                item['sources'] = [item.get('source', 'Unknown')]
                merged[clean_name] = item
        
        return list(merged.values())

# Create service instance
gmp_service = GMPService()