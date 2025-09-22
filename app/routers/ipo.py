# app/routers/ipo.py
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

# Import controller
from app.controllers.ipo_controller import ipo_controller

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/ipo", tags=["IPO"])

@router.get("/test")
async def test_nse_connection():
    """Test NSE API connection and get comprehensive status"""
    try:
        result = await ipo_controller.test_nse_connection()
        return result
    except Exception as e:
        logger.error(f"Test endpoint failed: {e}")
        return {
            "success": False,
            "message": "NSE API test failed",
            "error": str(e)
        }

@router.post("/refresh-session")
async def refresh_nse_session():
    """Manually refresh NSE session"""
    try:
        result = await ipo_controller.refresh_nse_session()
        return result
    except Exception as e:
        logger.error(f"Session refresh failed: {e}")
        return {
            "success": False,
            "message": "Session refresh failed",
            "error": str(e)
        }

@router.get("/current")
async def get_current_ipos(
    include_gmp: bool = Query(True, description="Include Gray Market Premium data")
):
    """Get all current active IPOs with optional GMP data"""
    try:
        result = await ipo_controller.get_current_ipos(include_gmp=include_gmp)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Current IPOs endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch current IPOs: {str(e)}"
        )

@router.get("/upcoming")
async def get_upcoming_ipos(
    include_gmp: bool = Query(True, description="Include Gray Market Premium data")
):
    """Get all upcoming IPOs with optional GMP data"""
    try:
        result = await ipo_controller.get_upcoming_ipos(include_gmp=include_gmp)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upcoming IPOs endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch upcoming IPOs: {str(e)}"
        )

@router.get("/past")
async def get_past_ipos(
    days_back: int = Query(30, ge=1, le=90, description="Number of days to look back (1-90)")
):
    """Get past IPOs performance"""
    try:
        result = await ipo_controller.get_past_ipos(days_back=days_back)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Past IPOs endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch past IPOs: {str(e)}"
        )

@router.get("/gmp")
async def get_gmp_data():
    """Get Gray Market Premium data for IPOs"""
    try:
        # For now, return demo GMP data since external sources are failing
        from app.services.gmp_service import GMPService
        gmp_service = GMPService()
        gmp_data = gmp_service.get_demo_gmp_data()
        gmp_metrics = gmp_service.calculate_gmp_metrics(gmp_data)
        
        return {
            'success': True,
            'message': f'Successfully fetched {len(gmp_data)} GMP records (demo data)',
            'count': len(gmp_data),
            'data': gmp_data,
            'metrics': gmp_metrics,
            'is_demo_data': True,
            'timestamp': datetime.now().isoformat(),
            'source': 'Demo Data - External GMP sources unavailable'
        }
    except Exception as e:
        logger.error(f"GMP data endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch GMP data: {str(e)}"
        )

@router.get("/gmp/recommendation/{company_name}")
async def get_gmp_recommendation(company_name: str):
    """Get GMP-based recommendation for a specific IPO"""
    try:
        from app.services.gmp_service import GMPService
        from datetime import datetime
        
        gmp_service = GMPService()
        gmp_data = gmp_service.get_demo_gmp_data()
        
        # Get recommendation
        recommendation = gmp_service.get_gmp_recommendations(company_name, gmp_data)
        
        return {
            'success': True,
            'message': f'GMP recommendation generated for {company_name}',
            'company_name': company_name,
            'recommendation': recommendation,
            'is_demo_data': True,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"GMP recommendation endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get GMP recommendation: {str(e)}"
        )

@router.get("/summary")
async def get_ipo_summary(
    include_gmp: bool = Query(True, description="Include GMP analysis")
):
    """Get complete IPO summary with all data"""
    try:
        result = await ipo_controller.get_ipo_summary(include_gmp=include_gmp)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IPO summary endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate IPO summary: {str(e)}"
        )

@router.get("/search")
async def search_ipos(
    query: str = Query(..., min_length=2, description="Search term for company name or symbol"),
    category: Optional[str] = Query("all", description="IPO category: current, upcoming, past, or all"),
    include_gmp: bool = Query(False, description="Include GMP data in search results")
):
    """Search IPOs by company name or symbol"""
    try:
        result = await ipo_controller.search_ipos(
            query=query,
            category=category,
            include_gmp=include_gmp
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search IPOs: {str(e)}"
        )

@router.get("/analytics")
async def get_ipo_analytics(
    include_gmp: bool = Query(True, description="Include GMP analytics")
):
    """Get comprehensive IPO market analytics and insights"""
    try:
        from datetime import datetime
        
        # Fetch data for analytics
        current_result = await ipo_controller.get_current_ipos(include_gmp=False)
        upcoming_result = await ipo_controller.get_upcoming_ipos(include_gmp=False)
        
        current_data = current_result.get('data', [])
        upcoming_data = upcoming_result.get('data', [])
        
        # Calculate basic analytics
        analytics = {
            "market_activity": {
                "current_count": len(current_data),
                "upcoming_count": len(upcoming_data),
                "total_active": len(current_data) + len(upcoming_data),
                "activity_level": "High" if len(current_data) + len(upcoming_data) > 10 else "Moderate"
            },
            "data_quality": {
                "real_current_data": current_result.get('is_real_data', False),
                "real_upcoming_data": upcoming_result.get('is_real_data', False)
            },
            "session_health": current_result.get('session_info', {})
        }
        
        return {
            "success": True,
            "message": "IPO analytics generated successfully",
            "analytics": analytics,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API + Demo GMP"
        }
        
    except Exception as e:
        logger.error(f"Analytics endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics: {str(e)}"
        )