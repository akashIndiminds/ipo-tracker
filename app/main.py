from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ipo, market
import logging
import os
from datetime import datetime

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ipo_tracker.log'),
        logging.StreamHandler()
    ]
)

app = FastAPI(
    title="IPO Tracker API",
    description="Complete IPO tracking and market analysis API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ipo.router, prefix="/api/ipo", tags=["IPO"])
app.include_router(market.router, prefix="/api/market", tags=["Market"])

@app.get("/")
async def root():
    return {
        "message": "IPO Tracker API is running!",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ipo-tracker",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)