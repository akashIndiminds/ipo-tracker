# app/services/ipo_service.py
from typing import Dict, Any, List
import logging
from datetime import datetime

from app.services.nse_scraper_service import nse_scraper_service
from app.services.storage_service import storage_service
from app.services.data_processor import DataProcessor  # ✅ Fixed

logger = logging.getLogger(__name__)

class IPOService:
    """IPO Service - Contains all business logic"""

    def __init__(self):
        self.nse_scraper = nse_scraper_service
        self.storage = storage_service
        self.processor = DataProcessor  # ✅ Class reference (static methods के लिए)

    async def get_current_ipos(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Business logic for current IPOs"""
        try:
            logger.info("IPO Service: Processing current IPOs request")
            
            # Check cache first unless force refresh
            if not force_refresh:
                cached_data = self.storage.get_cached_data("current_ipos")
                if cached_data:
                    logger.info("Returning cached current IPO data")
                    return {
                        "success": True,
                        "message": f"Retrieved {len(cached_data['data'])} current IPOs from cache",
                        "data": cached_data["data"],
                        "count": len(cached_data["data"]),
                        "metadata": {
                            "source": "cache",
                            "cache_age_seconds": self.storage.get_data_age("current_ipos"),
                            "is_cached": True
                        }
                    }

            # Fetch fresh data from NSE
            logger.info("Fetching fresh current IPO data from NSE")
            raw_data = self.nse_scraper.get_current_ipos()
            
            if not raw_data:
                return {
                    "success": False,
                    "message": "No current IPO data available from NSE",
                    "data": [],
                    "count": 0
                }

            # Process and clean data
            processed_data = self.processor.clean_ipo_data(raw_data)
            
            # Store processed data
            save_success = self.storage.save_data("current_ipos", processed_data, "NSE_API")
            
            return {
                "success": True,
                "message": f"Retrieved {len(processed_data)} current IPOs",
                "data": processed_data,
                "count": len(processed_data),
                "metadata": {
                    "source": "NSE_API",
                    "is_cached": False,
                    "saved_to_storage": save_success,
                    "processed_records": len(processed_data),
                    "raw_records": len(raw_data)
                }
            }

        except Exception as e:
            logger.error(f"IPO Service error - current IPOs: {e}")
            return {
                "success": False,
                "message": f"Failed to get current IPOs: {str(e)}",
                "data": [],
                "count": 0
            }

    async def get_upcoming_ipos(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Business logic for upcoming IPOs"""
        try:
            logger.info("IPO Service: Processing upcoming IPOs request")
            
            # Check cache first unless force refresh
            if not force_refresh:
                cached_data = self.storage.get_cached_data("upcoming_ipos")
                if cached_data:
                    logger.info("Returning cached upcoming IPO data")
                    return {
                        "success": True,
                        "message": f"Retrieved {len(cached_data['data'])} upcoming IPOs from cache",
                        "data": cached_data["data"],
                        "count": len(cached_data["data"]),
                        "metadata": {
                            "source": "cache",
                            "cache_age_seconds": self.storage.get_data_age("upcoming_ipos"),
                            "is_cached": True
                        }
                    }

            # Fetch fresh data from NSE
            logger.info("Fetching fresh upcoming IPO data from NSE")
            raw_data = self.nse_scraper.get_upcoming_ipos()
            
            if not raw_data:
                return {
                    "success": False,
                    "message": "No upcoming IPO data available from NSE",
                    "data": [],
                    "count": 0
                }

            # Process and clean data
            processed_data = self.processor.clean_ipo_data(raw_data)
            
            # Store processed data
            save_success = self.storage.save_data("upcoming_ipos", processed_data, "NSE_API")
            
            return {
                "success": True,
                "message": f"Retrieved {len(processed_data)} upcoming IPOs",
                "data": processed_data,
                "count": len(processed_data),
                "metadata": {
                    "source": "NSE_API",
                    "is_cached": False,
                    "saved_to_storage": save_success,
                    "processed_records": len(processed_data),
                    "raw_records": len(raw_data)
                }
            }

        except Exception as e:
            logger.error(f"IPO Service error - upcoming IPOs: {e}")
            return {
                "success": False,
                "message": f"Failed to get upcoming IPOs: {str(e)}",
                "data": [],
                "count": 0
            }

    async def get_subscription_details(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Business logic for subscription details"""
        try:
            logger.info(f"IPO Service: Processing subscription request for {symbol}")
            
            cache_key = f"subscription_{symbol.upper()}"
            
            # Register dynamic cache key if needed
            self.storage.register_data_type(cache_key, f"{cache_key}.json", 300)  # 5 min cache
            
            # Check cache first unless force refresh
            if not force_refresh:
                cached_data = self.storage.get_cached_data(cache_key)
                if cached_data and cached_data["data"]:
                    logger.info(f"Returning cached subscription data for {symbol}")
                    return {
                        "success": True,
                        "message": f"Retrieved subscription data for {symbol} from cache",
                        "subscription_data": cached_data["data"][0],
                        "from_cache": True,
                        "cache_age": self.storage.get_data_age(cache_key)
                    }

            # Fetch fresh subscription data from NSE
            logger.info(f"Fetching fresh subscription data for {symbol} from NSE")
            subscription_data = self.nse_scraper.get_detailed_subscription(symbol)
            
            if not subscription_data:
                return {
                    "success": False,
                    "message": f"No subscription data available for {symbol}",
                    "subscription_data": {},
                    "from_cache": False
                }

            # Store subscription data
            save_success = self.storage.save_data(cache_key, [subscription_data], "NSE_SUBSCRIPTION_API")
            
            return {
                "success": True,
                "message": f"Retrieved subscription data for {symbol}",
                "subscription_data": subscription_data,
                "from_cache": False,
                "saved_to_storage": save_success
            }

        except Exception as e:
            logger.error(f"IPO Service error - subscription {symbol}: {e}")
            return {
                "success": False,
                "message": f"Failed to get subscription data for {symbol}: {str(e)}",
                "subscription_data": {},
                "from_cache": False
            }

    async def get_market_status(self) -> Dict[str, Any]:
        """Business logic for market status"""
        try:
            logger.info("IPO Service: Processing market status request")
            
            # Market status can be cached for shorter duration (5 minutes)
            cached_data = self.storage.get_cached_data("market_status")
            cache_age = self.storage.get_data_age("market_status") or 0
            
            if cached_data and cache_age < 300:  # 5 minutes
                logger.info("Returning cached market status")
                return {
                    "success": True,
                    "message": "Market status retrieved from cache",
                    "data": cached_data["data"],
                    "from_cache": True,
                    "cache_age_seconds": cache_age
                }

            # Fetch fresh market status from NSE
            logger.info("Fetching fresh market status from NSE")
            market_data = self.nse_scraper.get_market_status()
            
            if not market_data:
                return {
                    "success": False,
                    "message": "No market status data available",
                    "data": [],
                    "from_cache": False
                }

            # Store market status
            save_success = self.storage.save_data("market_status", market_data, "NSE_API")
            
            return {
                "success": True,
                "message": f"Retrieved market status with {len(market_data)} records",
                "data": market_data,
                "from_cache": False,
                "saved_to_storage": save_success
            }

        except Exception as e:
            logger.error(f"IPO Service error - market status: {e}")
            return {
                "success": False,
                "message": f"Failed to get market status: {str(e)}",
                "data": [],
                "from_cache": False
            }

    async def get_system_status(self) -> Dict[str, Any]:
        """Business logic for system status"""
        try:
            logger.info("IPO Service: Getting system status")
            
            system_status = {
                "services": {},
                "storage": {},
                "overall_health": "unknown"
            }

            # Check NSE Scraper Service
            try:
                nse_status = self.nse_scraper.get_session_info()
                system_status["services"]["nse_scraper"] = {
                    "status": "active" if nse_status.get("session_active") else "inactive",
                    "details": nse_status
                }
            except Exception as e:
                system_status["services"]["nse_scraper"] = {
                    "status": "error",
                    "error": str(e)
                }

            # Check Storage Service
            try:
                storage_stats = self.storage.get_storage_stats()
                storage_health = self.storage.health_check()
                system_status["storage"] = {
                    "status": storage_health.get("status", "unknown"),
                    "stats": storage_stats,
                    "health": storage_health
                }
            except Exception as e:
                system_status["storage"] = {
                    "status": "error",
                    "error": str(e)
                }

            # Calculate overall health
            service_count = len(system_status["services"])
            healthy_services = sum(1 for s in system_status["services"].values() 
                                 if s.get("status") in ["active", "healthy"])
            
            if healthy_services == service_count and system_status["storage"].get("status") == "healthy":
                system_status["overall_health"] = "healthy"
            elif healthy_services > service_count / 2:
                system_status["overall_health"] = "partial"
            else:
                system_status["overall_health"] = "unhealthy"

            system_status["health_summary"] = f"{healthy_services}/{service_count} services healthy"
            
            return system_status

        except Exception as e:
            logger.error(f"IPO Service error - system status: {e}")
            return {
                "overall_health": "error",
                "error": str(e),
                "services": {},
                "storage": {}
            }

    async def refresh_all_data(self) -> Dict[str, Any]:
        """Business logic for refreshing all data"""
        try:
            logger.info("IPO Service: Refreshing all data")
            
            refresh_results = {}
            
            # Refresh current IPOs
            try:
                current_result = await self.get_current_ipos(force_refresh=True)
                refresh_results["current_ipos"] = "success" if current_result["success"] else "failed"
            except Exception as e:
                refresh_results["current_ipos"] = f"error: {str(e)}"

            # Refresh upcoming IPOs
            try:
                upcoming_result = await self.get_upcoming_ipos(force_refresh=True)
                refresh_results["upcoming_ipos"] = "success" if upcoming_result["success"] else "failed"
            except Exception as e:
                refresh_results["upcoming_ipos"] = f"error: {str(e)}"

            # Refresh market status
            try:
                market_result = await self.get_market_status()
                refresh_results["market_status"] = "success" if market_result["success"] else "failed"
            except Exception as e:
                refresh_results["market_status"] = f"error: {str(e)}"

            # Calculate success rate
            successful = sum(1 for result in refresh_results.values() if result == "success")
            total = len(refresh_results)
            success_rate = (successful / total * 100) if total > 0 else 0

            return {
                "success": successful > 0,
                "message": f"Data refresh completed: {successful}/{total} successful",
                "refresh_summary": refresh_results,
                "success_rate": round(success_rate, 1)
            }

        except Exception as e:
            logger.error(f"IPO Service error - refresh all: {e}")
            return {
                "success": False,
                "message": f"Failed to refresh data: {str(e)}",
                "refresh_summary": {},
                "success_rate": 0
            }

    # Utility methods for business logic
    def _validate_symbol(self, symbol: str) -> bool:
        """Validate IPO symbol format"""
        if not symbol or len(symbol) < 2:
            return False
        return symbol.isalnum() and symbol.isupper()

    def _calculate_subscription_metrics(self, subscription_data: Dict) -> Dict:
        """Calculate additional subscription metrics"""
        try:
            metrics = {
                "total_categories": len(subscription_data.get("categories", {})),
                "oversubscribed_categories": 0,
                "undersubscribed_categories": 0
            }

            for category_data in subscription_data.get("categories", {}).values():
                subscription_numeric = category_data.get("subscription_times_numeric", 0)
                if subscription_numeric >= 1:
                    metrics["oversubscribed_categories"] += 1
                else:
                    metrics["undersubscribed_categories"] += 1

            return metrics
        except Exception as e:
            logger.warning(f"Error calculating subscription metrics: {e}")
            return {}

    def _determine_ipo_recommendation(self, ipo_data: Dict) -> str:
        """Business logic to determine IPO recommendation"""
        try:
            status = ipo_data.get("status", "").lower()
            subscription_ratio = ipo_data.get("subscription_ratio", 0)
            
            if "demo" in status:
                return "Demo data - no recommendation"
            
            if subscription_ratio > 5:
                return "Highly subscribed - caution advised"
            elif subscription_ratio > 2:
                return "Well subscribed - monitor closely"
            elif subscription_ratio > 1:
                return "Adequately subscribed"
            else:
                return "Undersubscribed - may have potential"
            
        except Exception as e:
            logger.warning(f"Error determining recommendation: {e}")
            return "Unable to determine recommendation"

# Create service instance
ipo_service = IPOService()