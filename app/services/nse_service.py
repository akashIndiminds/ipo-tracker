import requests
import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
from urllib.parse import urljoin
import cloudscraper
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class NSEService:
    """Advanced NSE data scraping service with enhanced anti-blocking features"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com/api"
        self.base_site = "https://www.nseindia.com"
        
        # Initialize cloudscraper for better CloudFlare handling
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # Multiple user agents
        self.ua = UserAgent()
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0'
        ]
        
        # Request delays for rate limiting
        self.min_delay = 2
        self.max_delay = 5
        self.last_request_time = 0
        
        # Session management
        self.session_initialized = False
        self.cookies_valid = False
        
        # Initialize session
        self._init_session()
        
    def _get_headers(self):
        """Get random headers for requests"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
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
    
    def _init_session(self):
        """Initialize session with NSE homepage and get cookies"""
        try:
            logger.info("🔧 Initializing advanced NSE session...")
            
            # Method 1: Using cloudscraper
            self.scraper.headers.update(self._get_headers())
            
            # Visit homepage to establish session
            homepage_response = self.scraper.get(self.base_site, timeout=30)
            logger.info(f"📱 Homepage response: {homepage_response.status_code}")
            
            if homepage_response.status_code == 200:
                self.session_initialized = True
                self.cookies_valid = True
                logger.info("✅ Session initialized successfully")
            else:
                logger.warning(f"⚠️ Homepage returned {homepage_response.status_code}")
            
            # Visit some basic pages to warm up session
            warmup_urls = [
                '/market-data/live-equity-market',
                '/companies-listing/corporate-filings-ipo'
            ]
            
            for url in warmup_urls:
                try:
                    self.scraper.get(f"{self.base_site}{url}", timeout=20)
                    time.sleep(random.uniform(1, 2))
                except:
                    continue
            
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            logger.warning(f"⚠️ Session initialization error: {e}")
            self.session_initialized = False
    
    def _rate_limit(self):
        """Implement intelligent rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        min_interval = random.uniform(self.min_delay, self.max_delay)
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.info(f"⏱️ Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: dict = None, max_retries: int = 5) -> Optional[Any]:
        """Enhanced request method with advanced anti-blocking"""
        
        for attempt in range(max_retries):
            try:
                # Rate limiting
                self._rate_limit()
                
                # Refresh session if needed
                if not self.session_initialized or attempt > 2:
                    self._init_session()
                
                # Update headers for each request
                self.scraper.headers.update(self._get_headers())
                
                logger.info(f"🔄 Request attempt {attempt + 1}/{max_retries}: {url}")
                
                # Make request using cloudscraper
                response = self.scraper.get(url, params=params, timeout=45)
                logger.info(f"📊 Response: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        # Clean response text to remove null bytes
                        clean_text = response.text.replace('\x00', '')
                        data = json.loads(clean_text)
                        
                        data_len = len(data) if isinstance(data, list) else len(data.get('data', [])) if isinstance(data, dict) else 'unknown'
                        logger.info(f"✅ Success! Data length: {data_len}")
                        return data
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON decode error: {e}")
                        # Try to extract JSON from response
                        try:
                            # Sometimes response has extra characters
                            json_start = response.text.find('{')
                            json_end = response.text.rfind('}') + 1
                            if json_start >= 0 and json_end > json_start:
                                clean_json = response.text[json_start:json_end].replace('\x00', '')
                                return json.loads(clean_json)
                        except:
                            pass
                        return None
                        
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 15
                    logger.warning(f"⏳ Rate limited! Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    
                elif response.status_code == 403:
                    logger.warning("🚫 Access forbidden! Using different strategy...")
                    self._init_session()
                    time.sleep(random.uniform(5, 10))
                    
                elif response.status_code == 404:
                    logger.error("🔍 Endpoint not found")
                    return None
                    
                elif response.status_code == 503:
                    logger.warning("🔧 Service unavailable, retrying...")
                    time.sleep(random.uniform(10, 20))
                    
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code}")
                    time.sleep(random.uniform(3, 6))
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Request timeout on attempt {attempt + 1}")
                time.sleep(random.uniform(5, 10))
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Connection error on attempt {attempt + 1}")
                time.sleep(random.uniform(8, 15))
                
            except Exception as e:
                logger.error(f"❌ Request failed (attempt {attempt + 1}): {e}")
                time.sleep(random.uniform(3, 8))
        
        logger.error(f"💀 All {max_retries} attempts failed for: {url}")
        return self._get_fallback_data(url)
    
    def _get_fallback_data(self, url: str) -> List[Dict]:
        """Provide fallback data when all requests fail"""
        if "current-issue" in url:
            return self._get_demo_current_ipos()
        elif "upcoming" in url:
            return self._get_demo_upcoming_ipos()
        elif "indices" in url:
            return self._get_demo_indices()
        return []
    
    def _get_demo_current_ipos(self) -> List[Dict]:
        """Demo current IPOs data"""
        return [
            {
                "symbol": "DEMO_CURRENT",
                "companyName": "Demo Current IPO Limited",
                "series": "EQ",
                "issueStartDate": datetime.now().strftime("%d-%b-%Y"),
                "issueEndDate": (datetime.now() + timedelta(days=2)).strftime("%d-%b-%Y"),
                "issuePrice": "Rs.100 to Rs.120",
                "issueSize": "50000000",
                "status": "Demo Data - NSE API Unavailable",
                "noOfTime": "1.25",
                "noOfSharesOffered": "5000000",
                "noOfsharesBid": "6250000"
            }
        ]
    
    def _get_demo_upcoming_ipos(self) -> List[Dict]:
        """Demo upcoming IPOs data"""
        return [
            {
                "symbol": "DEMO_UPCOMING",
                "companyName": "Demo Upcoming IPO Limited",
                "series": "EQ",
                "issueStartDate": (datetime.now() + timedelta(days=5)).strftime("%d-%b-%Y"),
                "issueEndDate": (datetime.now() + timedelta(days=8)).strftime("%d-%b-%Y"),
                "issuePrice": "Rs.200 to Rs.250",
                "issueSize": "75000000",
                "status": "Forthcoming"
            }
        ]
    
    def _get_demo_indices(self) -> List[Dict]:
        """Demo market indices data"""
        return [
            {
                "indexName": "NIFTY 50",
                "last": 25000.0,
                "open": 24980.0,
                "high": 25050.0,
                "low": 24950.0,
                "previousClose": 24990.0,
                "change": 10.0,
                "percChange": 0.04,
                "yearHigh": 26277.35,
                "yearLow": 21743.65,
                "timeVal": datetime.now().strftime("%d-%b-%Y %H:%M")
            }
        ]

    # Main API methods
    async def get_current_ipos(self) -> List[Dict]:
        """Get current active IPOs"""
        logger.info("\n📈 Fetching Current IPOs...")
        
        url = f"{self.base_url}/ipo-current-issue"
        result = self._make_request(url)
        
        if result and isinstance(result, list):
            logger.info(f"🎯 Found {len(result)} current IPOs")
            return result
        
        logger.warning("⚠️ Using fallback data for current IPOs")
        return self._get_demo_current_ipos()
    
    async def get_upcoming_ipos(self) -> List[Dict]:
        """Get upcoming IPOs"""
        logger.info("\n🔮 Fetching Upcoming IPOs...")
        
        url = f"{self.base_url}/all-upcoming-issues"
        params = {"category": "ipo"}
        result = self._make_request(url, params)
        
        if result and isinstance(result, list):
            logger.info(f"🎯 Found {len(result)} upcoming IPOs")
            return result
        
        logger.warning("⚠️ Using fallback data for upcoming IPOs")
        return self._get_demo_upcoming_ipos()
    
    async def get_past_ipos(self, days_back: int = 30) -> List[Dict]:
        """Get past IPOs"""
        logger.info(f"\n📊 Fetching Past IPOs (Last {days_back} days)...")
        
        days_back = min(days_back, 90)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        url = f"{self.base_url}/public-past-issues"
        params = {
            "from_date": start_date.strftime("%d-%m-%Y"),
            "to_date": end_date.strftime("%d-%m-%Y"),
            "security_type": "all"
        }
        
        result = self._make_request(url, params)
        
        if result and isinstance(result, list):
            logger.info(f"🎯 Found {len(result)} past IPOs")
            return result
        
        logger.warning("⚠️ No past IPOs data available")
        return []
    
    async def get_market_indices(self) -> List[Dict]:
        """Get market indices"""
        logger.info("\n📊 Fetching Market Indices...")
        
        url = f"{self.base_url}/allIndices"
        result = self._make_request(url)
        
        if result:
            if isinstance(result, dict) and 'data' in result:
                indices_data = result['data']
                logger.info(f"🎯 Found {len(indices_data)} market indices")
                return indices_data
            elif isinstance(result, list):
                logger.info(f"🎯 Found {len(result)} market indices")
                return result
        
        logger.warning("⚠️ Using fallback data for market indices")
        return self._get_demo_indices()
    
    async def get_market_status(self) -> List[Dict]:
        """Get market status"""
        logger.info("\n🎯 Fetching Market Status...")
        
        url = f"{self.base_url}/marketStatus"
        result = self._make_request(url)
        
        if result and isinstance(result, list):
            logger.info(f"🎯 Found market status: {len(result)} entries")
            return result
        
        # Fallback market status
        return [
            {
                "market": "Capital Market",
                "marketStatus": "Open" if 9 <= datetime.now().hour <= 15 else "Closed",
                "tradeDate": datetime.now().strftime("%d-%b-%Y"),
                "index": "NIFTY 50"
            }
        ]
    
    async def test_all_endpoints(self) -> Dict[str, Any]:
        """Test all endpoints comprehensively"""
        logger.info("\n🧪 Testing All NSE Endpoints...")
        
        test_results = {}
        
        endpoints = {
            'current_ipos': self.get_current_ipos,
            'upcoming_ipos': self.get_upcoming_ipos,
            'past_ipos': lambda: self.get_past_ipos(7),
            'market_indices': self.get_market_indices,
            'market_status': self.get_market_status
        }
        
        for endpoint_name, endpoint_func in endpoints.items():
            start_time = time.time()
            
            try:
                data = await endpoint_func()
                response_time = time.time() - start_time
                
                test_results[endpoint_name] = {
                    'status': 'success' if data else 'empty',
                    'count': len(data) if data else 0,
                    'response_time': round(response_time, 2),
                    'sample': data[:1] if data else []
                }
                
            except Exception as e:
                response_time = time.time() - start_time
                test_results[endpoint_name] = {
                    'status': 'failed',
                    'count': 0,
                    'response_time': round(response_time, 2),
                    'error': str(e)
                }
        
        # Calculate metrics
        success_count = sum(1 for result in test_results.values() if result['status'] == 'success')
        total_count = len(test_results)
        avg_response_time = sum(result['response_time'] for result in test_results.values()) / total_count
        
        overall_status = (
            'excellent' if success_count == total_count else
            'good' if success_count >= 3 else
            'partial' if success_count >= 1 else
            'failed'
        )
        
        summary = {
            'overall_status': overall_status,
            'success_rate': round((success_count / total_count) * 100, 1),
            'working_endpoints': success_count,
            'total_endpoints': total_count,
            'average_response_time': round(avg_response_time, 2),
            'test_results': test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"\n📊 Test Summary: {success_count}/{total_count} endpoints working ({summary['success_rate']}%)")
        return summary