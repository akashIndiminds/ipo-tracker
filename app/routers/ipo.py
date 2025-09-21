from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import logging

# Import services with error handling
try:
    from app.services.nse_service import NSEService
    from app.services.data_processor import DataProcessor
    from app.services.gmp_service import GMPService
    from app.models.ipo import IPOData, IPOResponse
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Import error in IPO router: {e}")
    # Create fallback classes if imports fail
    class NSEService:
        async def get_current_ipos(self): return []
        async def get_upcoming_ipos(self): return []
        async def get_past_ipos(self, days): return []
        async def test_all_endpoints(self): return {"status": "error"}
    
    class DataProcessor:
        @staticmethod
        def clean_ipo_data(data): return data
        @staticmethod
        def format_ipo_summary(*args): return {}
        @staticmethod
        def _merge_ipo_gmp_data(ipo_data, gmp_data): return ipo_data
        @staticmethod
        def _assess_market_activity(current, upcoming): return "Unknown"
        @staticmethod
        def _is_number(text): return False
        @staticmethod
        def _format_currency(amount): return f"₹{amount:,.0f}"
    
    class GMPService:
        async def get_gmp_data(self): return []
        def get_demo_gmp_data(self): return []
        def calculate_gmp_metrics(self, data): return {}

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
            "message": f"NSE API test completed: {test_results.get('working_endpoints', 0)}/{test_results.get('total_endpoints', 0)} endpoints working",
            "overall_status": test_results.get('overall_status', 'unknown'),
            "success_rate": test_results.get('success_rate', 0),
            "test_results": test_results.get('test_results', {}),
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

@router.get("/current", response_model=dict)
async def get_current_ipos(include_gmp: bool = Query(True, description="Include Gray Market Premium data")):
    """Get all current active IPOs with optional GMP data"""
    try:
        logger.info("📈 API Call: Current IPOs")
        nse_service = NSEService()
        
        # Fetch raw IPO data
        raw_data = await nse_service.get_current_ipos()
        
        # Process and clean data
        cleaned_data = DataProcessor.clean_ipo_data(raw_data)
        
        # Fetch GMP data if requested
        gmp_data = []
        if include_gmp:
            try:
                logger.info("💰 Fetching GMP data for current IPOs...")
                gmp_service = GMPService()
                gmp_data = await gmp_service.get_gmp_data()
                
                if not gmp_data:
                    gmp_data = gmp_service.get_demo_gmp_data()
                
                # Merge GMP data with IPO data
                cleaned_data = DataProcessor._merge_ipo_gmp_data(cleaned_data, gmp_data)
                
            except Exception as gmp_error:
                logger.warning(f"GMP data fetch failed: {gmp_error}")
                # Continue without GMP data
        
        logger.info(f"✅ Fetched {len(cleaned_data)} current IPOs")
        
        return {
            "success": True,
            "message": f"Successfully fetched {len(cleaned_data)} current IPOs",
            "count": len(cleaned_data),
            "data": cleaned_data,
            "gmp_included": include_gmp and len(gmp_data) > 0,
            "gmp_count": len(gmp_data) if include_gmp else 0,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API + GMP Sources" if include_gmp else "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching current IPOs: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch current IPOs: {str(e)}"
        )

@router.get("/upcoming", response_model=dict)
async def get_upcoming_ipos(include_gmp: bool = Query(True, description="Include Gray Market Premium data")):
    """Get all upcoming IPOs with optional GMP data"""
    try:
        logger.info("🔮 API Call: Upcoming IPOs")
        nse_service = NSEService()
        
        # Fetch raw data
        raw_data = await nse_service.get_upcoming_ipos()
        
        # Process and clean data
        cleaned_data = DataProcessor.clean_ipo_data(raw_data)
        
        # Fetch GMP data if requested
        gmp_data = []
        if include_gmp:
            try:
                logger.info("💰 Fetching GMP data for upcoming IPOs...")
                gmp_service = GMPService()
                gmp_data = await gmp_service.get_gmp_data()
                
                if not gmp_data:
                    gmp_data = gmp_service.get_demo_gmp_data()
                
                # Merge GMP data with IPO data
                cleaned_data = DataProcessor._merge_ipo_gmp_data(cleaned_data, gmp_data)
                
            except Exception as gmp_error:
                logger.warning(f"GMP data fetch failed: {gmp_error}")
        
        logger.info(f"✅ Fetched {len(cleaned_data)} upcoming IPOs")
        
        return {
            "success": True,
            "message": f"Successfully fetched {len(cleaned_data)} upcoming IPOs",
            "count": len(cleaned_data),
            "data": cleaned_data,
            "gmp_included": include_gmp and len(gmp_data) > 0,
            "gmp_count": len(gmp_data) if include_gmp else 0,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API + GMP Sources" if include_gmp else "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching upcoming IPOs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch upcoming IPOs: {str(e)}"
        )

@router.get("/past", response_model=dict)
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
        
        return {
            "success": True,
            "message": f"Successfully fetched {len(cleaned_data)} past IPOs from last {days_back} days",
            "count": len(cleaned_data),
            "data": cleaned_data,
            "days_back": days_back,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching past IPOs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch past IPOs: {str(e)}"
        )

@router.get("/gmp", response_model=dict)
async def get_gmp_data():
    """Get Gray Market Premium data for IPOs"""
    try:
        logger.info("💰 API Call: GMP Data")
        gmp_service = GMPService()
        
        # Fetch GMP data
        gmp_data = await gmp_service.get_gmp_data()
        
        if not gmp_data:
            # Use demo data if no real data available
            gmp_data = gmp_service.get_demo_gmp_data()
            is_demo = True
        else:
            is_demo = False
        
        # Calculate GMP metrics
        gmp_metrics = gmp_service.calculate_gmp_metrics(gmp_data)
        
        logger.info(f"✅ Fetched {len(gmp_data)} GMP records")
        
        return {
            "success": True,
            "message": f"Successfully fetched {len(gmp_data)} GMP records",
            "count": len(gmp_data),
            "data": gmp_data,
            "metrics": gmp_metrics,
            "is_demo_data": is_demo,
            "timestamp": datetime.now().isoformat(),
            "source": "Demo Data" if is_demo else "Multiple GMP Sources"
        }
        
    except Exception as e:
        logger.error(f"Error fetching GMP data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch GMP data: {str(e)}"
        )

@router.get("/gmp/recommendation/{company_name}")
async def get_gmp_recommendation(company_name: str):
    """Get GMP-based recommendation for a specific IPO"""
    try:
        logger.info(f"🎯 API Call: GMP Recommendation for {company_name}")
        gmp_service = GMPService()
        
        # Fetch GMP data
        gmp_data = await gmp_service.get_gmp_data()
        
        if not gmp_data:
            gmp_data = gmp_service.get_demo_gmp_data()
        
        # Get recommendation
        recommendation = gmp_service.get_gmp_recommendations(company_name, gmp_data)
        
        return {
            "success": True,
            "message": f"GMP recommendation generated for {company_name}",
            "company_name": company_name,
            "recommendation": recommendation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting GMP recommendation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get GMP recommendation: {str(e)}"
        )

@router.get("/summary", response_model=dict)
async def get_ipo_summary(include_gmp: bool = Query(True, description="Include GMP analysis")):
    """Get complete IPO summary with all data"""
    try:
        logger.info("📋 API Call: Complete IPO Summary")
        nse_service = NSEService()
        
        # Fetch all IPO data
        current_raw = await nse_service.get_current_ipos()
        upcoming_raw = await nse_service.get_upcoming_ipos()
        past_raw = await nse_service.get_past_ipos(30)
        
        # Process data
        current_clean = DataProcessor.clean_ipo_data(current_raw)
        upcoming_clean = DataProcessor.clean_ipo_data(upcoming_raw)
        past_clean = DataProcessor.clean_ipo_data(past_raw)
        
        # Fetch GMP data if requested
        gmp_data = []
        if include_gmp:
            try:
                gmp_service = GMPService()
                gmp_data = await gmp_service.get_gmp_data()
                if not gmp_data:
                    gmp_data = gmp_service.get_demo_gmp_data()
            except Exception as gmp_error:
                logger.warning(f"GMP data fetch failed: {gmp_error}")
        
        # Create summary using data processor
        summary_data = DataProcessor.format_ipo_summary(
            current_clean, upcoming_clean, past_clean, gmp_data if include_gmp else None
        )
        
        response = {
            "success": True,
            "message": "IPO summary generated successfully",
            "summary": summary_data,
            "gmp_included": include_gmp and len(gmp_data) > 0,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API + GMP Sources" if include_gmp else "NSE API"
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
    category: Optional[str] = Query("all", description="IPO category: current, upcoming, past, or all"),
    include_gmp: bool = Query(False, description="Include GMP data in search results")
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
        
        # Include GMP data if requested
        if include_gmp:
            try:
                gmp_service = GMPService()
                gmp_data = await gmp_service.get_gmp_data()
                if gmp_data:
                    all_ipos = DataProcessor._merge_ipo_gmp_data(all_ipos, gmp_data)
            except Exception as gmp_error:
                logger.warning(f"GMP data merge failed during search: {gmp_error}")
        
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
            "gmp_included": include_gmp,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching IPOs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search IPOs: {str(e)}"
        )

@router.get("/analytics")
async def get_ipo_analytics(include_gmp: bool = Query(True, description="Include GMP analytics")):
    """Get comprehensive IPO market analytics and insights"""
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
        
        # Fetch GMP data if requested
        gmp_metrics = {}
        if include_gmp:
            try:
                gmp_service = GMPService()
                gmp_data = await gmp_service.get_gmp_data()
                if not gmp_data:
                    gmp_data = gmp_service.get_demo_gmp_data()
                gmp_metrics = gmp_service.calculate_gmp_metrics(gmp_data)
            except Exception as gmp_error:
                logger.warning(f"GMP analytics failed: {gmp_error}")
        
        # Calculate analytics
        analytics = {
            "market_activity": {
                "current_count": len(current_clean),
                "upcoming_count": len(upcoming_clean),
                "past_90_days": len(past_clean),
                "activity_level": DataProcessor._assess_market_activity(current_clean, upcoming_clean)
            },
            "subscription_analysis": _analyze_subscriptions(current_clean),
            "sector_analysis": _analyze_sectors(current_clean + upcoming_clean),
            "size_analysis": _analyze_issue_sizes(current_clean + upcoming_clean),
            "timing_analysis": _analyze_timing(upcoming_clean),
            "risk_analysis": _analyze_risk_levels(current_clean + upcoming_clean)
        }
        
        # Add GMP analytics if available
        if include_gmp and gmp_metrics:
            analytics["gmp_analysis"] = gmp_metrics
        
        return {
            "success": True,
            "message": "IPO analytics generated successfully",
            "analytics": analytics,
            "gmp_included": include_gmp and bool(gmp_metrics),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating IPO analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate IPO analytics: {str(e)}"
        )

