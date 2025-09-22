# app/services/gmp_service.py
import requests
import cloudscraper
import time
import random
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
from bs4 import BeautifulSoup
import re
import json

logger = logging.getLogger(__name__)

class GMPService:
    """Enhanced Gray Market Premium Service"""
    
    def __init__(self):
        # Create cloudscraper for better protection bypass
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # GMP data sources with better reliability
        self.gmp_sources = [
            {
                'name': 'IPOWatch',
                'url': 'https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/',
                'parser': self._parse_ipowatch_gmp,
                'priority': 1
            },
            {
                'name': 'Chittorgarh',
                'url': 'https://www.chittorgarh.com/ipo_gmp.asp',
                'parser': self._parse_chittorgarh_gmp,
                'priority': 2
            },
            {
                'name': 'IPO Central',
                'url': 'https://ipocentral.in/ipo-gmp/',
                'parser': self._parse_ipocentral_gmp,
                'priority': 3
            }
        ]
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def _get_headers(self):
        """Get random headers"""
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
        """Make GMP request with retry logic"""
        
        for attempt in range(max_retries):
            try:
                # Update headers
                self.scraper.headers.update(self._get_headers())
                
                # Random delay
                time.sleep(random.uniform(2, 5))
                
                logger.info(f"🔄 GMP Request attempt {attempt + 1}: {url}")
                
                response = self.scraper.get(url, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"✅ GMP request successful")
                    return response.text
                else:
                    logger.warning(f"⚠️ GMP request failed: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ GMP request error (attempt {attempt + 1}): {e}")
                time.sleep(random.uniform(3, 6))
        
        return None
    
    def _parse_ipowatch_gmp(self, html_content: str) -> List[Dict]:
        """Parse IPOWatch GMP data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            gmp_data = []
            
            # Find tables with GMP data
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                # Skip header row
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 4:
                        try:
                            # Extract data from cells
                            company_name = cells[0].get_text(strip=True)
                            gmp_text = cells[1].get_text(strip=True)
                            price_range = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                            listing_gain = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                            
                            # Extract GMP value
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
                            logger.warning(f"Error parsing GMP row: {e}")
                            continue
            
            logger.info(f"✅ Parsed {len(gmp_data)} GMP records from IPOWatch")
            return gmp_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing IPOWatch GMP: {e}")
            return []
    
    def _parse_chittorgarh_gmp(self, html_content: str) -> List[Dict]:
        """Parse Chittorgarh GMP data"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            gmp_data = []
            
            # Find GMP tables
            tables = soup.find_all('table', class_='table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    
                    if len(cells) >= 5:
                        try:
                            company_name = cells[0].get_text(strip=True)
                            price_band = cells[1].get_text(strip=True)
                            gmp_text = cells[2].get_text(strip=True)
                            estimated_listing = cells[3].get_text(strip=True)
                            
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
                            logger.warning(f"Error parsing Chittorgarh GMP row: {e}")
                            continue
            
            logger.info(f"✅ Parsed {len(gmp_data)} GMP records from Chittorgarh")
            return gmp_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing Chittorgarh GMP: {e}")
            return []
    
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
                            logger.warning(f"Error parsing IPO Central GMP row: {e}")
                            continue
            
            logger.info(f"✅ Parsed {len(gmp_data)} GMP records from IPO Central")
            return gmp_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing IPO Central GMP: {e}")
            return []
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text (handles ₹, %, etc.)"""
        if not text:
            return None
        
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[₹,%\s₹]', '', str(text))
        
        # Extract number including negative values
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
        
        # Sort sources by priority
        sorted_sources = sorted(self.gmp_sources, key=lambda x: x['priority'])
        
        for source in sorted_sources:
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
        
        # If no real data, use demo data
        if not all_gmp_data:
            logger.warning("⚠️ No GMP data from sources, using demo data")
            all_gmp_data = self.get_demo_gmp_data()
        
        # Merge and deduplicate
        merged_data = self._merge_gmp_data(all_gmp_data)
        
        logger.info(f"🎯 Final GMP records: {len(merged_data)}")
        return merged_data
    
    def _merge_gmp_data(self, gmp_data: List[Dict]) -> List[Dict]:
        """Merge and deduplicate GMP data from multiple sources"""
        merged = {}
        
        for item in gmp_data:
            company_name = item.get('company_name', '').strip().upper()
            
            # Clean company name for better matching
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
    
    def calculate_gmp_metrics(self, gmp_data: List[Dict]) -> Dict[str, Any]:
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
        
        # Calculate percentages
        total = len(gmp_values)
        metrics['positive_percentage'] = round((metrics['positive_gmp_count'] / total) * 100, 1)
        metrics['negative_percentage'] = round((metrics['negative_gmp_count'] / total) * 100, 1)
        metrics['neutral_percentage'] = round((metrics['zero_gmp_count'] / total) * 100, 1)
        
        # Market sentiment based on GMP
        if metrics['positive_percentage'] > 70:
            metrics['market_sentiment'] = 'Very Bullish'
        elif metrics['positive_percentage'] > 50:
            metrics['market_sentiment'] = 'Bullish'
        elif metrics['positive_percentage'] > 30:
            metrics['market_sentiment'] = 'Neutral'
        else:
            metrics['market_sentiment'] = 'Bearish'
        
        # GMP distribution
        metrics['gmp_distribution'] = {
            'high_premium': len([gmp for gmp in gmp_values if gmp > 100]),
            'medium_premium': len([gmp for gmp in gmp_values if 50 <= gmp <= 100]),
            'low_premium': len([gmp for gmp in gmp_values if 0 < gmp < 50]),
            'at_par': len([gmp for gmp in gmp_values if gmp == 0]),
            'discount': len([gmp for gmp in gmp_values if gmp < 0])
        }
        
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
            'estimated_listing_gain': company_gmp.get('estimated_listing_gain'),
            'sources': company_gmp.get('sources', []),
            'last_updated': company_gmp.get('last_updated')
        }
        
        # Generate recommendations based on GMP
        if gmp_value > 100:
            recommendations['recommendation'] = 'Strong Buy'
            recommendations['reason'] = 'Very high GMP indicates exceptional market demand'
            recommendations['risk_level'] = 'Low'
            recommendations['confidence'] = 'High'
        elif gmp_value > 50:
            recommendations['recommendation'] = 'Buy'
            recommendations['reason'] = 'Good GMP shows strong market interest'
            recommendations['risk_level'] = 'Low-Medium'
            recommendations['confidence'] = 'High'
        elif gmp_value > 20:
            recommendations['recommendation'] = 'Consider'
            recommendations['reason'] = 'Moderate GMP indicates decent demand'
            recommendations['risk_level'] = 'Medium'
            recommendations['confidence'] = 'Medium'
        elif gmp_value > 0:
            recommendations['recommendation'] = 'Cautious'
            recommendations['reason'] = 'Low but positive GMP'
            recommendations['risk_level'] = 'Medium'
            recommendations['confidence'] = 'Medium'
        elif gmp_value == 0:
            recommendations['recommendation'] = 'Neutral'
            recommendations['reason'] = 'No premium in gray market'
            recommendations['risk_level'] = 'Medium-High'
            recommendations['confidence'] = 'Low'
        else:
            recommendations['recommendation'] = 'Avoid'
            recommendations['reason'] = 'Negative GMP indicates weak demand'
            recommendations['risk_level'] = 'High'
            recommendations['confidence'] = 'High'
        
        return recommendations
    
    def get_demo_gmp_data(self) -> List[Dict]:
        """Provide comprehensive demo GMP data"""
        return [
            {
                'company_name': 'TATA TECHNOLOGIES LIMITED',
                'gmp': 125,
                'price_range': 'Rs.485 to Rs.500',
                'estimated_listing_gain': 25.0,
                'sources': ['Demo Source'],
                'last_updated': datetime.now().isoformat()
            },
            {
                'company_name': 'NEXUS SELECT TRUST',
                'gmp': 85,
                'price_range': 'Rs.112 to Rs.114',
                'estimated_listing_gain': 74.6,
                'sources': ['Demo Source'],
                'last_updated': datetime.now().isoformat()
            },
            {
                'company_name': 'IREDA LIMITED',
                'gmp': -5,
                'price_range': 'Rs.32 to Rs.33',
                'estimated_listing_gain': -15.2,
                'sources': ['Demo Source'],
                'last_updated': datetime.now().isoformat()
            },
            {
                'company_name': 'BHARTI HEXACOM LIMITED',
                'gmp': 45,
                'price_range': 'Rs.570 to Rs.575',
                'estimated_listing_gain': 7.8,
                'sources': ['Demo Source'],
                'last_updated': datetime.now().isoformat()
            },
            {
                'company_name': 'INDIA SHELTER FINANCE',
                'gmp': 0,
                'price_range': 'Rs.88 to Rs.90',
                'estimated_listing_gain': 0.0,
                'sources': ['Demo Source'],
                'last_updated': datetime.now().isoformat()
            }
        ]