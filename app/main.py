# main.py
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from app.routes.ipo_routes import router as ipo_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IPO Tracker API",
    description="Complete IPO tracking system with NSE integration",
    version="1.0.0",
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

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "IPO Tracker API",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "IPO Tracker API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "current_ipos": "/api/ipo/current",
            "upcoming_ipos": "/api/ipo/upcoming", 
            "subscription_details": "/api/ipo/{symbol}/subscription",
            "market_status": "/api/ipo/market/status",
            "system_status": "/api/ipo/status",
            "refresh_data": "/api/ipo/refresh"
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("IPO Tracker API: Starting up...")
    logger.info("Services initialized successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("IPO Tracker API: Shutting down...")
    
    try:
        # Import and cleanup services
        from app.services.nse_scraper_service import nse_scraper_service
        from app.services.storage_service import storage_service
        from app.services.data_processor import DataProcessor  # ✅ Fixed
        
        nse_scraper_service.cleanup()
        storage_service.cleanup()
        # DataProcessor has static methods, so no cleanup needed
        
        logger.info("All services cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )