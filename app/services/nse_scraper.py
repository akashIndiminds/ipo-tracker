# app/services/nse_scraper.py
"""NSE Scraper - Handles connection, session management, and anti-detection"""

import time
import random
import json
import os
from typing import Dict, List, Optional, Any
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning

# Disable warnings and SSL verification
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
os.environ['PYTHONHTTPSVERIFY'] = '0'

try:
    import brotli
    HAS_BROTLI = True
except ImportError:
    HAS_BROTLI = False

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)

class NSEScraper:
    """NSE Scraper with smart session management and anti-detection"""
    
    def __init__(self):
        # NSE URLs
        self.base_url = "https://www.nseindia.com"
        self.api_base = "https://www.nseindia.com/api"
        
        # Session management
        self.sessions = []
        self.current_session_index = 0
        self.session_active = False
        self.request_count = 0
        self.last_session_time = 0
        self.blocked_until = 0
        
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
            
        logger.info("Initializing NSE session...")
        
        try:
            session = self._get_current_session()
            
            # Visit homepage
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
            
            # Visit IPO section
            time.sleep(random.uniform(5, 10))
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
                self.session_active = True
                return True
                
        except Exception as e:
            logger.error(f"Session initialization failed: {e}")
            self._rotate_session()
            return False
    
    def make_api_call(self, endpoint, params=None):
        """Make API call with anti-detection and error handling"""
        
        # Check if blocked
        if self._is_blocked():
            logger.warning("Currently blocked, cannot make API call")
            return None
        
        # Session management
        if not self.session_active or self.request_count > 15:
            logger.info("Refreshing session...")
            if not self._initialize_session():
                logger.error("Session refresh failed")
                return None
        
        # Rate limiting
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
                    logger.info(f"Successfully fetched data from {endpoint}")
                    return data
                        
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode failed: {e}")
                    return None
                    
            elif response.status_code == 401:
                logger.error("401 Unauthorized - rotating session")
                self.session_active = False
                self._rotate_session()
                return None
                
            elif response.status_code == 403:
                logger.error("403 Forbidden - setting blocked status")
                self.session_active = False
                self._set_blocked(30)
                return None
                
            elif response.status_code == 429:
                logger.error("429 Rate Limited - setting blocked status")
                self._set_blocked(60)
                return None
                
            else:
                logger.error(f"Unexpected status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"API call failed: {e}")
            self._rotate_session()
            return None
    
    def force_refresh(self):
        """Force refresh session"""
        self.session_active = False
        self.blocked_until = 0
        self.request_count = 0
        return self._initialize_session()
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            'session_active': self.session_active,
            'current_session': self.current_session_index,
            'request_count': self.request_count,
            'blocked_until': self.blocked_until,
            'is_blocked': self._is_blocked(),
            'sessions_count': len(self.sessions)
        }
    
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

# Create scraper instance
nse_scraper = NSEScraper()