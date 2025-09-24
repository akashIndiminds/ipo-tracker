# app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes with correct path
from .routes.ipo_routes import router as ipo_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NSE IPO Tracker API",
    description="Real-time IPO tracking system with NSE integration",
    version="2.0.0",
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
        "service": "NSE IPO Tracker API",
        "version": "2.0.0",
        "message": "API is running successfully"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NSE IPO Tracker API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "current_ipos": "/api/ipo/current",
            "upcoming_ipos": "/api/ipo/upcoming",
            "market_status": "/api/ipo/market-status",
            "test_connection": "/api/ipo/test",
            "refresh_session": "/api/ipo/refresh"
        }
    }

# Test endpoint
@app.get("/test")
async def test_endpoint():
    """Quick test endpoint"""
    try:
        from .controllers.ipo_controller import ipo_controller
        result = await ipo_controller.test_nse_connection()
        return {
            "test_status": "API is working",
            "nse_connection": result.get('success', False),
            "message": result.get('message', 'Connection test completed')
        }
    except Exception as e:
        return {
            "test_status": "API has issues",
            "error": str(e),
            "message": "Check logs for details"
        }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 NSE IPO Tracker API: Starting up...")
    logger.info("✅ Services initialized successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 NSE IPO Tracker API: Shutting down...")
    logger.info("🧹 Cleanup completed")