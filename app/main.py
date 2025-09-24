# app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from .routes.ipo_routes import router as ipo_router
from .routes.local_routes import router as local_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NSE IPO Tracker API v2.1",
    description="Real-time IPO tracking with NSE integration and local storage",
    version="2.1.0",
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NSE IPO Tracker API",
        "version": "2.1.0",
        "message": "API is running successfully",
        "features": [
            "NSE Live Data",
            "Local Data Storage", 
            "File-based Caching",
            "Daily Data Archives"
        ]
    }

# Root endpoint with comprehensive API information
@app.get("/")
async def root():
    """Root endpoint with complete API information"""
    return {
        "message": "NSE IPO Tracker API v2.1",
        "version": "2.1.0",
        "docs": "/docs",
        "health": "/health",
        "features": {
            "nse_live_data": "Fetch real-time data from NSE",
            "local_storage": "Store and retrieve daily data files",
            "file_caching": "Automatic JSON file management",
            "date_filtering": "Query data by specific dates"
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
            }
        },
        "data_types": [
            "current_ipos",
            "upcoming_ipos", 
            "market_status",
            "active_category"
        ],
        "usage_examples": {
            "fetch_and_store": "POST /api/ipo/fetch-all",
            "get_today_data": "GET /api/local/current-ipos",
            "get_specific_date": "GET /api/local/current-ipos?date=2025-09-24",
            "check_available_dates": "GET /api/local/available-dates/current_ipos",
            "get_symbol_data": "GET /api/ipo/active-category/SOLARWORLD"
        }
    }

# Test endpoint with both NSE and local data status
@app.get("/test")
async def test_endpoint():
    """Comprehensive test endpoint for both NSE and local services"""
    try:
        from .controllers.ipo_controller import ipo_controller
        from .controllers.local_controller import local_controller
        
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
            "overall_status": "READY" if nse_result.get('success', False) and local_working else "PARTIAL",
            "recommendations": [
                "✅ API is fully functional" if nse_result.get('success', False) and local_working else "⚠️ Some services may be limited",
                "🔗 Use /api/ipo/ endpoints for live NSE data",
                "💾 Use /api/local/ endpoints for stored data",
                "📊 Check /api/local/summary for data overview"
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
    logger.info("🚀 NSE IPO Tracker API v2.1: Starting up...")
    
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
    
    logger.info("✅ Services initialized successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 NSE IPO Tracker API: Shutting down...")
    
    # Cleanup NSE service
    try:
        from .services.nse_service import nse_service
        nse_service.cleanup()
        logger.info("🧹 NSE service cleanup completed")
    except Exception as e:
        logger.error(f"❌ NSE service cleanup error: {e}")
    
    logger.info("✅ Shutdown completed")