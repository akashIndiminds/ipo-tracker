# run_server.py
import uvicorn
import os
import sys
from pathlib import Path
import logging

def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 80)
    print("🚀 NSE IPO TRACKER API v2.1 - Live Data + File Storage")
    print("=" * 80)
    print("🌐 Server URL: http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🧪 Comprehensive Test: http://localhost:8000/test")
    print("-" * 80)
    print("🎯 NSE Live Data Endpoints:")
    print("   • Current IPOs: http://localhost:8000/api/ipo/current")
    print("   • Upcoming IPOs: http://localhost:8000/api/ipo/upcoming")
    print("   • Market Status: http://localhost:8000/api/ipo/market-status")
    print("   • Active Category: http://localhost:8000/api/ipo/active-category/SYMBOL")
    print("   • Fetch All Data: http://localhost:8000/api/ipo/fetch-all")
    print("   • Test NSE Connection: http://localhost:8000/api/ipo/test")
    print("   • Refresh Session: http://localhost:8000/api/ipo/refresh")
    print("-" * 80)
    print("💾 Local Stored Data Endpoints:")
    print("   • Stored Current IPOs: http://localhost:8000/api/local/current-ipos")
    print("   • Stored Upcoming IPOs: http://localhost:8000/api/local/upcoming-ipos")
    print("   • Stored Market Status: http://localhost:8000/api/local/market-status")
    print("   • Stored Active Category: http://localhost:8000/api/local/active-category")
    print("   • Available Dates: http://localhost:8000/api/local/available-dates/current_ipos")
    print("   • Data Summary: http://localhost:8000/api/local/summary")
    print("   • Cleanup Old Files: http://localhost:8000/api/local/cleanup/current_ipos")
    print("-" * 80)
    print("🔧 New Features v2.1:")
    print("✅ Restructured architecture (Scraper + Service + Storage)")
    print("✅ Daily JSON file storage with metadata")
    print("✅ Local data serving without NSE dependency")
    print("✅ File management and cleanup utilities")
    print("✅ Date-based data retrieval")
    print("✅ Active category endpoint with bid information")
    print("✅ Comprehensive error handling and logging")
    print("✅ Separate controllers for live vs stored data")
    print("❌ No auto-generated fallback data")
    print("=" * 80)

def setup_environment():
    """Setup environment"""
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent.absolute()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))

        # Create data directory
        data_dir = current_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        print(f"📁 Environment setup completed")
        print(f"   Working Directory: {current_dir}")
        print(f"   Data Directory: {data_dir}")
        return True

    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False

def check_file_structure():
    """Check if all required files exist"""
    print("\n🔍 Checking file structure...")

    required_files = [
        ("app/main.py", "Main App"),
        ("app/services/nse_scraper.py", "NSE Scraper"),
        ("app/services/nse_service.py", "NSE Service"),
        ("app/utils/file_storage.py", "File Storage"),
        ("app/controllers/ipo_controller.py", "IPO Controller"),
        ("app/controllers/local_controller.py", "Local Controller"),
        ("app/routes/ipo_routes.py", "IPO Routes"),
        ("app/routes/local_routes.py", "Local Routes"),
    ]

    missing_files = []
    created_dirs = []

    # Check and create directories
    for directory in ["app", "app/services", "app/utils", "app/controllers", "app/routes", "app/models"]:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(directory)

    if created_dirs:
        print(f"   📁 Created directories: {', '.join(created_dirs)}")

    # Check files
    for file_path, display_name in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {display_name}")
        else:
            missing_files.append((file_path, display_name))
            print(f"   ❌ {display_name} - Missing: {file_path}")

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files!")
        print("💡 Please create these files using the provided code:")
        for file_path, display_name in missing_files:
            print(f"   • {file_path}")
        return False

    print("✅ All required files found")
    return True

def test_imports():
    """Test if the main modules can be imported"""
    print("\n🧪 Testing imports...")
    
    try:
        from app.main import app
        print("   ✅ Main app imported successfully")
        
        from app.services.nse_service import nse_service
        print("   ✅ NSE service imported")
        
        from app.utils.file_storage import file_storage
        print("   ✅ File storage imported")
        
        from app.controllers.ipo_controller import ipo_controller
        print("   ✅ IPO controller imported")
        
        from app.controllers.local_controller import local_controller
        print("   ✅ Local controller imported")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   💡 Check your file structure and imports")
        return False
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def verify_dependencies():
    """Verify required Python packages"""
    print("\n📦 Verifying dependencies...")
    
    required_packages = [
        ('fastapi', 'FastAPI framework'),
        ('uvicorn', 'ASGI server'),
        ('requests', 'HTTP library'),
        ('pydantic', 'Data validation')
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {description}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {description} - Missing: {package}")
    
    if missing_packages:
        print(f"\n❌ Missing {len(missing_packages)} packages!")
        print("💡 Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies available")
    return True

def quick_system_test():
    """Quick test of core functionality"""
    print("\n⚡ Quick system test...")
    
    try:
        # Test file storage
        from app.utils.file_storage import file_storage
        summary = file_storage.get_all_data_summary()
        print(f"   📁 Data files: {summary.get('total_files', 0)}")
        print(f"   💽 Storage size: {summary.get('total_size_mb', 0)} MB")
        
        # Test NSE service (quick test)
        from app.services.nse_service import nse_service
        session_info = nse_service.get_session_info()
        print(f"   🔗 NSE session: {'Active' if session_info.get('session_active') else 'Inactive'}")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️ System test warning: {e}")
        return True  # Don't fail startup for this

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

        # Check file structure
        if not check_file_structure():
            print("\n❌ Required files missing")
            print("💡 Please create all required files first")
            sys.exit(1)

        # Verify dependencies
        if not verify_dependencies():
            print("\n❌ Missing dependencies")
            print("💡 Install required packages first")
            sys.exit(1)

        # Test imports
        if not test_imports():
            print("\n❌ Import test failed")
            print("💡 Fix import errors before starting server")
            sys.exit(1)

        # Quick system test
        quick_system_test()

        print("\n🚀 Starting server...")
        print("💡 Press Ctrl+C to stop the server")
        print("🔄 Server will auto-reload on file changes")
        print("📊 Visit http://localhost:8000/docs for API documentation")
        print("-" * 80)

        # Start the server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True,
            reload_dirs=["app"],
            reload_excludes=["data/*"]  # Don't reload on data file changes
        )

    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        print("Thank you for using NSE IPO Tracker API v2.1!")

    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if port 8000 is available")
        print("2. Ensure all required files exist")
        print("3. Check Python version (3.8+ required)")
        print("4. Install dependencies: pip install fastapi uvicorn requests pydantic")
        print("5. Check file permissions")
        print("6. Run test first: python test_nse_connection.py")

        # Debug info
        print(f"\n📋 Debug Info:")
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Platform: {sys.platform}")

        sys.exit(1)

if __name__ == "__main__":
    main()