# app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from .routes.ipo_routes import router as ipo_router
from .routes.local_routes import router as local_router
from .routes.gmp_routes import router as gmp_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NSE IPO Tracker API v3.0 - With GMP Integration",
    description="Real-time IPO tracking with NSE integration, GMP analysis, and mathematical predictions",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ipo_router)
app.include_router(local_router)
app.include_router(gmp_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NSE IPO Tracker API with GMP Integration",
        "version": "3.0.0",
        "message": "API is running successfully",
        "features": [
            "NSE Live Data",
            "Local Data Storage", 
            "File-based Caching",
            "Daily Data Archives",
            "GMP Data Scraping",
            "Mathematical Predictions",
            "Risk Assessment",
            "Investment Recommendations"
        ]
    }

# Root endpoint with comprehensive API information
@app.get("/")
async def root():
    """Root endpoint with complete API information"""
    return {
        "message": "NSE IPO Tracker API v3.0 - Now with GMP Integration & Predictions!",
        "version": "3.0.0",
        "docs": "/docs",
        "health": "/health",
        "new_features_v3": {
            "gmp_integration": "Grey Market Premium data from multiple sources",
            "mathematical_predictions": "AI-powered IPO performance predictions",
            "risk_assessment": "Comprehensive risk analysis and scoring",
            "investment_advice": "BUY/HOLD/AVOID recommendations with confidence scores",
            "market_analysis": "Overall market sentiment and trend analysis"
        },
        "endpoints": {
            "nse_live": {
                "current_ipos": "/api/ipo/current",
                "upcoming_ipos": "/api/ipo/upcoming", 
                "market_status": "/api/ipo/market-status",
                "active_category": "/api/ipo/active-category/{symbol}",
                "test_connection": "/api/ipo/test",
                "refresh_session": "/api/ipo/refresh",
                "fetch_all": "/api/ipo/fetch-all"
            },
            "local_stored": {
                "current_ipos": "/api/local/current-ipos?date=YYYY-MM-DD",
                "upcoming_ipos": "/api/local/upcoming-ipos?date=YYYY-MM-DD",
                "market_status": "/api/local/market-status?date=YYYY-MM-DD",
                "active_category": "/api/local/active-category?symbol=XXX&date=YYYY-MM-DD",
                "available_dates": "/api/local/available-dates/{data_type}",
                "data_summary": "/api/local/summary",
                "cleanup": "/api/local/cleanup/{data_type}?keep_days=30"
            },
            "gmp_analysis": {
                "full_analysis": "/api/gmp/analyze",
                "get_recommendation": "/api/gmp/recommendation/{symbol}",
                "top_recommendations": "/api/gmp/top-recommendations?limit=5",
                "update_gmp_data": "/api/gmp/update-gmp",
                "prediction_explanation": "/api/gmp/explanation/{symbol}",
                "market_summary": "/api/gmp/market-summary"
            }
        },
        "data_types": [
            "current_ipos",
            "upcoming_ipos", 
            "market_status",
            "active_category",
            "ipo_gmp_analysis",
            "latest_gmp_data"
        ],
        "usage_examples": {
            "comprehensive_analysis": "POST /api/gmp/analyze",
            "get_specific_recommendation": "GET /api/gmp/recommendation/SOLARWORLD",
            "top_5_picks": "GET /api/gmp/top-recommendations?limit=5",
            "update_gmp_data": "POST /api/gmp/update-gmp",
            "market_overview": "GET /api/gmp/market-summary",
            "prediction_logic": "GET /api/gmp/explanation/SYMBOL"
        },
        "mathematical_model": {
            "components": {
                "gmp_analysis": "30% weight - Grey market premium from multiple sources",
                "subscription_analysis": "25% weight - Demand and subscription patterns", 
                "fundamental_analysis": "20% weight - Company and issue fundamentals",
                "market_conditions": "15% weight - Overall market environment",
                "risk_assessment": "10% weight - Risk factor evaluation"
            },
            "output": {
                "recommendation": "BUY/HOLD/AVOID",
                "risk_level": "LOW/MEDIUM/HIGH",
                "confidence_score": "0-100%",
                "expected_listing_gain": "Percentage",
                "expected_listing_price": "Rupees"
            }
        }
    }

# Test endpoint with comprehensive system status
@app.get("/test")
async def test_endpoint():
    """Comprehensive test endpoint for all services"""
    try:
        from .controllers.ipo_controller import ipo_controller
        from .controllers.local_controller import local_controller
        from .controllers.gmp_controller import gmp_controller
        
        # Test NSE connection
        nse_result = await ipo_controller.test_nse_connection()
        
        # Test local storage
        try:
            local_summary = await local_controller.get_data_summary()
            local_working = True
            local_message = f"Local storage working - {local_summary['summary'].get('total_files', 0)} files available"
        except Exception as e:
            local_working = False
            local_message = f"Local storage error: {str(e)}"
        
        # Test GMP service
        try:
            gmp_update = await gmp_controller.update_gmp_data()
            gmp_working = gmp_update.get('success', False)
            gmp_message = f"GMP service {'working' if gmp_working else 'has issues'}"
            if gmp_working:
                gmp_details = gmp_update.get('update_details', {})
                gmp_message += f" - {len(gmp_details.get('sources_scraped', []))} sources scraped"
        except Exception as e:
            gmp_working = False
            gmp_message = f"GMP service error: {str(e)}"
        
        overall_status = "READY" if (nse_result.get('success', False) and local_working and gmp_working) else "PARTIAL"
        
        return {
            "api_status": "API is working",
            "nse_connection": {
                "status": nse_result.get('success', False),
                "message": nse_result.get('message', 'Unknown'),
                "working_endpoints": nse_result.get('test_results', {}).get('working_endpoints', [])
            },
            "local_storage": {
                "status": local_working,
                "message": local_message
            },
            "gmp_service": {
                "status": gmp_working,
                "message": gmp_message
            },
            "overall_status": overall_status,
            "new_v3_features": [
                "✅ GMP data scraping from multiple sources",
                "✅ Mathematical prediction engine",
                "✅ Risk assessment and scoring",
                "✅ Investment recommendations",
                "✅ Market sentiment analysis"
            ],
            "recommendations": [
                "🔗 Use /api/ipo/ endpoints for live NSE data",
                "💾 Use /api/local/ endpoints for stored data",
                "🧮 Use /api/gmp/ endpoints for predictions and analysis",
                "📊 Check /api/gmp/market-summary for market overview",
                "🎯 Get specific recommendations with /api/gmp/recommendation/{symbol}"
            ]
        }
    except Exception as e:
        return {
            "api_status": "API has issues",
            "error": str(e),
            "message": "Check logs for details",
            "overall_status": "ERROR"
        }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 NSE IPO Tracker API v3.0: Starting up with GMP Integration...")
    
    # Verify data directory exists
    try:
        from .utils.file_storage import file_storage
        logger.info(f"📁 Data directory initialized: {file_storage.data_dir.absolute()}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize file storage: {e}")
    
    # Test NSE connection (optional)
    try:
        from .controllers.ipo_controller import ipo_controller
        test_result = await ipo_controller.test_nse_connection()
        if test_result.get('success'):
            logger.info("✅ NSE connection test: PASSED")
        else:
            logger.warning("⚠️ NSE connection test: FAILED (API still functional)")
    except Exception as e:
        logger.warning(f"⚠️ NSE connection test error: {e}")
    
    # Test GMP service (optional)
    try:
        from .services.gmp_scraper import gmp_scraper
        logger.info("🔍 GMP scraper initialized")
        logger.info("🧮 Mathematical prediction engine ready")
    except Exception as e:
        logger.warning(f"⚠️ GMP service initialization warning: {e}")
    
    logger.info("✅ Services initialized successfully - Ready for GMP-powered predictions!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 NSE IPO Tracker API v3.0: Shutting down...")
    
    # Cleanup NSE service
    try:
        from .services.nse_service import nse_service
        nse_service.cleanup()
        logger.info("🧹 NSE service cleanup completed")
    except Exception as e:
        logger.error(f"❌ NSE service cleanup error: {e}")
    
    # Cleanup GMP scraper
    try:
        from .services.gmp_scraper import gmp_scraper
        if hasattr(gmp_scraper, 'session'):
            gmp_scraper.session.close()
        logger.info("🧹 GMP scraper cleanup completed")
    except Exception as e:
        logger.error(f"❌ GMP scraper cleanup error: {e}")
    
    logger.info("✅ Shutdown completed")