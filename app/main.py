# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
import sys
from pathlib import Path

# Setup logging first
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ipo_tracker.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IPO Tracker API",
    description="Complete IPO tracking and market analysis API with NSE data scraping",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers with error handling
try:
    from app.routers.ipo import router as ipo_router
    app.include_router(ipo_router)
    logger.info("✅ IPO router loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load IPO router: {e}")

try:
    from app.routers.market import router as market_router  
    app.include_router(market_router)
    logger.info("✅ Market router loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load Market router: {e}")

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("🚀 IPO Tracker API v2.0 Starting Up...")
    logger.info("📍 Server URL: http://localhost:8000")
    logger.info("📊 API Docs: http://localhost:8000/docs")
    logger.info("🧪 Test Endpoint: http://localhost:8000/test")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("🛑 IPO Tracker API Shutting Down...")
    
    # Cleanup resources
    try:
        from app.controllers.ipo_controller import ipo_controller
        ipo_controller.cleanup()
    except:
        pass

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "🚀 IPO Tracker API v2.0 - NSE Data Scraping",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "features": [
            "✅ Real-time IPO data from NSE",
            "✅ Advanced anti-blocking web scraping",
            "✅ Gray Market Premium (GMP) tracking",
            "✅ Market indices tracking",
            "✅ Current, upcoming & past IPOs",
            "✅ RESTful API endpoints",
            "✅ Auto-retry mechanisms",
            "✅ Rate limiting protection",
            "✅ MVC Architecture",
            "✅ Data validation & cleaning"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "test": "/test",
            "current_ipos": "/api/ipo/current",
            "upcoming_ipos": "/api/ipo/upcoming", 
            "past_ipos": "/api/ipo/past",
            "gmp_data": "/api/ipo/gmp",
            "ipo_summary": "/api/ipo/summary",
            "search_ipos": "/api/ipo/search",
            "market_indices": "/api/market/indices",
            "market_status": "/api/market/status",
            "market_dashboard": "/api/market/dashboard"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ipo-tracker-api",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }

@app.get("/test")
async def quick_test():
    """Quick test of all services"""
    try:
        from app.controllers.ipo_controller import ipo_controller
        
        # Test NSE connection
        test_results = await ipo_controller.test_nse_connection()
        
        return {
            "message": "Service connectivity test completed",
            "timestamp": datetime.now().isoformat(),
            **test_results
        }
        
    except Exception as e:
        logger.error(f"❌ Test endpoint failed: {e}")
        return {
            "message": "Service test failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False
        }

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Something went wrong on our end",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": f"The endpoint {request.url.path} was not found",
            "timestamp": datetime.now().isoformat(),
            "available_endpoints": [
                "/docs", "/health", "/test",
                "/api/ipo/current", "/api/ipo/upcoming", 
                "/api/ipo/past", "/api/ipo/gmp", "/api/ipo/summary"
            ]
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )