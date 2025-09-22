# app/services/nse_scraper.py
"""
NSE Data Scraper with Complete Anti-Blocking Logic
"""

import requests
import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)

class NSEScraper:
    """
    Advanced NSE Scraper with multiple bypass strategies
    """
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.api_base = "https://www.nseindia.com/api"
        
        # Initialize different scrapers
        self.session = requests.Session()
        self.cloudscraper = cloudscraper.create_scraper()
        self.selenium_driver = None
        
        # Headers pool
        self.headers_pool = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.nseindia.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors', 
                'Sec-Fetch-Site': 'same-origin',
                'X-Requested-With': 'XMLHttpRequest',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        ]
        
        # Initialize session
        self.cookies = {}
        self.last_request_time = 0
        self.request_delay = 2  # Minimum delay between requests
        
    def _init_selenium(self):
        """Initialize Selenium with undetected Chrome driver"""
        try:
            # Chrome options for stealth
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--headless=new')  # New headless mode
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Create driver
            self.selenium_driver = uc.Chrome(options=chrome_options, version_main=120)
            self.selenium_driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            logger.info("✅ Selenium driver initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Selenium initialization failed: {e}")
            return False
    
    def _get_cookies_selenium(self):
        """Get cookies using Selenium"""
        try:
            if not self.selenium_driver:
                self._init_selenium()
            
            logger.info("🍪 Getting cookies via Selenium...")
            
            # Visit NSE homepage
            self.selenium_driver.get(self.base_url)
            time.sleep(random.uniform(3, 5))
            
            # Wait for page to load
            WebDriverWait(self.selenium_driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get cookies
            selenium_cookies = self.selenium_driver.get_cookies()
            
            # Convert to requests format
            for cookie in selenium_cookies:
                self.cookies[cookie['name']] = cookie['value']
            
            logger.info(f"✅ Got {len(self.cookies)} cookies")
            return True
            
        except Exception as e:
            logger.error(f"❌ Selenium cookie fetch failed: {e}")
            return False
    
    def _get_cookies_cloudscraper(self):
        """Get cookies using CloudScraper"""
        try:
            logger.info("🍪 Getting cookies via CloudScraper...")
            
            response = self.cloudscraper.get(self.base_url, timeout=30)
            
            if response.status_code == 200:
                self.cookies = self.cloudscraper.cookies.get_dict()
                logger.info(f"✅ Got {len(self.cookies)} cookies via CloudScraper")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ CloudScraper cookie fetch failed: {e}")
            return False
    
    def _get_cookies_requests(self):
        """Get cookies using requests with session"""
        try:
            logger.info("🍪 Getting cookies via Requests...")
            
            # Set headers
            headers = random.choice(self.headers_pool)
            self.session.headers.update(headers)
            
            # Visit homepage first
            response = self.session.get(self.base_url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ Got cookies via Requests")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Requests cookie fetch failed: {e}")
            return False
    
    def _ensure_cookies(self):
        """Ensure we have valid cookies using multiple methods"""
        
        # Method 1: Try CloudScraper first (fastest)
        if self._get_cookies_cloudscraper():
            return True
        
        # Method 2: Try Requests
        if self._get_cookies_requests():
            return True
        
        # Method 3: Try Selenium (slowest but most reliable)
        if self._get_cookies_selenium():
            return True
        
        logger.error("❌ All cookie fetch methods failed!")
        return False
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.request_delay:
            sleep_time = self.request_delay - elapsed + random.uniform(0.5, 1.5)
            logger.info(f"⏱️ Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_with_selenium(self, url: str) -> Optional[Dict]:
        """Fetch data using Selenium"""
        try:
            if not self.selenium_driver:
                self._init_selenium()
            
            logger.info(f"🌐 Fetching with Selenium: {url}")
            
            self.selenium_driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            # Try to find pre tag with JSON
            try:
                pre_element = self.selenium_driver.find_element(By.TAG_NAME, "pre")
                json_text = pre_element.text
                return json.loads(json_text)
            except:
                # Try to extract from page source
                page_source = self.selenium_driver.page_source
                
                # Look for JSON in script tags
                soup = BeautifulSoup(page_source, 'html.parser')
                scripts = soup.find_all('script')
                
                for script in scripts:
                    if script.string and 'window.__PRELOADED_STATE__' in script.string:
                        # Extract JSON from script
                        json_str = script.string.split('=', 1)[1].strip()
                        if json_str.endswith(';'):
                            json_str = json_str[:-1]
                        return json.loads(json_str)
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Selenium fetch failed: {e}")
            return None
    
    def fetch_with_cloudscraper(self, url: str) -> Optional[Dict]:
        """Fetch data using CloudScraper"""
        try:
            logger.info(f"☁️ Fetching with CloudScraper: {url}")
            
            response = self.cloudscraper.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ CloudScraper fetch failed: {e}")
            return None
    
    def fetch_with_requests(self, url: str) -> Optional[Dict]:
        """Fetch data using requests"""
        try:
            logger.info(f"📡 Fetching with Requests: {url}")
            
            headers = random.choice(self.headers_pool)
            response = self.session.get(url, headers=headers, cookies=self.cookies, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Requests fetch failed: {e}")
            return None
    
    def fetch_api_data(self, endpoint: str, params: dict = None) -> Optional[Dict]:
        """
        Main method to fetch API data using multiple strategies
        """
        url = f"{self.api_base}/{endpoint}"
        if params:
            url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
        
        logger.info(f"\n🎯 Fetching: {endpoint}")
        
        # Ensure we have cookies
        if not self.cookies:
            self._ensure_cookies()
        
        # Apply rate limiting
        self._rate_limit()
        
        # Strategy 1: Try CloudScraper
        data = self.fetch_with_cloudscraper(url)
        if data:
            logger.info("✅ CloudScraper successful")
            return data
        
        # Strategy 2: Try Requests with cookies
        data = self.fetch_with_requests(url)
        if data:
            logger.info("✅ Requests successful")
            return data
        
        # Strategy 3: Get fresh cookies and retry
        logger.info("🔄 Refreshing cookies...")
        self._ensure_cookies()
        data = self.fetch_with_requests(url)
        if data:
            logger.info("✅ Requests with fresh cookies successful")
            return data
        
        # Strategy 4: Use Selenium (last resort)
        data = self.fetch_with_selenium(url)
        if data:
            logger.info("✅ Selenium successful")
            return data
        
        logger.error(f"❌ All strategies failed for {endpoint}")
        return None
    
    def get_current_ipos(self) -> List[Dict]:
        """Get current IPOs"""
        data = self.fetch_api_data("ipo-current-issue")
        return data if data else []
    
    def get_upcoming_ipos(self) -> List[Dict]:
        """Get upcoming IPOs"""
        data = self.fetch_api_data("all-upcoming-issues", {"category": "ipo"})
        return data if data else []
    
    def get_past_ipos(self, days: int = 30) -> List[Dict]:
        """Get past IPOs"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "from_date": start_date.strftime("%d-%m-%Y"),
            "to_date": end_date.strftime("%d-%m-%Y"),
            "security_type": "all"
        }
        
        data = self.fetch_api_data("public-past-issues", params)
        return data if data else []
    
    def get_market_indices(self) -> List[Dict]:
        """Get market indices"""
        data = self.fetch_api_data("allIndices")
        
        if data and isinstance(data, dict):
            return data.get('data', [])
        elif isinstance(data, list):
            return data
        
        return []
    
    def get_gmp_data(self) -> List[Dict]:
        """Get GMP data from IPOWatch"""
        try:
            logger.info("💰 Fetching GMP data from IPOWatch...")
            
            url = "https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"
            
            response = self.cloudscraper.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find GMP table
                table = soup.find('table', class_='tablepress')
                if not table:
                    table = soup.find('table')
                
                if table:
                    df = pd.read_html(str(table))[0]
                    
                    gmp_data = []
                    for _, row in df.iterrows():
                        try:
                            gmp_data.append({
                                'company_name': row.iloc[0],
                                'gmp': self._extract_number(row.iloc[1]),
                                'price_range': row.iloc[2] if len(row) > 2 else '',
                                'estimated_listing_gain': self._extract_number(row.iloc[3]) if len(row) > 3 else 0,
                                'source': 'IPOWatch',
                                'last_updated': datetime.now().isoformat()
                            })
                        except:
                            continue
                    
                    logger.info(f"✅ Got {len(gmp_data)} GMP records")
                    return gmp_data
            
            return []
            
        except Exception as e:
            logger.error(f"❌ GMP fetch failed: {e}")
            return []
    
    def _extract_number(self, text: str) -> float:
        """Extract number from text"""
        import re
        if not text:
            return 0
        
        # Remove currency symbols and extract number
        cleaned = re.sub(r'[₹,%\s]', '', str(text))
        match = re.search(r'[-+]?[\d.]+', cleaned)
        
        if match:
            try:
                return float(match.group())
            except:
                return 0
        return 0
    
    def cleanup(self):
        """Cleanup resources"""
        if self.selenium_driver:
            try:
                self.selenium_driver.quit()
            except:
                pass
        logger.info("🧹 Cleaned up resources")
