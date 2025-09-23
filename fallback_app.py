from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="IPO Tracker API - Minimal Mode")


@app.get("/")
async def root():
    return {
        "message": "IPO Tracker API - Minimal Mode",
        "status": "Running with limited functionality",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "minimal"}
