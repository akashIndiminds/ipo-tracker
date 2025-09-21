from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

from app.services.nse_service import NSEService
from app.services.data_processor import DataProcessor
from app.models.ipo import IPOData, IPOResponse, IPOSummary

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/test", response_model=dict)
async def test_nse_connection():
    """Test NSE API connection and get comprehensive status"""
    try:
        logger.info("🧪 Testing NSE API Connection...")
        nse_service = NSEService()
        
        # Run comprehensive test
        test_results = await nse_service.test_all_endpoints()
        
        return {
            "success": True,
            "message": f"NSE API test completed: {test_results['working_endpoints']}/{test_results['total_endpoints']} endpoints working",
            "overall_status": test_results['overall_status'],
            "success_rate": test_results['success_rate'],
            "test_results": test_results['test_results'],
            "timestamp": datetime.now().isoformat(),
            "recommendations": _get_recommendations(test_results)
        }
        
    except Exception as e:
        logger.error(f"NSE API test failed: {e}")
        return {
            "success": False,
            "message": "NSE API test failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/current", response_model=IPOResponse)
async def get_current_ipos():
    """Get all current active IPOs"""
    try:
        logger.info("📈 API Call: Current IPOs")
        nse_service = NSEService()
        
        # Fetch raw data
        raw_data = await nse_service.get_current_ipos()
        
        # Process and clean data
        cleaned_data = DataProcessor.clean_ipo_data(raw_data)
        
        logger.info(f"✅ Fetched {len(cleaned_data)} current IPOs")
        
        return IPOResponse(
            success=True,
            message=f"Successfully fetched {len(cleaned_data)} current IPOs",
            count=len(cleaned_data),
            data=[IPOData(**item) for item in cleaned_data],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error fetching current IPOs: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch current IPOs: {str(e)}"
        )

@router.get("/upcoming", response_model=IPOResponse)
async def get_upcoming_ipos():
    """Get all upcoming IPOs"""
    try:
        logger.info("🔮 API Call: Upcoming IPOs")
        nse_service = NSEService()
        
        # Fetch raw data
        raw_data = await nse_service.get_upcoming_ipos()
        
        # Process and clean data
        cleaned_data = DataProcessor.clean_ipo_data(raw_data)
        
        logger.info(f"✅ Fetched {len(cleaned_data)} upcoming IPOs")
        
        return IPOResponse(
            success=True,
            message=f"Successfully fetched {len(cleaned_data)} upcoming IPOs",
            count=len(cleaned_data),
            data=[IPOData(**item) for item in cleaned_data],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error fetching upcoming IPOs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch upcoming IPOs: {str(e)}"
        )

@router.get("/past", response_model=IPOResponse)
async def get_past_ipos(
    days_back: int = Query(30, ge=1, le=90, description="Number of days to look back (1-90)")
):
    """Get past IPOs performance"""
    try:
        logger.info(f"📊 API Call: Past IPOs (Last {days_back} days)")
        nse_service = NSEService()
        
        # Fetch raw data
        raw_data = await nse_service.get_past_ipos(days_back)
        
        # Process and clean data
        cleaned_data = DataProcessor.clean_ipo_data(raw_data)
        
        logger.info(f"✅ Fetched {len(cleaned_data)} past IPOs")
        
        return IPOResponse(
            success=True,
            message=f"Successfully fetched {len(cleaned_data)} past IPOs from last {days_back} days",
            count=len(cleaned_data),
            data=[IPOData(**item) for item in cleaned_data],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error fetching past IPOs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch past IPOs: {str(e)}"
        )

@router.get("/summary", response_model=dict)
async def get_ipo_summary():
    """Get complete IPO summary with all data"""
    try:
        logger.info("📋 API Call: Complete IPO Summary")
        nse_service = NSEService()
        
        # Fetch all data
        current_raw = await nse_service.get_current_ipos()
        upcoming_raw = await nse_service.get_upcoming_ipos()
        past_raw = await nse_service.get_past_ipos(30)
        
        # Process data
        current_clean = DataProcessor.clean_ipo_data(current_raw)
        upcoming_clean = DataProcessor.clean_ipo_data(upcoming_raw)
        past_clean = DataProcessor.clean_ipo_data(past_raw)
        
        # Create summary using data processor
        summary_data = DataProcessor.format_ipo_summary(current_clean, upcoming_clean, past_clean)
        
        response = {
            "success": True,
            "message": "IPO summary generated successfully",
            "summary": summary_data,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
        logger.info("✅ IPO summary generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error generating IPO summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate IPO summary: {str(e)}"
        )

@router.get("/search")
async def search_ipos(
    query: str = Query(..., min_length=2, description="Search term for company name or symbol"),
    category: Optional[str] = Query("all", description="IPO category: current, upcoming, past, or all")
):
    """Search IPOs by company name or symbol"""
    try:
        logger.info(f"🔍 API Call: Search IPOs - Query: '{query}', Category: '{category}'")
        nse_service = NSEService()
        
        all_ipos = []
        
        # Fetch data based on category
        if category in ["current", "all"]:
            current_data = await nse_service.get_current_ipos()
            all_ipos.extend(DataProcessor.clean_ipo_data(current_data))
        
        if category in ["upcoming", "all"]:
            upcoming_data = await nse_service.get_upcoming_ipos()
            all_ipos.extend(DataProcessor.clean_ipo_data(upcoming_data))
        
        if category in ["past", "all"]:
            past_data = await nse_service.get_past_ipos(60)  # Last 60 days for search
            all_ipos.extend(DataProcessor.clean_ipo_data(past_data))
        
        # Search in the data
        query_lower = query.lower()
        search_results = [
            ipo for ipo in all_ipos
            if query_lower in ipo.get('company_name', '').lower() or
               query_lower in ipo.get('symbol', '').lower()
        ]
        
        logger.info(f"✅ Found {len(search_results)} matching IPOs")
        
        return {
            "success": True,
            "message": f"Found {len(search_results)} IPOs matching '{query}'",
            "query": query,
            "category": category,
            "count": len(search_results),
            "data": search_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching IPOs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search IPOs: {str(e)}"
        )

@router.get("/analytics")
async def get_ipo_analytics():
    """Get IPO market analytics and insights"""
    try:
        logger.info("📊 API Call: IPO Analytics")
        nse_service = NSEService()
        
        # Fetch data for analytics
        current_data = await nse_service.get_current_ipos()
        upcoming_data = await nse_service.get_upcoming_ipos()
        past_data = await nse_service.get_past_ipos(90)  # Last 3 months
        
        # Process data
        current_clean = DataProcessor.clean_ipo_data(current_data)
        upcoming_clean = DataProcessor.clean_ipo_data(upcoming_data)
        past_clean = DataProcessor.clean_ipo_data(past_data)
        
        # Calculate analytics
        analytics = {
            "market_activity": {
                "current_count": len(current_clean),
                "upcoming_count": len(upcoming_clean),
                "past_90_days": len(past_clean),
                "activity_level": "high" if len(current_clean) + len(upcoming_clean) > 5 else "moderate"
            },
            "subscription_analysis": _analyze_subscriptions(current_clean),
            "sector_analysis": _analyze_sectors(current_clean + upcoming_clean),
            "size_analysis": _analyze_issue_sizes(current_clean + upcoming_clean),
            "timing_analysis": _analyze_timing(upcoming_clean)
        }
        
        return {
            "success": True,
            "message": "IPO analytics generated successfully",
            "analytics": analytics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating IPO analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate IPO analytics: {str(e)}"
        )

def _get_recommendations(test_results: dict) -> List[str]:
    """Generate recommendations based on test results"""
    recommendations = []
    
    if test_results['success_rate'] < 50:
        recommendations.append("🚨 Most endpoints are failing - check network connectivity")
    elif test_results['success_rate'] < 80:
        recommendations.append("⚠️ Some endpoints are unstable - monitor closely")
    
    if test_results['average_response_time'] > 10:
        recommendations.append("🐌 Response times are slow - consider proxy or different approach")
    
    failing_endpoints = [
        name for name, data in test_results['test_results'].items()
        if data['status'] == 'failed'
    ]
    
    if failing_endpoints:
        recommendations.append(f"🔧 Fix failing endpoints: {', '.join(failing_endpoints)}")
    
    if not recommendations:
        recommendations.append("✅ All systems are working well!")
    
    return recommendations

def _analyze_subscriptions(ipos_data: List[dict]) -> dict:
    """Analyze subscription patterns"""
    if not ipos_data:
        return {"message": "No current IPOs for subscription analysis"}
    
    subscriptions = []
    for ipo in ipos_data:
        sub_times = ipo.get('subscription_times', '')
        if sub_times and sub_times.replace('.', '').isdigit():
            subscriptions.append(float(sub_times))
    
    if subscriptions:
        avg_subscription = sum(subscriptions) / len(subscriptions)
        return {
            "average_subscription": round(avg_subscription, 2),
            "oversubscribed_count": len([s for s in subscriptions if s > 1.0]),
            "highly_subscribed": len([s for s in subscriptions if s > 2.0]),
            "max_subscription": max(subscriptions)
        }
    
    return {"message": "No subscription data available"}

def _analyze_sectors(ipos_data: List[dict]) -> dict:
    """Analyze sector distribution"""
    # This is a simplified sector analysis
    # In real implementation, you'd need sector mapping logic
    return {
        "message": "Sector analysis requires additional sector classification data",
        "total_companies": len(ipos_data)
    }

def _analyze_issue_sizes(ipos_data: List[dict]) -> dict:
    """Analyze issue size distribution"""
    sizes = []
    for ipo in ipos_data:
        size_str = ipo.get('issue_size', '')
        if size_str.isdigit():
            sizes.append(int(size_str))
    
    if sizes:
        total_value = sum(sizes)
        return {
            "total_market_value": total_value,
            "average_size": total_value // len(sizes),
            "largest_ipo": max(sizes),
            "smallest_ipo": min(sizes),
            "count": len(sizes)
        }
    
    return {"message": "No issue size data available"}

def _analyze_timing(upcoming_ipos: List[dict]) -> dict:
    """Analyze timing patterns of upcoming IPOs"""
    return {
        "upcoming_count": len(upcoming_ipos),
        "message": "Timing analysis shows upcoming IPO distribution"
    }