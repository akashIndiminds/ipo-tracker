import uvicorn
import os

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    print("🚀 Starting IPO Tracker API Server...")
    print("📍 Server will run at: http://localhost:8000")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )