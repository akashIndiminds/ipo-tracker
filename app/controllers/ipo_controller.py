# app/controllers/ipo_controller.py
from fastapi import HTTPException
from typing import Dict, Any
import logging
from datetime import datetime

from app.services.ipo_service import ipo_service
from app.models.ipo_models import IPOResponse, ErrorResponse

logger = logging.getLogger(__name__)

class IPOController:
    """IPO Controller - Handles HTTP requests and responses only"""

    def __init__(self):
        self.ipo_service = ipo_service

    async def get_current_ipos(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Handle current IPOs request"""
        try:
            result = await self.ipo_service.get_current_ipos(force_refresh)
            
            if result["success"]:
                return IPOResponse(
                    success=True,
                    message=result["message"],
                    data=result["data"],
                    count=result["count"],
                    metadata=result.get("metadata", {}),
                    timestamp=datetime.now().isoformat()
                ).dict()
            else:
                raise HTTPException(status_code=500, detail=result["message"])
                
        except Exception as e:
            logger.error(f"Controller error - current IPOs: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch current IPOs: {str(e)}")

    async def get_upcoming_ipos(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Handle upcoming IPOs request"""
        try:
            result = await self.ipo_service.get_upcoming_ipos(force_refresh)
            
            if result["success"]:
                return IPOResponse(
                    success=True,
                    message=result["message"],
                    data=result["data"],
                    count=result["count"],
                    metadata=result.get("metadata", {}),
                    timestamp=datetime.now().isoformat()
                ).dict()
            else:
                raise HTTPException(status_code=500, detail=result["message"])
                
        except Exception as e:
            logger.error(f"Controller error - upcoming IPOs: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch upcoming IPOs: {str(e)}")

    async def get_subscription_details(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Handle subscription details request"""
        try:
            result = await self.ipo_service.get_subscription_details(symbol, force_refresh)
            
            return {
                "success": result["success"],
                "symbol": symbol.upper(),
                "subscription_data": result.get("subscription_data", {}),
                "message": result.get("message", ""),
                "from_cache": result.get("from_cache", False),
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Controller error - subscription {symbol}: {e}")
            return ErrorResponse(
                success=False,
                message=f"Failed to fetch subscription for {symbol}: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()

    async def get_market_status(self) -> Dict[str, Any]:
        """Handle market status request"""
        try:
            result = await self.ipo_service.get_market_status()
            
            return {
                "success": result["success"],
                "message": result["message"],
                "data": result["data"],
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Controller error - market status: {e}")
            return ErrorResponse(
                success=False,
                message=f"Failed to fetch market status: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()

    async def get_system_status(self) -> Dict[str, Any]:
        """Handle system status request"""
        try:
            result = await self.ipo_service.get_system_status()
            
            return {
                "success": True,
                "message": "System status retrieved",
                "system_status": result,
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Controller error - system status: {e}")
            return ErrorResponse(
                success=False,
                message=f"Failed to get system status: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()

    async def refresh_all_data(self) -> Dict[str, Any]:
        """Handle refresh request"""
        try:
            result = await self.ipo_service.refresh_all_data()
            
            return {
                "success": result["success"],
                "message": result["message"],
                "refresh_summary": result.get("refresh_summary", {}),
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Controller error - refresh: {e}")
            return ErrorResponse(
                success=False,
                message=f"Failed to refresh data: {str(e)}",
                timestamp=datetime.now().isoformat()
            ).dict()

# Create controller instance
ipo_controller = IPOController()