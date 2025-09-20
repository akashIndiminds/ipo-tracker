# app/services/monitoring_service.py
"""
Monitoring service to track API health and performance
"""
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
from dataclasses import dataclass

@dataclass
class APIHealthStatus:
    endpoint: str
    status: str  # healthy, degraded, down
    response_time: float
    last_check: datetime
    error_count: int
    success_rate: float

class MonitoringService:
    def __init__(self):
        self.health_status = {}
        self.error_log = []
        self.performance_metrics = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/ipo_tracker.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def check_api_health(self, nse_service) -> Dict[str, APIHealthStatus]:
        """Check health of all NSE APIs"""
        endpoints = {
            'current_ipos': nse_service.get_current_ipos,
            'upcoming_ipos': nse_service.get_upcoming_ipos,
            'past_ipos': lambda: nse_service.get_past_ipos(7),
            'market_indices': nse_service.get_market_indices,
            'market_status': nse_service.get_market_status
        }
        
        health_results = {}
        
        for endpoint_name, endpoint_func in endpoints.items():
            start_time = time.time()
            
            try:
                result = endpoint_func()
                response_time = time.time() - start_time
                
                if result:
                    status = "healthy"
                    self._log_success(endpoint_name, response_time)
                else:
                    status = "degraded"
                    self._log_error(endpoint_name, "Empty response")
                
            except Exception as e:
                response_time = time.time() - start_time
                status = "down"
                self._log_error(endpoint_name, str(e))
            
            # Calculate success rate
            success_rate = self._calculate_success_rate(endpoint_name)
            
            health_results[endpoint_name] = APIHealthStatus(
                endpoint=endpoint_name,
                status=status,
                response_time=response_time,
                last_check=datetime.now(),
                error_count=self._get_error_count(endpoint_name),
                success_rate=success_rate
            )
        
        return health_results
    
    def _log_success(self, endpoint: str, response_time: float):
        """Log successful API call"""
        self.logger.info(f"✅ {endpoint} - Success - {response_time:.2f}s")
        
        # Store performance metric
        self.performance_metrics.append({
            'endpoint': endpoint,
            'timestamp': datetime.now(),
            'response_time': response_time,
            'status': 'success'
        })
        
        # Keep only last 1000 metrics
        if len(self.performance_metrics) > 1000:
            self.performance_metrics = self.performance_metrics[-1000:]
    
    def _log_error(self, endpoint: str, error: str):
        """Log API error"""
        self.logger.error(f"❌ {endpoint} - Error: {error}")
        
        # Store error
        self.error_log.append({
            'endpoint': endpoint,
            'timestamp': datetime.now(),
            'error': error
        })
        
        # Keep only last 500 errors
        if len(self.error_log) > 500:
            self.error_log = self.error_log[-500:]
    
    def _calculate_success_rate(self, endpoint: str, hours_back: int = 24) -> float:
        """Calculate success rate for endpoint in last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        recent_metrics = [
            m for m in self.performance_metrics 
            if m['endpoint'] == endpoint and m['timestamp'] > cutoff_time
        ]
        
        if not recent_metrics:
            return 0.0
        
        successful_calls = len([m for m in recent_metrics if m['status'] == 'success'])
        total_calls = len(recent_metrics)
        
        return (successful_calls / total_calls) * 100
    
    def _get_error_count(self, endpoint: str, hours_back: int = 24) -> int:
        """Get error count for endpoint in last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        recent_errors = [
            e for e in self.error_log 
            if e['endpoint'] == endpoint and e['timestamp'] > cutoff_time
        ]
        
        return len(recent_errors)
    
    def get_system_health_summary(self) -> Dict:
        """Get overall system health summary"""
        if not self.health_status:
            return {"status": "unknown", "message": "No health data available"}
        
        all_statuses = [status.status for status in self.health_status.values()]
        
        if all(status == "healthy" for status in all_statuses):
            overall_status = "healthy"
        elif any(status == "down" for status in all_statuses):
            overall_status = "degraded"
        else:
            overall_status = "degraded"
        
        avg_response_time = sum(status.response_time for status in self.health_status.values()) / len(self.health_status)
        avg_success_rate = sum(status.success_rate for status in self.health_status.values()) / len(self.health_status)
        
        return {
            "overall_status": overall_status,
            "average_response_time": round(avg_response_time, 2),
            "average_success_rate": round(avg_success_rate, 2),
            "endpoints": {name: status.__dict__ for name, status in self.health_status.items()},
            "last_updated": datetime.now().isoformat()
        }

