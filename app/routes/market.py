# app/routers/market.py
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
import logging

# Import controller
from app.controllers.market_controller import market_controller

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/market", tags=["Market"])

@router.get("/indices")
async def get_market_indices():
    """Get major market indices"""
    try:
        result = await market_controller.get_market_indices()
        return result
    except Exception as e:
        logger.error(f"❌ Market indices endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market indices: {str(e)}"
        )

@router.get("/sentiment")
async def get_market_sentiment():
    """Get detailed market sentiment analysis"""
    try:
        result = await market_controller.get_market_sentiment()
        return result
    except Exception as e:
        logger.error(f"❌ Market sentiment endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze market sentiment: {str(e)}"
        )

@router.get("/status")
async def get_market_status():
    """Get current market status"""
    try:
        result = await market_controller.get_market_status()
        return result
    except Exception as e:
        logger.error(f"❌ Market status endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market status: {str(e)}"
        )

@router.get("/dashboard")
async def get_market_dashboard():
    """Get complete market dashboard data"""
    try:
        result = await market_controller.get_market_dashboard()
        return result
    except Exception as e:
        logger.error(f"❌ Market dashboard endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )

@router.get("/overview")
async def get_market_overview():
    """Get market overview with key metrics"""
    try:
        result = await market_controller.get_market_overview()
        return result
    except Exception as e:
        logger.error(f"❌ Market overview endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate market overview: {str(e)}"
        )

@router.get("/test")
async def test_market_endpoints():
    """Test market endpoints"""
    try:
        result = await market_controller.test_market_endpoints()
        return result
    except Exception as e:
        logger.error(f"❌ Market test endpoint failed: {e}")
        return {
            "success": False,
            "message": "Market endpoints test failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }