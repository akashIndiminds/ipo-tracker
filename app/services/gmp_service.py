import requests
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
from bs4 import BeautifulSoup
import re
import cloudscraper

logger = logging.getLogger(__name__)

class GMPService:
    """Gray Market Premium tracking service"""
    
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # GMP data sources
        self.gmp_sources = [
            {
                'name': 'IPO Central',
                'url': 'https://ipocentral.in/ipo-gmp/',
                'parser': self._parse_ipocentral_gmp
            },
            {
                'name': 'Chittorgarh',
                'url': 'https://www.chittorgarh.com/ipo_gmp.asp',
                'parser': self._parse_chittorgarh_gmp
            }
        ]
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
    def _get_headers(self):
        """Get random headers for GMP requests"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache'
        }
    
    def _make_gmp_request(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Make request to GMP sources"""
        for attempt in range(max_retries):
            try:
                self.scraper.headers.update(self._get_headers())
                
                # Random delay
                time.sleep(random.uniform(2, 5))
                
                response = self.scraper.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"GMP request failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"GMP request error (attempt {attempt + 1}): {e}")
                time.sleep(random.uniform(3, 6))
        
        return None
    
    def _parse_ipocentral_gmp(self, html_content: str) -> List[Dict]:
        """Parse IPO Central GMP data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            gmp_data = []
            
            # Find GMP table
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 4:
                        try:
                            company_name = cells[0].get_text(strip=True)
                            gmp_value = self._extract_number(cells[1].get_text(strip=True))
                            price_range = cells[2].get_text(strip=True)
                            listing_gain = self._extract_number(cells[3].get_text(strip=True))
                            
                            if company_name and gmp_value is not None:
                                gmp_data.append({
                                    'company_name': company_name,
                                    'gmp': gmp_value,
                                    'price_range': price_range,
                                    'estimated_listing_gain': listing_gain,
                                    'source': 'IPO Central',
                                    'last_updated': datetime.now().isoformat()
                                })
                                
                        except Exception as e:
                            logger.warning(f"Error parsing GMP row: {e}")
                            continue
            
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error parsing IPO Central GMP: {e}")
            return []
    
    def _parse_chittorgarh_gmp(self, html_content: str) -> List[Dict]:
        """Parse Chittorgarh GMP data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            gmp_data = []
            
            # Find GMP table
            tables = soup.find_all('table', class_='table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 5:
                        try:
                            company_name = cells[0].get_text(strip=True)
                            gmp_value = self._extract_number(cells[2].get_text(strip=True))
                            price_band = cells[1].get_text(strip=True)
                            estimated_listing = self._extract_number(cells[3].get_text(strip=True))
                            
                            if company_name and gmp_value is not None:
                                gmp_data.append({
                                    'company_name': company_name,
                                    'gmp': gmp_value,
                                    'price_range': price_band,
                                    'estimated_listing_gain': estimated_listing,
                                    'source': 'Chittorgarh',
                                    'last_updated': datetime.now().isoformat()
                                })
                                
                        except Exception as e:
                            logger.warning(f"Error parsing Chittorgarh GMP row: {e}")
                            continue
            
            return gmp_data
            
        except Exception as e:
            logger.error(f"Error parsing Chittorgarh GMP: {e}")
            return []
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text (handles ₹, %, etc.)"""
        if not text:
            return None
        
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[₹,%\s₹]', '', str(text))
        
        # Extract number
        match = re.search(r'[-+]?[\d.]+', cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None
    
    async def get_gmp_data(self) -> List[Dict]:
        """Get comprehensive GMP data from multiple sources"""
        logger.info("\n💰 Fetching GMP Data from multiple sources...")
        
        all_gmp_data = []
        
        for source in self.gmp_sources:
            try:
                logger.info(f"📊 Fetching from {source['name']}...")
                
                html_content = self._make_gmp_request(source['url'])
                
                if html_content:
                    gmp_data = source['parser'](html_content)
                    all_gmp_data.extend(gmp_data)
                    logger.info(f"✅ Got {len(gmp_data)} records from {source['name']}")
                else:
                    logger.warning(f"⚠️ No data from {source['name']}")
                    
            except Exception as e:
                logger.error(f"❌ Error fetching from {source['name']}: {e}")
                continue
        
        # Deduplicate and merge GMP data
        merged_data = self._merge_gmp_data(all_gmp_data)
        
        logger.info(f"🎯 Total GMP records: {len(merged_data)}")
        return merged_data
    
    def _merge_gmp_data(self, gmp_data: List[Dict]) -> List[Dict]:
        """Merge GMP data from multiple sources"""
        merged = {}
        
        for item in gmp_data:
            company_name = item.get('company_name', '').strip().upper()
            
            # Clean company name for better matching
            clean_name = re.sub(r'(LIMITED|LTD|PVT|PRIVATE|\.|,)', '', company_name).strip()
            
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
                if item.get('source') not in sources:
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
    
    def calculate_gmp_metrics(self, gmp_data: List[Dict], price_band: str = None) -> Dict[str, Any]:
        """Calculate GMP metrics and insights"""
        if not gmp_data:
            return {"message": "No GMP data available"}
        
        gmp_values = [item['gmp'] for item in gmp_data if item.get('gmp') is not None]
        
        if not gmp_values:
            return {"message": "No valid GMP values found"}
        
        metrics = {
            'average_gmp': round(sum(gmp_values) / len(gmp_values), 2),
            'max_gmp': max(gmp_values),
            'min_gmp': min(gmp_values),
            'positive_gmp_count': len([gmp for gmp in gmp_values if gmp > 0]),
            'negative_gmp_count': len([gmp for gmp in gmp_values if gmp < 0]),
            'zero_gmp_count': len([gmp for gmp in gmp_values if gmp == 0]),
            'total_companies': len(gmp_values)
        }
        
        # Calculate percentage distribution
        total = len(gmp_values)
        metrics['positive_percentage'] = round((metrics['positive_gmp_count'] / total) * 100, 1)
        metrics['negative_percentage'] = round((metrics['negative_gmp_count'] / total) * 100, 1)
        
        # Market sentiment based on GMP
        if metrics['positive_percentage'] > 70:
            metrics['market_sentiment'] = 'Very Bullish'
        elif metrics['positive_percentage'] > 50:
            metrics['market_sentiment'] = 'Bullish'
        elif metrics['positive_percentage'] > 30:
            metrics['market_sentiment'] = 'Neutral'
        else:
            metrics['market_sentiment'] = 'Bearish'
        
        # Calculate estimated listing gain if price band provided
        if price_band:
            price_match = re.findall(r'[\d.]+', price_band)
            if len(price_match) >= 2:
                try:
                    upper_price = float(price_match[-1])
                    avg_gmp = metrics['average_gmp']
                    
                    if upper_price > 0:
                        estimated_gain_percent = (avg_gmp / upper_price) * 100
                        metrics['estimated_listing_gain_percent'] = round(estimated_gain_percent, 2)
                except:
                    pass
        
        return metrics
    
    def get_gmp_recommendations(self, company_name: str, gmp_data: List[Dict]) -> Dict[str, Any]:
        """Get GMP-based recommendations for a specific IPO"""
        company_gmp = None
        
        # Find company in GMP data
        for item in gmp_data:
            if company_name.upper() in item.get('company_name', '').upper():
                company_gmp = item
                break
        
        if not company_gmp:
            return {"message": f"No GMP data found for {company_name}"}
        
        gmp_value = company_gmp.get('gmp', 0)
        
        recommendations = {
            'gmp_value': gmp_value,
            'company_name': company_gmp.get('company_name'),
            'price_range': company_gmp.get('price_range'),
            'sources': company_gmp.get('sources', []),
            'last_updated': company_gmp.get('last_updated')
        }
        
        # Generate recommendations based on GMP
        if gmp_value > 100:
            recommendations['recommendation'] = 'Strong Buy'
            recommendations['reason'] = 'Very high GMP indicates strong market demand'
            recommendations['risk_level'] = 'Low'
        elif gmp_value > 50:
            recommendations['recommendation'] = 'Buy'
            recommendations['reason'] = 'Positive GMP shows good market interest'
            recommendations['risk_level'] = 'Low-Medium'
        elif gmp_value > 0:
            recommendations['recommendation'] = 'Consider'
            recommendations['reason'] = 'Positive but modest GMP'
            recommendations['risk_level'] = 'Medium'
        elif gmp_value == 0:
            recommendations['recommendation'] = 'Neutral'
            recommendations['reason'] = 'No premium in gray market'
            recommendations['risk_level'] = 'Medium'
        else:
            recommendations['recommendation'] = 'Avoid'
            recommendations['reason'] = 'Negative GMP indicates weak demand'
            recommendations['risk_level'] = 'High'
        
        return recommendations
    
    def get_demo_gmp_data(self) -> List[Dict]:
        """Provide demo GMP data when sources are unavailable"""
        return [
            {
                'company_name': 'DEMO IPO LIMITED',
                'gmp': 85,
                'price_range': 'Rs.100 to Rs.120',
                'estimated_listing_gain': 70.8,
                'sources': ['Demo Source'],
                'last_updated': datetime.now().isoformat()
            },
            {
                'company_name': 'SAMPLE COMPANY LTD',
                'gmp': -10,
                'price_range': 'Rs.200 to Rs.250',
                'estimated_listing_gain': -4.0,
                'sources': ['Demo Source'],
                'last_updated': datetime.now().isoformat()
            },
            {
                'company_name': 'TEST INDUSTRIES',
                'gmp': 25,
                'price_range': 'Rs.150 to Rs.180',
                'estimated_listing_gain': 13.9,
                'sources': ['Demo Source'],
                'last_updated': datetime.now().isoformat()
            }
        ]
    