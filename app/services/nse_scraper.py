# app/services/nse_scraper.py
import requests
import time
import random
import json
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class NSESessionManager:
    """NSE Session Manager with Auto-Refresh"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.api_base = "https://www.nseindia.com/api"
        
        # Session management
        self.session = None
        self.session_active = False
        self.session_created_at = 0
        self.session_expires_at = 0
        self.session_duration = 600  # 10 minutes
        self.last_request_time = 0
        
        # Request settings
        self.min_delay = 1
        self.max_delay = 3
        self.max_retries = 2
        
        # Thread lock for session refresh
        self.session_lock = threading.Lock()
        
        # Initialize first session
        self._create_fresh_session()
    
    def _create_fresh_session(self):
        """Create a completely new NSE session"""
        with self.session_lock:
            try:
                logger.info("🔄 Creating fresh NSE session...")
                
                # Close existing session if any
                if self.session:
                    try:
                        self.session.close()
                    except:
                        pass
                
                # Create new session
                self.session = requests.Session()
                self.session.verify = False
                
                # Set realistic headers
                self.session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Cache-Control': 'max-age=0'
                })
                
                # Visit NSE homepage to establish session
                response = self.session.get(self.base_url, timeout=20)
                
                if response.status_code == 200:
                    current_time = time.time()
                    self.session_created_at = current_time
                    self.session_expires_at = current_time + self.session_duration
                    self.session_active = True
                    
                    logger.info("✅ Fresh NSE session created successfully")
                    
                    # Quick warmup
                    self._warmup_session()
                    
                    return True
                else:
                    logger.error(f"❌ NSE homepage returned: {response.status_code}")
                    self.session_active = False
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Failed to create NSE session: {e}")
                self.session_active = False
                return False
    
    def _warmup_session(self):
        """Warm up the session with light requests"""
        try:
            warmup_pages = [
                "/companies-listing",
                "/market-data"
            ]
            
            for page in warmup_pages:
                try:
                    self.session.get(f"{self.base_url}{page}", timeout=10)
                    time.sleep(random.uniform(0.5, 1))
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"⚠️ Session warmup issue: {e}")
    
    def _is_session_expired(self):
        """Check if current session is expired"""
        current_time = time.time()
        
        # Check time-based expiry
        if current_time >= self.session_expires_at:
            logger.info("⏰ Session expired due to time")
            return True
        
        # Check if session is too old (safety check)
        if (current_time - self.session_created_at) > (self.session_duration + 60):
            logger.info("⏰ Session expired due to age")
            return True
        
        return False
    
    def _refresh_session_if_needed(self):
        """Refresh session if needed"""
        if not self.session_active or self._is_session_expired():
            logger.info("🔄 Session refresh needed...")
            return self._create_fresh_session()
        
        return True
    
    def _rate_limit(self):
        """Smart rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        min_wait = random.uniform(self.min_delay, self.max_delay)
        
        if elapsed < min_wait:
            sleep_time = min_wait - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def make_api_request(self, endpoint: str, params: Dict = None) -> Optional[Any]:
        """Make API request with automatic session management"""
        
        # Refresh session if needed
        if not self._refresh_session_if_needed():
            logger.error("❌ Cannot establish NSE session")
            return None
        
        url = f"{self.api_base}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                self._rate_limit()
                
                # Set API-specific headers
                api_headers = {
                    'Accept': 'application/json, text/plain, */*',
                    'Referer': 'https://www.nseindia.com/companies-listing/corporate-filings-ipo',
                    'X-Requested-With': 'XMLHttpRequest'
                }
                
                logger.info(f"🌐 API request {attempt + 1}: {endpoint}")
                
                # Make request
                response = self.session.get(
                    url,
                    params=params,
                    headers=api_headers,
                    timeout=15
                )
                
                logger.info(f"📊 Response: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        clean_text = response.text.strip()
                        
                        if not clean_text:
                            logger.warning("Empty response")
                            continue
                        
                        data = json.loads(clean_text)
                        
                        # Validate and return data
                        if isinstance(data, list):
                            logger.info(f"✅ Success! Got {len(data)} records")
                            return data
                        elif isinstance(data, dict):
                            if 'data' in data:
                                logger.info(f"✅ Success! Got {len(data['data'])} records")
                                return data['data']
                            else:
                                logger.info("✅ Success! Got data object")
                                return data
                        
                        return None
                        
                    except json.JSONDecodeError:
                        logger.error("❌ Invalid JSON response")
                        continue
                
                elif response.status_code == 401:
                    logger.warning("🔑 Session expired (401) - refreshing...")
                    # Force session refresh and retry
                    self.session_active = False
                    if self._refresh_session_if_needed():
                        continue  # Retry with fresh session
                    else:
                        break
                
                elif response.status_code in [403, 429]:
                    logger.warning(f"🚫 Access restricted ({response.status_code}) - waiting longer...")
                    time.sleep(random.uniform(5, 10))
                    continue
                
                elif response.status_code == 503:
                    logger.warning("🔧 Service unavailable - retrying...")
                    time.sleep(random.uniform(3, 6))
                    continue
                
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code}")
                    break
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout on attempt {attempt + 1}")
                time.sleep(random.uniform(2, 4))
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"🔌 Connection error on attempt {attempt + 1}")
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                logger.error(f"❌ Request failed (attempt {attempt + 1}): {str(e)[:100]}")
                time.sleep(random.uniform(1, 3))
        
        logger.warning(f"💀 All attempts failed for: {endpoint}")
        return None
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.session:
                self.session.close()
            logger.info("🧹 NSE Session Manager cleaned up")
        except:
            pass

