
import uvicorn
import os
import sys
from pathlib import Path
import logging

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
    print("💰 GMP Data: http://localhost:8000/api/ipo/gmp")
    print("📊 Market Indices: http://localhost:8000/api/market/indices")
    print("🎛️ Market Dashboard: http://localhost:8000/api/market/dashboard")
    print("="*60)
    print("Features:")
    print("✅ Anti-blocking NSE data fetching")
    print("✅ CloudFlare bypass capabilities")
    print("✅ Gray Market Premium (GMP) tracking")
    print("✅ Multiple fallback strategies")
    print("✅ Rate limiting protection")
    print("✅ Proper MVC architecture")
    print("✅ Data validation & cleaning")
    print("✅ Comprehensive error handling")
    print("✅ Real-time market data")
    print("="*60)

def setup_environment():
    """Setup necessary directories and environment"""
    try:
        # Set proper encoding
        if sys.platform.startswith('win'):
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create app directory structure if not exists
        app_dir = Path("app")
        app_dir.mkdir(exist_ok=True)
        
        # Create __init__.py files to make directories packages
        init_files = [
            app_dir / "__init__.py",
            app_dir / "services" / "__init__.py",
            app_dir / "routers" / "__init__.py",
            app_dir / "models" / "__init__.py"
        ]
        
        for init_file in init_files:
            init_file.parent.mkdir(exist_ok=True)
            if not init_file.exists():
                init_file.write_text("# Auto-generated __init__.py\n", encoding='utf-8')
        
        # Add current directory to Python path
        current_dir = Path(__file__).parent.absolute()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        print("📁 Environment setup completed")
        return True
        
    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('requests', 'Requests'),
        ('pydantic', 'Pydantic'),
        ('cloudscraper', 'CloudScraper'),
        ('fake_useragent', 'FakeUserAgent'),
        ('bs4', 'BeautifulSoup4')
    ]
    
    missing_packages = []
    
    for package, display_name in required_packages:
        try:
            __import__(package)
            print(f"✅ {display_name}")
        except ImportError:
            missing_packages.append(display_name)
            print(f"❌ {display_name} - Missing")
    
    if missing_packages:
        print(f"\n❌ Missing dependencies: {', '.join(missing_packages)}")
        print("📥 Install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_file_encoding():
    """Check and fix file encoding issues"""
    try:
        # Check main app file
        app_main = Path("app") / "main.py"
        if app_main.exists():
            # Read and rewrite with proper encoding
            content = app_main.read_text(encoding='utf-8', errors='ignore')
            # Remove any null bytes
            clean_content = content.replace('\x00', '')
            app_main.write_text(clean_content, encoding='utf-8')
        
        print("✅ File encoding checked and cleaned")
        return True
        
    except Exception as e:
        print(f"⚠️ File encoding check warning: {e}")
        return True  # Continue anyway

def create_fallback_app():
    """Create a minimal fallback app if imports fail"""
    fallback_code = '''
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="IPO Tracker API - Minimal Mode")

@app.get("/")
async def root():
    return {
        "message": "IPO Tracker API - Minimal Mode",
        "status": "Running with limited functionality",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "mode": "minimal"}
'''
    
    try:
        fallback_file = Path("fallback_app.py")
        fallback_file.write_text(fallback_code, encoding='utf-8')
        return "fallback_app:app"
    except:
        return None

def main():
    """Main function to start the server"""
    try:
        # Print banner
        print_banner()
        
        # Setup environment
        if not setup_environment():
            print("\n❌ Cannot start server due to environment setup failure")
            sys.exit(1)
        
        # Check dependencies
        print("\n🔍 Checking dependencies...")
        if not check_dependencies():
            print("\n❌ Cannot start server due to missing dependencies")
            print("\n💡 Quick fix: pip install fastapi uvicorn requests pydantic cloudscraper fake-useragent beautifulsoup4")
            sys.exit(1)
        
        # Check file encoding
        print("\n🔧 Checking file encoding...")
        check_file_encoding()
        
        print("\n🔄 Starting server...")
        print("💡 Press Ctrl+C to stop the server")
        print("\n" + "-"*60)
        
        # Try to start the main app
        app_module = "app.main:app"
        
        try:
            # Test import first
            from app.main import app
            print("✅ Main app imported successfully")
        except Exception as import_error:
            print(f"⚠️ Main app import failed: {import_error}")
            print("🔄 Creating fallback app...")
            app_module = create_fallback_app()
            if not app_module:
                raise Exception("Could not create fallback app")
        
        # Configure logging
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
        
        # Start the server
        uvicorn.run(
            app_module,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True,
            log_config=log_config,
            reload_dirs=["app"] if Path("app").exists() else None
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
        print("5. Try running: python -c 'from app.main import app; print(\"Import OK\")'")
        
        # Additional debug info
        print(f"\n📋 Debug Info:")
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Python path: {sys.path[:3]}...")
        
        sys.exit(1)

if __name__ == "__main__":
    main()