# ===============================================
# STEP 1: Create app/services/enhanced_nse_service.py
# ===============================================

import requests
import random
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os

class AntiBlockingNSEService:
    def __init__(self):
        self.base_url = "https://www.nseindia.com/api"
        self.session = requests.Session()
        
        # Multiple user agents to avoid blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
    def _make_request(self, url: str, params: dict = None, max_retries: int = 3):
        """Make request with anti-blocking features"""
        for attempt in range(max_retries):
            try:
                # Random user agent for each request
                self.session.headers.update(self.headers)
                self.session.headers['User-Agent'] = random.choice(self.user_agents)
                
                # Add random delay
                time.sleep(random.uniform(1, 3))
                
                print(f"🔄 Attempting request to: {url} (Attempt {attempt + 1})")
                
                # Make request
                response = self.session.get(url, params=params, timeout=30)
                
                print(f"📊 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Got {len(data) if isinstance(data, list) else 'data'} records")
                    return data
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 10
                    print(f"⏳ Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif response.status_code == 403:
                    wait_time = (attempt + 1) * 5
                    print(f"🚫 Blocked, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                    time.sleep(2)
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Request timeout on attempt {attempt + 1}")
                time.sleep(3)
            except requests.exceptions.ConnectionError:
                print(f"🔌 Connection error on attempt {attempt + 1}")
                time.sleep(5)
            except Exception as e:
                print(f"❌ Request failed (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)
        
        print(f"💀 All attempts failed for: {url}")
        return None
    
    def get_current_ipos(self):
        """Get current IPOs from NSE"""
        print("\n📈 Fetching Current IPOs...")
        url = f"{self.base_url}/ipo-current-issue"
        result = self._make_request(url)
        return result if result else []
    
    def get_upcoming_ipos(self):
        """Get upcoming IPOs from NSE"""
        print("\n🔮 Fetching Upcoming IPOs...")
        url = f"{self.base_url}/all-upcoming-issues"
        params = {"category": "ipo"}
        result = self._make_request(url, params)
        return result if result else []
    
    def get_past_ipos(self, days_back: int = 30):
        """Get past IPOs from NSE"""
        print(f"\n📊 Fetching Past IPOs (Last {days_back} days)...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        url = f"{self.base_url}/public-past-issues"
        params = {
            "from_date": start_date.strftime("%d-%m-%Y"),
            "to_date": end_date.strftime("%d-%m-%Y"),
            "security_type": "all"
        }
        result = self._make_request(url, params)
        return result if result else []
    
    def get_market_indices(self):
        """Get market indices from NSE"""
        print("\n📊 Fetching Market Indices...")
        url = f"{self.base_url}/allIndices"
        result = self._make_request(url)
        if result and isinstance(result, dict):
            return result.get('data', [])
        return result if result else []
    
    def get_market_status(self):
        """Get market status from NSE"""
        print("\n🎯 Fetching Market Status...")
        url = f"{self.base_url}/marketStatus"
        result = self._make_request(url)
        return result if result else []