class NSEScraper:
    """NSE Scraper with Session Management"""
    
    def __init__(self):
        self.session_manager = NSESessionManager()
    
    def get_current_ipos(self) -> List[Dict]:
        """Get current IPOs from NSE only"""
        logger.info("\n📈 Fetching Current IPOs from NSE...")
        
        data = self.session_manager.make_api_request("/ipo-current-issue")
        
        if data and len(data) > 0:
            logger.info(f"✅ Found {len(data)} current IPOs from NSE")
            return data
        
        logger.info("📝 Using demo current IPOs")
        return self._get_demo_current_ipos()
    
    def get_upcoming_ipos(self) -> List[Dict]:
        """Get upcoming IPOs from NSE only"""
        logger.info("\n🔮 Fetching Upcoming IPOs from NSE...")
        
        data = self.session_manager.make_api_request("/all-upcoming-issues", {"category": "ipo"})
        
        if data and len(data) > 0:
            logger.info(f"✅ Found {len(data)} upcoming IPOs from NSE")
            return data
        
        logger.info("📝 Using demo upcoming IPOs")
        return self._get_demo_upcoming_ipos()
    
    def get_past_ipos(self, days_back: int = 30) -> List[Dict]:
        """Get past IPOs from NSE only"""
        logger.info(f"\n📊 Fetching Past IPOs from NSE (Last {days_back} days)...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=min(days_back, 90))
        
        params = {
            "from_date": start_date.strftime("%d-%m-%Y"),
            "to_date": end_date.strftime("%d-%m-%Y"),
            "security_type": "all"
        }
        
        data = self.session_manager.make_api_request("/public-past-issues", params)
        
        if data and len(data) > 0:
            logger.info(f"✅ Found {len(data)} past IPOs from NSE")
            return data
        
        logger.info("📝 No past IPO data available")
        return []
    
    def get_market_indices(self) -> List[Dict]:
        """Get market indices from NSE only"""
        logger.info("\n📊 Fetching Market Indices from NSE...")
        
        data = self.session_manager.make_api_request("/allIndices")
        
        if data and len(data) > 0:
            logger.info(f"✅ Found {len(data)} indices from NSE")
            return data
        
        logger.info("📝 Using demo market indices")
        return self._get_demo_indices()
    
    def get_market_status(self) -> List[Dict]:
        """Get market status from NSE only"""
        logger.info("\n🎯 Fetching Market Status from NSE...")
        
        data = self.session_manager.make_api_request("/marketStatus")
        
        if data and len(data) > 0:
            logger.info(f"✅ Found market status from NSE")
            return data
        
        # Fallback status
        return [{
            "market": "Capital Market",
            "marketStatus": "Open" if 9 <= datetime.now().hour <= 15 else "Closed",
            "tradeDate": datetime.now().strftime("%d-%b-%Y"),
            "index": "NIFTY 50"
        }]
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        current_time = time.time()
        
        return {
            "session_active": self.session_manager.session_active,
            "session_age_seconds": current_time - self.session_manager.session_created_at if self.session_manager.session_created_at else 0,
            "session_expires_in_seconds": self.session_manager.session_expires_at - current_time if self.session_manager.session_expires_at else 0,
            "last_request_seconds_ago": current_time - self.session_manager.last_request_time if self.session_manager.last_request_time else 0
        }
    
    def refresh_session(self) -> bool:
        """Manually refresh NSE session"""
        logger.info("🔄 Manual session refresh requested...")
        return self.session_manager._create_fresh_session()
    
    # Demo data methods (same as before)
    def _get_demo_current_ipos(self) -> List[Dict]:
        """Demo current IPOs"""
        return [
            {
                "symbol": "DEMO_CURRENT",
                "companyName": "Demo Current IPO Ltd",
                "series": "EQ",
                "issueStartDate": datetime.now().strftime("%d-%b-%Y"),
                "issueEndDate": (datetime.now() + timedelta(days=2)).strftime("%d-%b-%Y"),
                "issuePrice": "Rs.100 to Rs.120",
                "issueSize": "50000000",
                "status": "Active - Demo Data",
                "noOfTime": "1.25",
                "noOfSharesOffered": "5000000",
                "noOfsharesBid": "6250000"
            }
        ]
    
    def _get_demo_upcoming_ipos(self) -> List[Dict]:
        """Demo upcoming IPOs"""
        return [
            {
                "symbol": "DEMO_UPCOMING",
                "companyName": "Demo Upcoming IPO Ltd",
                "series": "EQ",
                "issueStartDate": (datetime.now() + timedelta(days=5)).strftime("%d-%b-%Y"),
                "issueEndDate": (datetime.now() + timedelta(days=8)).strftime("%d-%b-%Y"),
                "issuePrice": "Rs.200 to Rs.250",
                "issueSize": "75000000",
                "status": "Forthcoming"
            }
        ]
    
    def _get_demo_indices(self) -> List[Dict]:
        """Demo market indices"""
        return [
            {
                "indexName": "NIFTY 50",
                "last": 25847.75,
                "open": 25820.30,
                "high": 25889.60,
                "low": 25756.85,
                "previousClose": 25835.20,
                "change": 12.55,
                "percChange": 0.05,
                "yearHigh": 26277.35,
                "yearLow": 21281.45,
                "timeVal": datetime.now().strftime("%d-%b-%Y %H:%M")
            }
        ]
    
    def cleanup(self):
        """Cleanup resources"""
        self.session_manager.cleanup()