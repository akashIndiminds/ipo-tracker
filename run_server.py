# run_server.py
import uvicorn
import os
import sys
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 80)
    print("🚀 NSE IPO TRACKER API v4.0 - With GMP, AI & Mathematical Predictions")
    print("=" * 80)
    print("🌐 Server URL: http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("-" * 80)
    print("📍 Main Endpoints:")
    print("   • NSE Data: http://localhost:8000/api/ipo/current")
    print("   • GMP Analysis: http://localhost:8000/api/gmp/analyze")
    print("   • AI Prediction: http://localhost:8000/api/ai/analyze-all")
    print("   • Recommendation: http://localhost:8000/api/gmp/recommendation/SYMBOL")
    print("=" * 80)

def main():
    """Main function to start the server"""
    try:
        # Print banner
        print_banner()

        # Create data directory if not exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        print("\n🚀 Starting server...")
        print("💡 Press Ctrl+C to stop")
        print("-" * 80)

        # Start the server directly
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True,
            reload_dirs=["app"],
            reload_excludes=["data/*"]
        )

    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")

    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()