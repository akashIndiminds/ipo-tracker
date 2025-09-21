from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
import logging

from app.services.nse_service import NSEService
from app.services.data_processor import DataProcessor
from app.models.market import MarketIndex, MarketResponse, MarketDashboard, MarketStatus

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/indices", response_model=MarketResponse)
async def get_market_indices():
    """Get major market indices"""
    try:
        logger.info("📊 API Call: Market Indices")
        nse_service = NSEService()
        
        # Fetch raw data
        raw_data = await nse_service.get_market_indices()
        
        # Process and clean data
        cleaned_data = DataProcessor.clean_market_data(raw_data)
        
        # Filter to major indices only
        major_indices = DataProcessor.filter_major_indices(cleaned_data)
        
        logger.info(f"✅ Fetched {len(major_indices)} major market indices")
        
        return MarketResponse(
            success=True,
            message=f"Successfully fetched {len(major_indices)} market indices",
            count=len(major_indices),
            data=[MarketIndex(**item) for item in major_indices],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error fetching market indices: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate market overview: {str(e)}"
        )

@router.get("/sentiment")
async def get_market_sentiment():
    """Get detailed market sentiment analysis"""
    try:
        logger.info("🎭 API Call: Market Sentiment")
        nse_service = NSEService()
        
        # Fetch indices data
        indices_raw = await nse_service.get_market_indices()
        indices_clean = DataProcessor.clean_market_data(indices_raw)
        major_indices = DataProcessor.filter_major_indices(indices_clean)
        
        # Calculate detailed sentiment
        sentiment_data = DataProcessor.calculate_market_sentiment(major_indices)
        
        # Add additional sentiment metrics
        sentiment_analysis = {
            **sentiment_data,
            "detailed_breakdown": _get_sentiment_breakdown(major_indices),
            "sentiment_strength": _calculate_sentiment_strength(sentiment_data),
            "trend_analysis": _analyze_trends(major_indices)
        }
        
        return {
            "success": True,
            "message": "Market sentiment analysis completed",
            "sentiment_analysis": sentiment_analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing market sentiment: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze market sentiment: {str(e)}"
        )

# Helper functions
def _get_performance_summary(indices_data: List[dict]) -> dict:
    """Generate performance summary from indices data"""
    if not indices_data:
        return {"message": "No data available"}
    
    changes = [idx.get('percent_change', 0) for idx in indices_data if idx.get('percent_change') is not None]
    
    if changes:
        avg_change = sum(changes) / len(changes)
        max_change = max(changes)
        min_change = min(changes)
        
        return {
            "average_change": round(avg_change, 2),
            "best_performer": round(max_change, 2),
            "worst_performer": round(min_change, 2),
            "range": round(max_change - min_change, 2),
            "positive_count": len([c for c in changes if c > 0]),
            "negative_count": len([c for c in changes if c < 0])
        }
    
    return {"message": "No performance data available"}

def _determine_market_direction(indices_data: List[dict]) -> str:
    """Determine overall market direction"""
    if not indices_data:
        return "unknown"
    
    changes = [idx.get('percent_change', 0) for idx in indices_data if idx.get('percent_change') is not None]
    
    if changes:
        avg_change = sum(changes) / len(changes)
        if avg_change > 0.5:
            return "bullish"
        elif avg_change < -0.5:
            return "bearish"
        else:
            return "sideways"
    
    return "unknown"

def _calculate_volatility(indices_data: List[dict]) -> str:
    """Calculate market volatility level"""
    if not indices_data:
        return "unknown"
    
    changes = [abs(idx.get('percent_change', 0)) for idx in indices_data if idx.get('percent_change') is not None]
    
    if changes:
        avg_volatility = sum(changes) / len(changes)
        if avg_volatility > 2.0:
            return "high"
        elif avg_volatility > 1.0:
            return "moderate"
        else:
            return "low"
    
    return "unknown"

def _get_key_levels(nifty_data: dict) -> dict:
    """Get key support and resistance levels for NIFTY"""
    if not nifty_data:
        return {}
    
    current_price = nifty_data.get('last', 0)
    high = nifty_data.get('high', 0)
    low = nifty_data.get('low', 0)
    
    return {
        "current_level": current_price,
        "day_high": high,
        "day_low": low,
        "support_level": round(low * 0.995, 2),  # Approximate support
        "resistance_level": round(high * 1.005, 2),  # Approximate resistance
        "range": round(high - low, 2)
    }

def _get_sentiment_breakdown(indices_data: List[dict]) -> dict:
    """Get detailed sentiment breakdown by sector/index"""
    sector_sentiment = {}
    
    for index in indices_data:
        index_name = index.get('index_name', '')
        percent_change = index.get('percent_change', 0)
        
        if percent_change > 1:
            sentiment = "very_positive"
        elif percent_change > 0:
            sentiment = "positive"
        elif percent_change > -1:
            sentiment = "slightly_negative"
        else:
            sentiment = "negative"
        
        sector_sentiment[index_name] = {
            "sentiment": sentiment,
            "change": percent_change
        }
    
    return sector_sentiment

def _calculate_sentiment_strength(sentiment_data: dict) -> str:
    """Calculate the strength of market sentiment"""
    score = sentiment_data.get('sentiment_score', 50)
    
    if score > 70:
        return "very_strong"
    elif score > 60:
        return "strong"
    elif score < 30:
        return "very_weak"
    elif score < 40:
        return "weak"
    else:
        return "moderate"

def _analyze_trends(indices_data: List[dict]) -> dict:
    """Analyze market trends"""
    if not indices_data:
        return {"message": "No data for trend analysis"}
    
    # This is a simplified trend analysis
    # In real implementation, you'd need historical data
    positive_indices = [idx for idx in indices_data if idx.get('percent_change', 0) > 0]
    negative_indices = [idx for idx in indices_data if idx.get('percent_change', 0) < 0]
    
    return {
        "trending_up": len(positive_indices),
        "trending_down": len(negative_indices),
        "sideways": len(indices_data) - len(positive_indices) - len(negative_indices),
        "momentum": "positive" if len(positive_indices) > len(negative_indices) else "negative"
    }

@router.get("/status")
async def get_market_status():
    """Get current market status"""
    try:
        logger.info("🎯 API Call: Market Status")
        nse_service = NSEService()
        
        # Fetch market status
        status_data = await nse_service.get_market_status()
        
        logger.info(f"✅ Fetched market status: {len(status_data)} entries")
        
        return {
            "success": True,
            "message": f"Successfully fetched market status",
            "count": len(status_data),
            "data": status_data,
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
    except Exception as e:
        logger.error(f"Error fetching market status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market status: {str(e)}"
        )

@router.get("/dashboard")
async def get_market_dashboard():
    """Get complete market dashboard data"""
    try:
        logger.info("🎛️ API Call: Market Dashboard")
        nse_service = NSEService()
        
        # Fetch all market data
        indices_raw = await nse_service.get_market_indices()
        status_raw = await nse_service.get_market_status()
        
        # Process data
        indices_clean = DataProcessor.clean_market_data(indices_raw)
        major_indices = DataProcessor.filter_major_indices(indices_clean)
        
        # Calculate market sentiment
        sentiment_data = DataProcessor.calculate_market_sentiment(major_indices)
        
        # Get market highlights
        highlights = DataProcessor.get_market_highlights(major_indices)
        
        # Create dashboard
        dashboard = {
            "success": True,
            "message": "Market dashboard data fetched successfully",
            "dashboard": {
                "market_status": status_raw,
                "major_indices": major_indices,
                "market_sentiment": sentiment_data['sentiment'],
                "sentiment_score": sentiment_data['sentiment_score'],
                "statistics": {
                    "total_indices": sentiment_data['total_count'],
                    "positive_indices": sentiment_data['positive_count'],
                    "negative_indices": sentiment_data['negative_count'],
                    "neutral_indices": sentiment_data['total_count'] - sentiment_data['positive_count'] - sentiment_data['negative_count']
                },
                "highlights": highlights,
                "performance_summary": _get_performance_summary(major_indices)
            },
            "timestamp": datetime.now().isoformat(),
            "source": "NSE API"
        }
        
        logger.info(f"✅ Market dashboard generated with {len(major_indices)} indices")
        return dashboard
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch dashboard data: {str(e)}"
        )

@router.get("/test")
async def test_market_endpoints():
    """Test market endpoints"""
    try:
        logger.info("🧪 Testing Market Endpoints...")
        nse_service = NSEService()
        
        # Test indices endpoint
        indices_data = await nse_service.get_market_indices()
        indices_count = len(indices_data) if indices_data else 0
        
        # Test status endpoint
        status_data = await nse_service.get_market_status()
        status_count = len(status_data) if status_data else 0
        
        results = {
            "indices": {
                "count": indices_count,
                "status": "success" if indices_count > 0 else "failed",
                "sample": indices_data[:2] if indices_data else []
            },
            "market_status": {
                "count": status_count,
                "status": "success" if status_count > 0 else "failed",
                "sample": status_data[:2] if status_data else []
            }
        }
        
        total_success = sum(1 for r in results.values() if r['status'] == 'success')
        total_endpoints = len(results)
        
        return {
            "success": True,
            "message": f"Market endpoints test: {total_success}/{total_endpoints} working",
            "success_rate": (total_success / total_endpoints) * 100,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Market endpoints test failed: {e}")
        return {
            "success": False,
            "message": "Market endpoints test failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/overview")
async def get_market_overview():
    """Get market overview with key metrics"""
    try:
        logger.info("📈 API Call: Market Overview")
        nse_service = NSEService()
        
        # Fetch indices data
        indices_raw = await nse_service.get_market_indices()
        indices_clean = DataProcessor.clean_market_data(indices_raw)
        
        # Find key indices
        nifty_50 = next((idx for idx in indices_clean if idx['index_name'] == 'NIFTY 50'), None)
        bank_nifty = next((idx for idx in indices_clean if idx['index_name'] == 'NIFTY BANK'), None)
        
        # Calculate overview metrics
        overview = {
            "success": True,
            "message": "Market overview generated successfully",
            "overview": {
                "nifty_50": nifty_50,
                "bank_nifty": bank_nifty,
                "total_indices_tracked": len(indices_clean),
                "market_direction": _determine_market_direction(indices_clean),
                "volatility": _calculate_volatility(indices_clean),
                "key_levels": _get_key_levels(nifty_50) if nifty_50 else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return overview
        
    except Exception as e:
        logger.error(f"Error generating market overview: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate market overview: {str(e)}"
        )   