# app/services/nse_scraper_service.py
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
                logger.info("NSE Session: Creating fresh session...")

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
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Cache-Control": "max-age=0",
                })

                # Visit NSE homepage to establish session
                response = self.session.get(self.base_url, timeout=20)

                if response.status_code == 200:
                    current_time = time.time()
                    self.session_created_at = current_time
                    self.session_expires_at = current_time + self.session_duration
                    self.session_active = True
                    logger.info("NSE Session: Created successfully")
                    return True
                else:
                    logger.error(f"NSE Session: Homepage returned {response.status_code}")
                    self.session_active = False
                    return False

            except Exception as e:
                logger.error(f"NSE Session: Creation failed - {e}")
                self.session_active = False
                return False

    def _is_session_expired(self):
        """Check if current session is expired"""
        current_time = time.time()
        return current_time >= self.session_expires_at

    def _refresh_session_if_needed(self):
        """Refresh session if needed"""
        if not self.session_active or self._is_session_expired():
            logger.info("NSE Session: Refresh needed")
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
            logger.error("NSE Session: Cannot establish session")
            return None

        url = f"{self.api_base}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                self._rate_limit()

                # Set API-specific headers
                api_headers = {
                    "Accept": "application/json, text/plain, */*",
                    "Referer": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
                    "X-Requested-With": "XMLHttpRequest",
                }

                logger.info(f"NSE API: {endpoint} (attempt {attempt + 1})")

                # Make request
                response = self.session.get(url, params=params, headers=api_headers, timeout=15)
                logger.info(f"NSE API: Response {response.status_code}")

                if response.status_code == 200:
                    try:
                        clean_text = response.text.strip()
                        if not clean_text:
                            logger.warning("NSE API: Empty response")
                            continue

                        data = json.loads(clean_text)

                        # Validate and return data
                        if isinstance(data, list):
                            logger.info(f"NSE API: Success - {len(data)} records")
                            return data
                        elif isinstance(data, dict):
                            if "data" in data:
                                logger.info(f"NSE API: Success - {len(data['data'])} records")
                                return data["data"]
                            else:
                                logger.info("NSE API: Success - data object")
                                return data
                        return None

                    except json.JSONDecodeError:
                        logger.error("NSE API: Invalid JSON response")
                        continue

                elif response.status_code == 401:
                    logger.warning("NSE API: Session expired (401)")
                    self.session_active = False
                    if self._refresh_session_if_needed():
                        continue
                    else:
                        break

                elif response.status_code in [403, 429]:
                    logger.warning(f"NSE API: Access restricted ({response.status_code})")
                    time.sleep(random.uniform(5, 10))
                    continue

                else:
                    logger.warning(f"NSE API: HTTP {response.status_code}")
                    break

            except requests.exceptions.Timeout:
                logger.warning(f"NSE API: Timeout (attempt {attempt + 1})")
                time.sleep(random.uniform(2, 4))

            except Exception as e:
                logger.error(f"NSE API: Request failed (attempt {attempt + 1}): {str(e)[:100]}")
                time.sleep(random.uniform(1, 3))

        logger.warning(f"NSE API: All attempts failed for {endpoint}")
        return None

    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.session:
                self.session.close()
            logger.info("NSE Session: Cleaned up")
        except:
            pass

class NSEScraperService:
    """NSE Scraper Service - Handles all NSE API interactions"""

    def __init__(self):
        self.session_manager = NSESessionManager()

        # NSE API Endpoints
        self.endpoints = {
            "current_ipos": "/ipo-current-issue",
            "upcoming_ipos": "/all-upcoming-issues",
            "subscription_detail": "/ipo-active-category",
            "market_status": "/marketStatus",
        }

    def get_current_ipos(self) -> List[Dict]:
        """Get current IPOs from NSE"""
        logger.info("NSE Scraper: Fetching current IPOs")
        
        data = self.session_manager.make_api_request(self.endpoints["current_ipos"])
        
        if data is None:
            logger.warning("NSE Scraper: No current IPO data found")
            return []
        
        cleaned_data = self._clean_ipo_data(data)
        logger.info(f"NSE Scraper: Got {len(cleaned_data)} current IPOs")
        return cleaned_data

    def get_upcoming_ipos(self) -> List[Dict]:
        """Get upcoming IPOs from NSE"""
        logger.info("NSE Scraper: Fetching upcoming IPOs")
        
        params = {"category": "ipo"}
        data = self.session_manager.make_api_request(self.endpoints["upcoming_ipos"], params)
        
        if data is None:
            logger.warning("NSE Scraper: No upcoming IPO data found")
            return []
        
        cleaned_data = self._clean_ipo_data(data)
        logger.info(f"NSE Scraper: Got {len(cleaned_data)} upcoming IPOs")
        return cleaned_data

    def _clean_ipo_data(self, data: List[Dict]) -> List[Dict]:
        """Clean IPO data to ensure compatibility and correct types"""
        cleaned_data = []
        
        for item in data:
            try:
                cleaned_item = item.copy()
                
                # Convert to proper types
                cleaned_item['noOfSharesOffered'] = self._safe_int(item.get('noOfSharesOffered', 0))
                cleaned_item['noOfsharesBid'] = self._safe_int(item.get('noOfsharesBid', 0))
                cleaned_item['noOfTime'] = self._safe_float(item.get('noOfTime', '0.00'))
                
                # Ensure required fields have default values if missing
                cleaned_item['symbol'] = item.get('symbol', '')
                cleaned_item['companyName'] = item.get('companyName', '')
                cleaned_item['series'] = item.get('series', 'EQ')
                cleaned_item['issueStartDate'] = item.get('issueStartDate', '')
                cleaned_item['issueEndDate'] = item.get('issueEndDate', '')
                cleaned_item['issuePrice'] = item.get('issuePrice', '')
                cleaned_item['issueSize'] = item.get('issueSize', '0')
                cleaned_item['status'] = item.get('status', 'Upcoming' if 'upcoming' in self.endpoints else 'Active')
                
                if cleaned_item['symbol'] and cleaned_item['companyName']:
                    cleaned_data.append(cleaned_item)
                
            except Exception as e:
                logger.warning(f"NSE Scraper: Error cleaning IPO item: {e}")
                continue
        
        return cleaned_data

    def get_detailed_subscription(self, symbol: str) -> Optional[Dict]:
        """Get detailed subscription data for specific IPO"""
        logger.info(f"NSE Scraper: Fetching subscription for {symbol}")
        
        params = {"symbol": symbol.upper()}
        data = self.session_manager.make_api_request(self.endpoints["subscription_detail"], params)
        
        if data is None:
            logger.warning(f"NSE Scraper: No subscription data for {symbol}")
            return None
        
        processed_data = self._process_subscription_data(data, symbol)
        logger.info(f"NSE Scraper: Processed subscription data for {symbol}")
        return processed_data

    def get_market_status(self) -> List[Dict]:
        """Get market status from NSE"""
        logger.info("NSE Scraper: Fetching market status")
        
        data = self.session_manager.make_api_request(self.endpoints["market_status"])
        
        if data is None:
            logger.warning("NSE Scraper: No market status data found")
            return []
        
        logger.info(f"NSE Scraper: Got {len(data)} market status records")
        return data

    def _process_subscription_data(self, raw_data: Dict, symbol: str) -> Dict[str, Any]:
        """Process raw NSE subscription data into clean format"""
        try:
            processed = {
                "symbol": symbol,
                "last_updated": raw_data.get("updateTime", datetime.now().isoformat()),
                "total_subscription": "0.00x",
                "categories": {},
                "raw_data_available": True,
            }

            data_list = raw_data.get("dataList", [])

            for item in data_list:
                category = item.get("category", "")
                subscription_times = item.get("noOfTotalMeant", "0")
                shares_offered = self._safe_int(item.get("noOfShareOffered", "0"))
                shares_bid = self._safe_int(item.get("noOfSharesBid", "0"))

                # Skip header row
                if category == "Category":
                    continue

                # Process main categories
                if category == "Qualified Institutional Buyers(QIBs)":
                    processed["categories"]["QIB"] = {
                        "category_name": "Qualified Institutional Buyers",
                        "subscription_times": self._format_subscription(subscription_times),
                        "subscription_times_numeric": self._safe_float(subscription_times),
                        "shares_offered": shares_offered,
                        "shares_bid": shares_bid,
                        "status": self._get_subscription_status(self._safe_float(subscription_times)),
                    }

                elif category == "Non Institutional Investors":
                    processed["categories"]["NII"] = {
                        "category_name": "Non-Institutional Investors",
                        "subscription_times": self._format_subscription(subscription_times),
                        "subscription_times_numeric": self._safe_float(subscription_times),
                        "shares_offered": shares_offered,
                        "shares_bid": shares_bid,
                        "status": self._get_subscription_status(self._safe_float(subscription_times)),
                    }

                elif category == "Retail Individual Investors(RIIs)":
                    processed["categories"]["RII"] = {
                        "category_name": "Retail Individual Investors",
                        "subscription_times": self._format_subscription(subscription_times),
                        "subscription_times_numeric": self._safe_float(subscription_times),
                        "shares_offered": shares_offered,
                        "shares_bid": shares_bid,
                        "status": self._get_subscription_status(self._safe_float(subscription_times)),
                    }

                elif category == "Employees":
                    processed["categories"]["Employee"] = {
                        "category_name": "Employees",
                        "subscription_times": self._format_subscription(subscription_times),
                        "subscription_times_numeric": self._safe_float(subscription_times),
                        "shares_offered": shares_offered,
                        "shares_bid": shares_bid,
                        "status": self._get_subscription_status(self._safe_float(subscription_times)),
                    }

                elif category == "Total":
                    processed["total_subscription"] = self._format_subscription(subscription_times)
                    processed["total_subscription_numeric"] = self._safe_float(subscription_times)
                    processed["overall_status"] = self._get_subscription_status(self._safe_float(subscription_times))

            return processed

        except Exception as e:
            logger.error(f"NSE Scraper: Error processing subscription data - {e}")
            return {
                "symbol": symbol,
                "error": "Failed to process",
                "raw_data_available": False,
            }

    def _format_subscription(self, subscription_times: str) -> str:
        """Format subscription times like '3.07x'"""
        try:
            if not subscription_times or subscription_times == "":
                return "0.00x"
            num_value = float(subscription_times)
            return f"{num_value:.2f}x"
        except (ValueError, TypeError):
            return "0.00x"

    def _get_subscription_status(self, subscription_numeric: float) -> str:
        """Get subscription status based on numeric value"""
        if subscription_numeric >= 5:
            return "Highly Oversubscribed"
        elif subscription_numeric >= 2:
            return "Oversubscribed"
        elif subscription_numeric >= 1:
            return "Fully Subscribed"
        elif subscription_numeric >= 0.5:
            return "Moderately Subscribed"
        else:
            return "Undersubscribed"

    def _safe_int(self, value: Any) -> int:
        """Safely convert to integer"""
        try:
            if value is None or str(value).strip() == "" or value == "null":
                return 0
            if "E" in str(value).upper():
                return int(float(value))
            clean_value = str(value).replace(",", "").strip()
            return int(float(clean_value))
        except (ValueError, TypeError):
            return 0

    def _safe_float(self, value: Any) -> float:
        """Safely convert to float"""
        try:
            if value is None or str(value).strip() == "" or value == "null":
                return 0.0
            if "E" in str(value).upper():
                return float(value)
            clean_value = str(value).replace(",", "").strip()
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0

    # Session Management
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        current_time = time.time()
        return {
            "service": "NSE_API",
            "session_active": self.session_manager.session_active,
            "session_age_seconds": (
                current_time - self.session_manager.session_created_at
                if self.session_manager.session_created_at
                else 0
            ),
            "session_expires_in_seconds": (
                self.session_manager.session_expires_at - current_time
                if self.session_manager.session_expires_at
                else 0
            ),
            "last_request_seconds_ago": (
                current_time - self.session_manager.last_request_time
                if self.session_manager.last_request_time
                else 0
            ),
        }

    def refresh_session(self) -> bool:
        """Manually refresh NSE session"""
        logger.info("NSE Scraper: Manual session refresh requested")
        return self.session_manager._create_fresh_session()

    def cleanup(self):
        """Cleanup resources"""
        self.session_manager.cleanup()
        logger.info("NSE Scraper Service: Cleaned up")

# Create service instance
nse_scraper_service = NSEScraperService()