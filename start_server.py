
import uvicorn
import os
import sys
from pathlib import Path

def print_banner():
    """Print startup banner"""
    print("\n" + "="*60)
    print("🚀 IPO TRACKER API v2.0 - NSE Data Scraping")
    print("="*60)
    print("📍 Server URL: http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🧪 Test Endpoint: http://localhost:8000/test")
    print("💹 Current IPOs: http://localhost:8000/api/ipo/current")
    print("🔮 Upcoming IPOs: http://localhost:8000/api/ipo/upcoming")
    print("📊 Market Indices: http://localhost:8000/api/market/indices")
    print("🎛️ Market Dashboard: http://localhost:8000/api/market/dashboard")
    print("="*60)
    print("Features:")
    print("✅ Anti-blocking NSE data fetching")
    print("✅ CloudFlare bypass capabilities")
    print("✅ Multiple fallback strategies")
    print("✅ Rate limiting protection")
    print("✅ Proper MVC architecture")
    print("✅ Data validation & cleaning")
    print("✅ Comprehensive error handling")
    print("✅ Real-time market data")
    print("="*60)

def setup_environment():
    """Setup necessary directories and environment"""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Add current directory to Python path
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    print("📁 Environment setup completed")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'requests',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing dependencies: {', '.join(missing_packages)}")
        print("📥 Install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def main():
    """Main function to start the server"""
    try:
        # Print banner
        print_banner()
        
        # Setup environment
        setup_environment()
        
        # Check dependencies
        if not check_dependencies():
            print("\n❌ Cannot start server due to missing dependencies")
            sys.exit(1)
        
        print("\n🔄 Starting server...")
        print("💡 Press Ctrl+C to stop the server")
        print("\n" + "-"*60)
        
        # Start the server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        print("Thank you for using IPO Tracker API!")
        
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        print("\n🔍 Troubleshooting:")
        print("1. Check if port 8000 is available")
        print("2. Ensure all dependencies are installed: pip install -r requirements.txt")
        print("3. Check if app/main.py exists and is valid")
        print("4. Verify Python version (3.8+ required)")
        sys.exit(1)

if __name__ == "__main__":
    main()