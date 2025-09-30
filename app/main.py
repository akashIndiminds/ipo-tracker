from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import nse_routes, gmp_routes, math_routes, ai_routes, predict_routes ,local_routes
from app.routes import orchestrator_routes

# Pehle app initialize karo
app = FastAPI(
    title="IPO Tracker v5.0 - Clean Architecture",
    version="5.0.0"
)

# Phir routers add karo
app.include_router(nse_routes.router)
app.include_router(gmp_routes.router)
app.include_router(math_routes.router)
app.include_router(ai_routes.router)
app.include_router(predict_routes.router)
app.include_router(local_routes.router)
app.include_router(orchestrator_routes.router)

# Middleware add karo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    """API Information"""
    return {
        "name": "IPO Tracker v5.0",
        "version": "5.0.0",
        "endpoints": {
            "nse": {
                "current": "/api/nse/current",
                "upcoming": "/api/nse/upcoming"
            },
            "gmp": {
                "fetch": "/api/gmp/fetch",
                "predict": "/api/gmp/predict/{symbol}"
            },
            "math": {
                "predict": "/api/math/predict/{symbol}"
            },
            "ai": {
                "predict": "/api/ai/predict/{symbol}"
            },
            "final": {
                "single": "/api/predict/{symbol}",
                "all": "/api/predict/all"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
