import requests
import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

class NSEService:
    """NSE data scraping service with anti-blocking features"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com/api"
        self.session = requests.Session()
        
        # Multiple user agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # Headers for requests
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        # Initialize session
        self._init_session()
        
    def _init_session(self):
        """Initialize session with NSE homepage"""
        try:
            logger.info("🔧 Initializing NSE session...")
            
            # Update headers with random user agent
            self.headers['User-Agent'] = random.choice(self.user_agents)
            self.session.headers.update(self.headers)
            
            # Visit homepage to get cookies
            homepage_response = self.session.get('https://www.nseindia.com', timeout=15)
            logger.info(f"📱 Homepage response: {homepage_response.status_code}")
            
            # Small delay
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            logger.warning(f"⚠️ Session initialization warning: {e}")
    
    def _make_request(self, url: str, params: dict = None, max_retries: int = 3) -> Optional[Any]:
        """Make HTTP request with retry logic and anti-blocking"""
        
        for attempt in range(max_retries):
            try:
                # Update user agent for each request
                self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                # Random delay between requests
                delay = random.uniform(1, 4)
                time.sleep(delay)
                
                logger.info(f"🔄 Request attempt {attempt + 1}/{max_retries}: {url}")
                logger.info(f"⏱️ Delay: {delay:.1f}s")
                
                # Make request
                response = self.session.get(url, params=params, timeout=30)
                logger.info(f"📊 Response: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        data_len = len(data) if isinstance(data, list) else len(data.get('data', [])) if isinstance(data, dict) else 'unknown'
                        logger.info(f"✅ Success! Data length: {data_len}")
                        return data
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON decode error: {e}")
                        return None
                        
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 10
                    logger.warning(f"⏳ Rate limited! Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    
                elif response.status_code == 403:
                    logger.warning("🚫 Access forbidden! Reinitializing session...")
                    self._init_session()
                    time.sleep(5)
                    
                elif response.status_code == 404:
                    logger.error("🔍 Endpoint not found")
                    return None
                    
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code}: {response.text[:200]}")
                    time.sleep(2)
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Request timeout on attempt {attempt + 1}")
                time.sleep(3)
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Connection error on attempt {attempt + 1}")
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Request failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)
        
        logger.error(f"💀 All {max_retries} attempts failed for: {url}")
        return None
    
    async def get_current_ipos(self) -> List[Dict]:
        """Get current active IPOs"""
        logger.info("\n📈 Fetching Current IPOs...")
        
        url = f"{self.base_url}/ipo-current-issue"
        result = self._make_request(url)
        
        if result and isinstance(result, list):
            logger.info(f"🎯 Found {len(result)} current IPOs")
            return result
        
        logger.warning("⚠️ No current IPOs data available")
        return []
    
    async def get_upcoming_ipos(self) -> List[Dict]:
        """Get upcoming IPOs"""
        logger.info("\n🔮 Fetching Upcoming IPOs...")
        
        url = f"{self.base_url}/all-upcoming-issues"
        params = {"category": "ipo"}
        result = self._make_request(url, params)
        
        if result and isinstance(result, list):
            logger.info(f"🎯 Found {len(result)} upcoming IPOs")
            return result
        
        logger.warning("⚠️ No upcoming IPOs data available")
        return []
    
    async def get_past_ipos(self, days_back: int = 30) -> List[Dict]:
        """Get past IPOs"""
        logger.info(f"\n📊 Fetching Past IPOs (Last {days_back} days)...")
        
        # Limit days to avoid overloading
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
        
        logger.warning("⚠️ No market indices data available")
        return []
    
    async def get_market_status(self) -> List[Dict]:
        """Get market status"""
        logger.info("\n🎯 Fetching Market Status...")
        
        url = f"{self.base_url}/marketStatus"
        result = self._make_request(url)
        
        if result and isinstance(result, list):
            logger.info(f"🎯 Found market status: {len(result)} entries")
            return result
        
        logger.warning("⚠️ No market status data available")
        return []
    
    async def test_all_endpoints(self) -> Dict[str, Any]:
        """Test all endpoints and return comprehensive status"""
        logger.info("\n🧪 Testing All NSE Endpoints...")
        
        test_results = {}
        
        # Test endpoints
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
        
        # Calculate overall metrics
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
        logger.info(f"🎯 Overall Status: {overall_status.upper()}")
        
        return summary
    
    def get_fallback_data(self, data_type: str) -> List[Dict]:
        """Get fallback data when APIs are down"""
        fallback_data = {
            'current_ipos': [
                {
                    "symbol": "DEMO_IPO",
                    "companyName": "Demo Company Limited",
                    "issueStartDate": datetime.now().strftime("%d-%b-%Y"),
                    "issueEndDate": (datetime.now() + timedelta(days=3)).strftime("%d-%b-%Y"),
                    "issuePrice": "Rs.100 to Rs.120",
                    "status": "Demo Data - NSE API Unavailable",
                    "note": "This is fallback demo data"
                }
            ],
            'upcoming_ipos': [
                {
                    "symbol": "UPCOMING_DEMO",
                    "companyName": "Upcoming Demo Limited", 
                    "issueStartDate": (datetime.now() + timedelta(days=5)).strftime("%d-%b-%Y"),
                    "issueEndDate": (datetime.now() + timedelta(days=8)).strftime("%d-%b-%Y"),
                    "issuePrice": "Rs.200 to Rs.250",
                    "status": "Demo Data"
                }
            ],
            'market_indices': [
                {
                    "indexName": "NIFTY 50",
                    "last": 25000.0,
                    "percChange": 0.0,
                    "note": "Demo data - NSE API unavailable"
                }
            ]
        }
        
        return fallback_data.get(data_type, [])