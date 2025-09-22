# run_server.py
import uvicorn
import os
import sys
from pathlib import Path
import logging
import subprocess

def print_banner():
    """Print startup banner"""
    print("\n" + "="*70)
    print("🚀 IPO TRACKER API v2.0 - Enhanced NSE Data Scraping")
    print("="*70)
    print("📍 Server URL: http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🧪 Test Endpoint: http://localhost:8000/test")
    print("-" * 70)
    print("🎯 IPO Endpoints:")
    print("   • Current IPOs: http://localhost:8000/api/ipo/current")
    print("   • Upcoming IPOs: http://localhost:8000/api/ipo/upcoming")
    print("   • Past IPOs: http://localhost:8000/api/ipo/past")
    print("   • GMP Data: http://localhost:8000/api/ipo/gmp")
    print("   • IPO Summary: http://localhost:8000/api/ipo/summary")
    print("   • Search IPOs: http://localhost:8000/api/ipo/search")
    print("-" * 70)
    print("🎛️ Market Endpoints:")
    print("   • Market Indices: http://localhost:8000/api/market/indices")
    print("   • Market Status: http://localhost:8000/api/market/status")
    print("   • Market Dashboard: http://localhost:8000/api/market/dashboard")
    print("="*70)
    print("🔧 Features:")
    print("✅ Advanced CloudFlare bypass")
    print("✅ Multiple NSE endpoint fallbacks")
    print("✅ Gray Market Premium tracking")
    print("✅ Rate limiting & session management")
    print("✅ Data validation & cleaning")
    print("✅ Proper MVC architecture")
    print("✅ Comprehensive error handling")
    print("✅ Real-time market data")
    print("✅ Demo data fallbacks")
    print("="*70)

def setup_environment():
    """Setup environment and directories"""
    try:
        # Create necessary directories
        directories = [
            "logs",
            "app",
            "app/controllers",
            "app/services", 
            "app/routers",
            "app/models",
            "app/utils"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        
        # Create __init__.py files
        init_files = [
            "app/__init__.py",
            "app/controllers/__init__.py",
            "app/services/__init__.py",
            "app/routers/__init__.py",
            "app/models/__init__.py",
            "app/utils/__init__.py"
        ]
        
        for init_file in init_files:
            init_path = Path(init_file)
            if not init_path.exists():
                init_path.write_text("# Auto-generated __init__.py\n")
        
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
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('requests', 'Requests'),
        ('pydantic', 'Pydantic'),
        ('cloudscraper', 'CloudScraper'),
        ('fake_useragent', 'FakeUserAgent'),
        ('bs4', 'BeautifulSoup4'),
        ('pandas', 'Pandas')
    ]
    
    missing_packages = []
    
    for package, display_name in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {display_name}")
        except ImportError:
            missing_packages.append(display_name)
            print(f"   ❌ {display_name} - Missing")
    
    if missing_packages:
        print(f"\n❌ Missing dependencies: {', '.join(missing_packages)}")
        print("📥 Install them with:")
        print("   pip install -r requirements.txt")
        print("\nOr install manually:")
        print("   pip install fastapi uvicorn requests pydantic cloudscraper fake-useragent beautifulsoup4 pandas")
        return False
    
    print("✅ All required dependencies are installed")
    return True

def install_dependencies():
    """Auto-install missing dependencies"""
    print("\n📦 Attempting to install missing dependencies...")
    
    try:
        # Check if requirements.txt exists
        if Path("requirements.txt").exists():
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        else:
            # Install essential packages
            essential_packages = [
                "fastapi==0.104.1",
                "uvicorn[standard]==0.24.0", 
                "requests==2.31.0",
                "cloudscraper==1.2.71",
                "fake-useragent==1.4.0",
                "beautifulsoup4==4.12.2",
                "pandas==2.1.3",
                "pydantic==2.5.0"
            ]
            
            for package in essential_packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_fallback_files():
    """Create minimal fallback files if imports fail"""
    try:
        # Create minimal controller if missing
        controller_file = Path("app/controllers/ipo_controller.py")
        if not controller_file.exists():
            controller_content = '''
from typing import Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class IPOController:
    def __init__(self):
        pass
    
    async def test_nse_connection(self) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Minimal mode - full functionality not available",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_current_ipos(self, include_gmp: bool = True) -> Dict[str, Any]:
        return {
            "success": True,
            "message": "Demo data - NSE API unavailable",
            "count": 1,
            "data": [{
                "symbol": "DEMO_IPO",
                "company_name": "Demo IPO Limited",
                "status": "Demo Data"
            }],
            "timestamp": datetime.now().isoformat()
        }

ipo_controller = IPOController()
'''
            controller_file.write_text(controller_content)
        
        # Create minimal router if missing
        router_file = Path("app/routers/ipo.py")
        if not router_file.exists():
            router_content = '''
from fastapi import APIRouter
from app.controllers.ipo_controller import ipo_controller

router = APIRouter(prefix="/api/ipo", tags=["IPO"])

@router.get("/test")
async def test_connection():
    return await ipo_controller.test_nse_connection()

@router.get("/current")
async def get_current():
    return await ipo_controller.get_current_ipos()
'''
            router_file.write_text(router_content)
        
        print("✅ Fallback files created")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create fallback files: {e}")
        return False

def test_import():
    """Test if the main app can be imported"""
    try:
        from app.main import app
        print("✅ Main app imported successfully")
        return True
    except Exception as e:
        print(f"⚠️ Main app import failed: {e}")
        return False

def main():
    """Main function to start the server"""
    try:
        # Print banner
        print_banner()
        
        # Setup environment
        print("\n🔧 Setting up environment...")
        if not setup_environment():
            print("\n❌ Environment setup failed")
            sys.exit(1)
        
        # Check dependencies
        if not check_dependencies():
            print("\n💡 Attempting to install missing dependencies...")
            if not install_dependencies():
                print("\n❌ Could not install dependencies automatically")
                print("Please install manually with:")
                print("pip install fastapi uvicorn requests cloudscraper fake-useragent beautifulsoup4 pandas")
                sys.exit(1)
            
            # Recheck after installation
            if not check_dependencies():
                print("\n❌ Dependencies still missing after installation attempt")
                sys.exit(1)
        
        # Create fallback files if needed
        create_fallback_files()
        
        # Test import
        print("\n🧪 Testing app import...")
        if not test_import():
            print("⚠️ Using minimal fallback mode")
        
        print("\n🚀 Starting server...")
        print("💡 Press Ctrl+C to stop the server")
        print("-" * 70)
        
        # Start the server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True,
            reload_dirs=["app"]
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        print("Thank you for using IPO Tracker API!")
        
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        print("\n🔍 Troubleshooting steps:")
        print("1. Check if port 8000 is available")
        print("2. Ensure Python 3.8+ is installed")
        print("3. Try: pip install --upgrade pip setuptools wheel")
        print("4. Try: pip install fastapi uvicorn requests")
        print("5. Check firewall/antivirus blocking")
        
        # Debug info
        print(f"\n📋 Debug Info:")
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Platform: {sys.platform}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()