# app/services/nse_service.py
import time
import random
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Set environment variables
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Import libraries
import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Import Brotli for 'br' encoding
try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False

# Disable SSL
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)

class NSEService:
    """NSE Service with smart caching and anti-detection"""
    
    def __init__(self):
        # NSE URLs
        self.base_url = "https://www.nseindia.com"
        self.api_base = "https://www.nseindia.com/api"
        
        # Session management with rotation
        self.sessions = []
        self.current_session_index = 0
        self.session_active = False
        self.request_count = 0
        self.last_session_time = 0
        self.blocked_until = 0
        
        # Smart caching
        self.cache = {}
        self.cache_duration = {
            'current_ipos': 3600,    # 1 hour
            'upcoming_ipos': 7200,   # 2 hours  
            'market_status': 1800    # 30 minutes
        }
        
        # Anti-detection measures
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/130.0.0.0'
        ]
        
        # Initialize
        self._create_session_pool()
        self._initialize_session()
    
    def _create_session_pool(self):
        """Create pool of sessions for rotation"""
        for i in range(3):
            session = requests.Session()
            session.verify = False
            self.sessions.append(session)
    
    def _get_current_session(self):
        """Get current session with rotation"""
        if not self.sessions:
            self._create_session_pool()
        return self.sessions[self.current_session_index]
    
    def _rotate_session(self):
        """Rotate to next session"""
        self.current_session_index = (self.current_session_index + 1) % len(self.sessions)
        logger.info(f"Rotated to session {self.current_session_index}")
    
    def _is_blocked(self):
        """Check if we're temporarily blocked"""
        return time.time() < self.blocked_until
    
    def _set_blocked(self, duration_minutes=30):
        """Set blocked status"""
        self.blocked_until = time.time() + (duration_minutes * 60)
        logger.warning(f"Marked as blocked for {duration_minutes} minutes")
    
    def _get_cache_key(self, endpoint, params=None):
        """Generate cache key"""
        key = endpoint
        if params:
            key += "_" + "_".join([f"{k}={v}" for k, v in sorted(params.items())])
        return key
    
    def _get_from_cache(self, cache_key, cache_type):
        """Get data from cache if valid"""
        if cache_key not in self.cache:
            return None
            
        cache_entry = self.cache[cache_key]
        cache_age = time.time() - cache_entry['timestamp']
        max_age = self.cache_duration.get(cache_type, 3600)
        
        if cache_age < max_age:
            logger.info(f"Cache hit for {cache_key} (age: {cache_age:.1f}s)")
            return cache_entry['data']
        else:
            # Remove expired cache
            del self.cache[cache_key]
            logger.info(f"Cache expired for {cache_key}")
            return None
    
    def _store_in_cache(self, cache_key, data):
        """Store data in cache"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        logger.info(f"Cached data for {cache_key}")
    
    def _get_random_headers(self, for_api=False):
        """Get randomized headers"""
        ua = random.choice(self.user_agents)
        
        if for_api:
            return {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Referer': 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo',
                'Sec-CH-UA': '"Chromium";v="130", "Not?A_Brand";v="99"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': ua,
                'X-Requested-With': 'XMLHttpRequest'
            }
        else:
            return {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'max-age=0',
                'Sec-CH-UA': '"Chromium";v="130", "Not?A_Brand";v="99"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': ua
            }
    
    def _decode_response(self, response):
        """Decode response safely"""
        try:
            content = response.content
            encoding = response.headers.get('content-encoding', '').lower()
            
            if encoding == 'br' and HAS_BROTLI:
                try:
                    content = brotli.decompress(content)
                except:
                    # Fallback to raw content if brotli fails
                    content = response.content
            elif encoding == 'gzip':
                import gzip
                content = gzip.decompress(content)
            
            return content.decode('utf-8', errors='ignore')
            
        except Exception as e:
            logger.warning(f"Decode error fallback: {e}")
            return response.text
    
    def _initialize_session(self):
        """Initialize session with anti-detection"""
        if self._is_blocked():
            logger.warning("Currently blocked, skipping session initialization")
            return False
            
        logger.info("Initializing NSE session with anti-detection...")
        
        try:
            session = self._get_current_session()
            
            # Step 1: Visit homepage with random delay
            time.sleep(random.uniform(3, 7))
            
            headers = self._get_random_headers(for_api=False)
            
            homepage_response = session.get(
                self.base_url,
                headers=headers,
                timeout=30,
                verify=False
            )
            
            if homepage_response.status_code != 200:
                logger.error(f"Homepage failed: {homepage_response.status_code}")
                self._rotate_session()
                return False
            
            logger.info("Homepage loaded successfully")
            
            # Step 2: Random browsing simulation
            time.sleep(random.uniform(5, 10))
            
            # Visit IPO section
            ipo_page_url = f"{self.base_url}/market-data/all-upcoming-issues-ipo"
            headers = self._get_random_headers(for_api=False)
            headers['Referer'] = self.base_url
            
            ipo_response = session.get(
                ipo_page_url,
                headers=headers,
                timeout=30,
                verify=False
            )
            
            if ipo_response.status_code == 200:
                logger.info("IPO page loaded - session ready")
                self.session_active = True
                self.last_session_time = time.time()
                return True
            else:
                logger.warning(f"IPO page status: {ipo_response.status_code}")
                self.session_active = True  # Try anyway
                return True
                
        except Exception as e:
            logger.error(f"Session initialization failed: {e}")
            self._rotate_session()
            return False
    
    def _make_api_call(self, endpoint, params=None, cache_type=None):
        """Make API call with caching and anti-detection"""
        
        # Check cache first
        if cache_type:
            cache_key = self._get_cache_key(endpoint, params)
            cached_data = self._get_from_cache(cache_key, cache_type)
            if cached_data:
                return cached_data
        
        # Check if blocked
        if self._is_blocked():
            logger.warning("Currently blocked, returning cached data if available")
            return self.cache.get(cache_key, {}).get('data', []) if cache_type else []
        
        # Session management
        if not self.session_active or self.request_count > 15:
            logger.info("Refreshing session...")
            if not self._initialize_session():
                logger.error("Session refresh failed")
                return []
        
        # Smart rate limiting
        time.sleep(random.uniform(5, 12))
        
        # Build URL  
        url = f"{self.api_base}{endpoint}"
        if params:
            query_params = '&'.join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_params}"
        
        try:
            session = self._get_current_session()
            headers = self._get_random_headers(for_api=True)
            
            logger.info(f"API Call: {endpoint}")
            
            response = session.get(
                url,
                headers=headers,
                timeout=25,
                verify=False
            )
            
            self.request_count += 1
            
            logger.info(f"Response: {response.status_code}")
            
            if response.status_code == 200:
                decoded_text = self._decode_response(response)
                
                try:
                    data = json.loads(decoded_text)
                    
                    if isinstance(data, list):
                        logger.info(f"Got {len(data)} items")
                        # Cache successful response
                        if cache_type:
                            self._store_in_cache(cache_key, data)
                        return data
                    elif isinstance(data, dict):
                        logger.info("Got data object")
                        result = [data] if data else []
                        if cache_type:
                            self._store_in_cache(cache_key, result)
                        return result
                    else:
                        return data if data else []
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode failed: {e}")
                    return []
                    
            elif response.status_code == 401:
                logger.error("401 Unauthorized - rotating session")
                self.session_active = False
                self._rotate_session()
                return []
                
            elif response.status_code == 403:
                logger.error("403 Forbidden - setting blocked status")
                self.session_active = False
                self._set_blocked(30)  # Block for 30 minutes
                return []
                
            elif response.status_code == 429:
                logger.error("429 Rate Limited - setting blocked status")
                self._set_blocked(60)  # Block for 1 hour
                return []
                
            else:
                logger.error(f"Unexpected status: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"API call failed: {e}")
            self._rotate_session()
            return []
    
    def fetch_current_ipos(self) -> List[Dict]:
        """Fetch current IPOs with caching"""
        logger.info("Fetching current IPOs...")
        
        data = self._make_api_call('/ipo-current-issue', cache_type='current_ipos')
        
        if data and len(data) > 0:
            return self._process_ipo_data(data)
        
        logger.warning("No current IPO data")
        return []
    
    def fetch_upcoming_ipos(self) -> List[Dict]:
        """Fetch upcoming IPOs with caching"""
        logger.info("Fetching upcoming IPOs...")
        
        data = self._make_api_call('/all-upcoming-issues', {'category': 'ipo'}, cache_type='upcoming_ipos')
        
        if data and len(data) > 0:
            return self._process_ipo_data(data)
        
        logger.warning("No upcoming IPO data")
        return []
    
    def fetch_market_status(self) -> List[Dict]:
        """Fetch market status with correct endpoint"""
        logger.info("Fetching market status...")
        
        # Fixed endpoint - it's marketStatus not marketstatus
        data = self._make_api_call('/marketstatus', cache_type='marketstatus')
        
        if data and len(data) > 0:
            return self._process_market_data(data)
        
        logger.warning("No market status data")
        return []
    
    def _process_ipo_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Process IPO data"""
        processed = []
        
        for item in raw_data:
            try:
                processed_item = {
                    'symbol': str(item.get('symbol', '')).strip(),
                    'company_name': str(item.get('companyName', '')).strip(),
                    'series': str(item.get('series', 'EQ')).strip(),
                    'issue_start_date': str(item.get('issueStartDate', '')).strip(),
                    'issue_end_date': str(item.get('issueEndDate', '')).strip(),
                    'issue_price': str(item.get('issuePrice', '')).strip(),
                    'issue_size': str(item.get('issueSize', '0')).strip(),
                    'status': str(item.get('status', 'Unknown')).strip(),
                    'subscription_times': self._safe_float(item.get('noOfTime', 0)),
                    'shares_offered': self._safe_int(item.get('noOfSharesOffered', 0)),
                    'shares_bid': self._safe_int(item.get('noOfsharesBid', 0)),
                    'is_sme': bool(item.get('isBse', '0') == '1'),
                    'category': str(item.get('category', 'Total')).strip()
                }
                
                if processed_item['symbol'] and processed_item['company_name']:
                    processed.append(processed_item)
                    
            except Exception as e:
                logger.warning(f"Processing error: {e}")
                continue
        
        logger.info(f"Processed {len(processed)} IPOs")
        return processed
    
    def _process_market_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Process market status data"""
        processed = []
        
        for item in raw_data:
            try:
                processed_item = {
                    'market': str(item.get('market', '')).strip(),
                    'market_status': str(item.get('marketstatus', '')).strip(),
                    'trade_date': str(item.get('tradeDate', '')).strip(),
                    'index': str(item.get('index', '')).strip()
                }
                
                if processed_item['market']:
                    processed.append(processed_item)
                    
            except Exception as e:
                logger.warning(f"Processing error: {e}")
                continue
        
        logger.info(f"Processed {len(processed)} market records")
        return processed
    
    def _safe_int(self, value) -> int:
        try:
            if isinstance(value, str):
                if 'E' in value.upper():
                    return int(float(value))
                return int(float(value.replace(',', '')))
            return int(float(value)) if value else 0
        except:
            return 0
    
    def _safe_float(self, value) -> float:
        try:
            if isinstance(value, str):
                return float(value.replace(',', ''))
            return float(value) if value else 0.0
        except:
            return 0.0
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            'session_active': self.session_active,
            'current_scraper': f'session_{self.current_session_index}',
            'request_count': self.request_count,
            'cache_size': len(self.cache),
            'blocked_until': self.blocked_until,
            'is_blocked': self._is_blocked(),
            'sessions_count': len(self.sessions)
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test NSE connection"""
        logger.info("Testing NSE connection...")
        
        results = {
            'session_creation': False,
            'api_access': False,
            'current_ipos': False,
            'market_status': False,
            'overall_status': 'failed',
            'scrapers_working': [],
            'scrapers_failed': []
        }
        
        # Test session
        if self._initialize_session():
            results['session_creation'] = True
            results['scrapers_working'].append('session_init')
        else:
            results['scrapers_failed'].append('session_init')
        
        # Test endpoints only if not blocked
        if results['session_creation'] and not self._is_blocked():
            try:
                current_data = self.fetch_current_ipos()
                if current_data and len(current_data) > 0:
                    results['current_ipos'] = True
                    results['api_access'] = True
                    results['scrapers_working'].append('current_ipos')
                else:
                    results['scrapers_failed'].append('current_ipos')
            except:
                results['scrapers_failed'].append('current_ipos')
            
            try:
                market_data = self.fetch_market_status()
                if market_data and len(market_data) > 0:
                    results['market_status'] = True
                    results['api_access'] = True
                    results['scrapers_working'].append('market_status')
                else:
                    results['scrapers_failed'].append('market_status')
            except:
                results['scrapers_failed'].append('market_status')
        
        # Overall status
        if results['api_access']:
            results['overall_status'] = 'working'
        elif results['session_creation']:
            results['overall_status'] = 'partial'
        
        return results
    
    def clear_cache(self):
        """Clear cache manually"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def force_refresh(self):
        """Force refresh session and clear cache"""
        self.clear_cache()
        self.session_active = False
        self.blocked_until = 0
        return self._initialize_session()
    
    def cleanup(self):
        """Cleanup all sessions"""
        try:
            for session in self.sessions:
                session.close()
            self.sessions.clear()
            self.session_active = False
            logger.info("All sessions cleanup completed")
        except:
            pass

# Create service instance
nse_service = NSEService()