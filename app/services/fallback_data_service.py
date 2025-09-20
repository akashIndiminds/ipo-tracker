
# app/services/fallback_data_service.py
"""
Fallback data service when NSE APIs are completely blocked
"""
import json
import os
from datetime import datetime
from typing import Dict, List

class FallbackDataService:
    def __init__(self):
        self.fallback_dir = "fallback_data"
        os.makedirs(self.fallback_dir, exist_ok=True)
        
    def save_working_data(self, data_type: str, data: dict):
        """Save working data as fallback"""
        fallback_file = os.path.join(self.fallback_dir, f"{data_type}.json")
        
        fallback_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            with open(fallback_file, 'w') as f:
                json.dump(fallback_data, f, indent=2)
        except:
            pass
    
    def get_fallback_data(self, data_type: str) -> dict:
        """Get fallback data when APIs fail"""
        fallback_file = os.path.join(self.fallback_dir, f"{data_type}.json")
        
        if os.path.exists(fallback_file):
            try:
                with open(fallback_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Return minimal fallback data
        return self._get_minimal_fallback(data_type)
    
    def _get_minimal_fallback(self, data_type: str) -> dict:
        """Minimal hardcoded fallback data"""
        fallbacks = {
            'current_ipos': {
                'timestamp': datetime.now().isoformat(),
                'data': [
                    {
                        "symbol": "SAMPLE_IPO",
                        "companyName": "Sample Company Limited",
                        "issueStartDate": "20-Sep-2025",
                        "issueEndDate": "24-Sep-2025",
                        "issuePrice": "Rs.100 to Rs.110",
                        "status": "Active",
                        "noOfTime": "1.5"
                    }
                ]
            },
            'market_indices': {
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'data': [
                        {
                            "indexName": "NIFTY 50",
                            "last": 25300,
                            "percChange": -0.5,
                            "high": 25400,
                            "low": 25200
                        }
                    ]
                }
            }
        }
        
        return fallbacks.get(data_type, {'timestamp': datetime.now().isoformat(), 'data': []})

# app/services/proxy_service.py
"""
Proxy service for additional anti-blocking
"""
import requests
import random
from typing import Optional, List

class ProxyService:
    def __init__(self):
        # Free proxy lists (you can add more reliable ones)
        self.free_proxies = [
            # Add free proxy IPs here
            # Format: {"http": "http://proxy:port", "https": "https://proxy:port"}
        ]
        
        # Premium proxy services (recommended for production)
        self.premium_proxies = [
            # Add premium proxy endpoints here
        ]
        
        self.current_proxy = None
    
    def get_working_proxy(self) -> Optional[Dict]:
        """Find a working proxy"""
        all_proxies = self.premium_proxies + self.free_proxies
        random.shuffle(all_proxies)
        
        for proxy in all_proxies:
            if self._test_proxy(proxy):
                self.current_proxy = proxy
                return proxy
        
        return None
    
    def _test_proxy(self, proxy: dict, timeout: int = 10) -> bool:
        """Test if proxy is working"""
        try:
            response = requests.get(
                "https://httpbin.org/ip", 
                proxies=proxy, 
                timeout=timeout
            )
            return response.status_code == 200
        except:
            return False
    
    def make_proxy_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make request through proxy"""
        if not self.current_proxy:
            self.get_working_proxy()
        
        if self.current_proxy:
            kwargs['proxies'] = self.current_proxy
        
        try:
            return requests.get(url, **kwargs)
        except:
            # Try to get new proxy on failure
            self.get_working_proxy()
            return None
