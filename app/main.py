from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime

# Import routers with error handling
try:
    from app.routers import ipo, market
except ImportError as e:
    print(f"Import error: {e}")
    # Create dummy routers if import fails
    from fastapi import APIRouter
    ipo = APIRouter()
    market = APIRouter()

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
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

# Include routers with error handling
try:
    app.include_router(ipo.router, prefix="/api/ipo", tags=["IPO Data"])
    app.include_router(market.router, prefix="/api/market", tags=["Market Data"])
except Exception as e:
    logger.error(f"Router inclusion error: {e}")

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
            "✅ Anti-blocking web scraping",
            "✅ GMP (Gray Market Premium) tracking",
            "✅ Market indices tracking",
            "✅ Current, upcoming & past IPOs",
            "✅ RESTful API endpoints",
            "✅ Auto-retry mechanisms",
            "✅ Rate limiting protection"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "test": "/test",
            "current_ipos": "/api/ipo/current",
            "upcoming_ipos": "/api/ipo/upcoming", 
            "past_ipos": "/api/ipo/past",
            "gmp_data": "/api/ipo/gmp",
            "market_indices": "/api/market/indices",
            "market_status": "/api/market/status",
            "dashboard": "/api/market/dashboard"
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
    """Quick test of NSE connectivity"""
    try:
        from app.services.nse_service import NSEService
        
        nse_service = NSEService()
        test_results = await nse_service.test_all_endpoints()
        
        return {
            "message": "NSE API Test Completed",
            "timestamp": datetime.now().isoformat(),
            "success": True,
            **test_results
        }
        
    except Exception as e:
        logger.error(f"Test endpoint failed: {e}")
        return {
            "message": "Test failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "success": False
        }

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_server_error(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Something went wrong on our end",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)