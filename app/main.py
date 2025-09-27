# app/main.py
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from .routes.ipo_routes import router as ipo_router
from .routes.local_routes import router as local_router
from .routes.gmp_routes import router as gmp_router
from .routes.gmp_history_routes import router as gmp_history_router
from .routes.ai_routes import router as ai_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NSE IPO Tracker API v4.0 - With GMP, AI & Mathematical Predictions",
    description="Real-time IPO tracking with NSE integration, GMP analysis, Gemini AI predictions, and pure mathematical models",
    version="4.0.0",
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

# Include routers
app.include_router(ipo_router)
app.include_router(local_router)
app.include_router(gmp_router)
app.include_router(gmp_history_router)
app.include_router(ai_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NSE IPO Tracker API with GMP, AI & Mathematical Predictions",
        "version": "4.0.0",
        "message": "API is running successfully"
    }

# Root endpoint with comprehensive API information
@app.get("/")
async def root():
    """Root endpoint with complete API information"""
    return {
        "message": "NSE IPO Tracker API v4.0 - Now with Gemini AI Integration!",
        "version": "4.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "nse_live": {
                "current_ipos": "/api/ipo/current",
                "upcoming_ipos": "/api/ipo/upcoming", 
                "market_status": "/api/ipo/market-status",
                "active_category": "/api/ipo/active-category/{symbol}"
            },
            "gmp_analysis": {
                "full_analysis": "/api/gmp/analyze",
                "get_recommendation": "/api/gmp/recommendation/{symbol}",
                "top_recommendations": "/api/gmp/top-recommendations?limit=5",
                "market_summary": "/api/gmp/market-summary"
            },
            "ai_predictions": {
                "analyze_all_with_ai": "/api/ai/analyze-all",
                "get_ai_prediction": "/api/ai/prediction/{symbol}",
                "refresh_ai_predictions": "/api/ai/refresh",
                "get_stored_predictions": "/api/ai/stored-predictions"
            }
        }
    }

# Test endpoint - SIMPLIFIED (no actual tests)
@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {
        "api_status": "Ready",
        "message": "Use individual endpoints to test services",
        "endpoints": {
            "test_nse": "/api/ipo/test",
            "test_gmp": "/api/gmp/update-gmp",
            "test_ai": "/api/ai/stored-predictions"
        }
    }

# Simplified startup - NO TESTS
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup - NO TESTS"""
    logger.info("🚀 API Started - v4.0")
    
    # Just create data directory
    try:
        from pathlib import Path
        Path("data").mkdir(exist_ok=True)
    except:
        pass

# Simplified shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 API Shutdown")