# Helper functions
def _get_recommendations(test_results: dict) -> List[str]:
    """Generate recommendations based on test results"""
    recommendations = []
    
    success_rate = test_results.get('success_rate', 0)
    avg_response_time = test_results.get('average_response_time', 0)
    test_data = test_results.get('test_results', {})
    
    if success_rate < 50:
        recommendations.append("🚨 Most endpoints are failing - check network connectivity")
    elif success_rate < 80:
        recommendations.append("⚠️ Some endpoints are unstable - monitor closely")
    
    if avg_response_time > 10:
        recommendations.append("🐌 Response times are slow - consider proxy or different approach")
    
    failing_endpoints = [
        name for name, data in test_data.items()
        if data.get('status') == 'failed'
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
    subscription_levels = {
        "heavily_oversubscribed": 0,  # >10x
        "highly_oversubscribed": 0,   # 5-10x
        "well_subscribed": 0,         # 2-5x
        "fully_subscribed": 0,        # 1-2x
        "undersubscribed": 0          # <1x
    }
    
    for ipo in ipos_data:
        sub_times = ipo.get('subscription_times', '')
        if sub_times and DataProcessor._is_number(sub_times):
            sub_rate = float(sub_times)
            subscriptions.append(sub_rate)
            
            # Categorize subscription level
            if sub_rate >= 10:
                subscription_levels["heavily_oversubscribed"] += 1
            elif sub_rate >= 5:
                subscription_levels["highly_oversubscribed"] += 1
            elif sub_rate >= 2:
                subscription_levels["well_subscribed"] += 1
            elif sub_rate >= 1:
                subscription_levels["fully_subscribed"] += 1
            else:
                subscription_levels["undersubscribed"] += 1
    
    if subscriptions:
        avg_subscription = sum(subscriptions) / len(subscriptions)
        return {
            "average_subscription": round(avg_subscription, 2),
            "total_analyzed": len(subscriptions),
            "oversubscribed_count": len([s for s in subscriptions if s > 1.0]),
            "highly_subscribed": len([s for s in subscriptions if s > 2.0]),
            "max_subscription": max(subscriptions),
            "min_subscription": min(subscriptions),
            "subscription_distribution": subscription_levels,
            "market_sentiment": "Strong" if avg_subscription > 2 else "Moderate" if avg_subscription > 1 else "Weak"
        }
    
    return {"message": "No subscription data available"}

def _analyze_sectors(ipos_data: List[dict]) -> dict:
    """Analyze sector distribution of IPOs"""
    if not ipos_data:
        return {"message": "No IPO data for sector analysis"}
    
    # Sector keywords mapping
    sector_keywords = {
        "Technology": ["tech", "software", "it", "digital", "cyber", "data", "cloud"],
        "Healthcare": ["pharma", "medical", "health", "bio", "drug", "hospital"],
        "Financial": ["bank", "finance", "insurance", "nbfc", "mutual"],
        "Energy": ["power", "energy", "solar", "wind", "oil", "gas"],
        "Manufacturing": ["manufacturing", "industrial", "auto", "steel", "textile"],
        "Consumer": ["fmcg", "retail", "food", "beverage", "consumer"],
        "Real Estate": ["real estate", "construction", "housing", "property"],
        "Infrastructure": ["infra", "road", "railway", "port", "logistics"]
    }
    
    sector_distribution = {}
    unclassified = 0
    
    for ipo in ipos_data:
        company_name = ipo.get('company_name', '').lower()
        classified = False
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in company_name for keyword in keywords):
                sector_distribution[sector] = sector_distribution.get(sector, 0) + 1
                classified = True
                break
        
        if not classified:
            unclassified += 1
    
    total_companies = len(ipos_data)
    
    # Calculate percentages
    sector_percentages = {
        sector: round((count / total_companies) * 100, 1)
        for sector, count in sector_distribution.items()
    }
    
    return {
        "total_companies": total_companies,
        "sector_distribution": sector_distribution,
        "sector_percentages": sector_percentages,
        "unclassified": unclassified,
        "dominant_sector": max(sector_distribution.items(), key=lambda x: x[1])[0] if sector_distribution else None
    }

def _analyze_issue_sizes(ipos_data: List[dict]) -> dict:
    """Analyze issue size distribution"""
    if not ipos_data:
        return {"message": "No IPO data for size analysis"}
    
    sizes = []
    size_categories = {
        "Large Cap": 0,    # >500Cr
        "Mid Cap": 0,      # 100-500Cr  
        "Small Cap": 0,    # 25-100Cr
        "Micro Cap": 0     # <25Cr
    }
    
    for ipo in ipos_data:
        size_str = ipo.get('issue_size', '')
        if size_str and DataProcessor._is_number(size_str):
            size_value = float(size_str)
            sizes.append(size_value)
            
            # Categorize by size
            category = ipo.get('issue_size_category', '')
            if category in size_categories:
                size_categories[category] += 1
    
    if sizes:
        total_value = sum(sizes)
        avg_size = total_value / len(sizes)
        
        return {
            "total_market_value": total_value,
            "total_market_value_formatted": DataProcessor._format_currency(total_value),
            "average_size": avg_size,
            "average_size_formatted": DataProcessor._format_currency(avg_size),
            "largest_ipo": max(sizes),
            "largest_ipo_formatted": DataProcessor._format_currency(max(sizes)),
            "smallest_ipo": min(sizes),
            "smallest_ipo_formatted": DataProcessor._format_currency(min(sizes)),
            "count": len(sizes),
            "size_distribution": size_categories,
            "market_composition": "Large Cap Heavy" if size_categories["Large Cap"] > len(sizes) * 0.4 else "Diversified"
        }
    
    return {"message": "No issue size data available"}

def _analyze_timing(upcoming_ipos: List[dict]) -> dict:
    """Analyze timing patterns of upcoming IPOs"""
    if not upcoming_ipos:
        return {"message": "No upcoming IPOs for timing analysis"}
    
    timing_distribution = {
        "This Week": 0,
        "Next Week": 0,
        "This Month": 0,
        "Next Month": 0,
        "Later": 0
    }
    
    urgency_levels = {
        "High": 0,
        "Medium": 0, 
        "Low": 0
    }
    
    for ipo in upcoming_ipos:
        days_to_start = ipo.get('days_to_start', 0)
        urgency = ipo.get('urgency', 'Low')
        
        # Timing distribution
        if days_to_start <= 7:
            timing_distribution["This Week"] += 1
        elif days_to_start <= 14:
            timing_distribution["Next Week"] += 1
        elif days_to_start <= 30:
            timing_distribution["This Month"] += 1
        elif days_to_start <= 60:
            timing_distribution["Next Month"] += 1
        else:
            timing_distribution["Later"] += 1
        
        # Urgency levels
        if urgency in urgency_levels:
            urgency_levels[urgency] += 1
    
    return {
        "upcoming_count": len(upcoming_ipos),
        "timing_distribution": timing_distribution,
        "urgency_levels": urgency_levels,
        "immediate_opportunities": timing_distribution["This Week"] + timing_distribution["Next Week"],
        "pipeline_strength": "Strong" if len(upcoming_ipos) > 5 else "Moderate" if len(upcoming_ipos) > 2 else "Weak"
    }

def _analyze_risk_levels(ipos_data: List[dict]) -> dict:
    """Analyze risk level distribution"""
    if not ipos_data:
        return {"message": "No IPO data for risk analysis"}
    
    risk_distribution = {
        "Low": 0,
        "Medium": 0,
        "High": 0
    }
    
    for ipo in ipos_data:
        risk_level = ipo.get('risk_level', 'Medium')
        if risk_level in risk_distribution:
            risk_distribution[risk_level] += 1
    
    total = len(ipos_data)
    risk_percentages = {
        risk: round((count / total) * 100, 1)
        for risk, count in risk_distribution.items()
    }
    
    # Overall market risk assessment
    if risk_percentages.get("Low", 0) > 50:
        market_risk = "Low Risk Market"
    elif risk_percentages.get("High", 0) > 50:
        market_risk = "High Risk Market"
    else:
        market_risk = "Balanced Risk Market"
    
    return {
        "total_analyzed": total,
        "risk_distribution": risk_distribution,
        "risk_percentages": risk_percentages,
        "market_risk_assessment": market_risk,
        "low_risk_opportunities": risk_distribution.get("Low", 0)
    }