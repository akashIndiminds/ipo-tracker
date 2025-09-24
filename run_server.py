# run_server.py
import uvicorn
import os
import sys
from pathlib import Path
import logging

def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 70)
    print("🚀 NSE IPO TRACKER API v2.0 - Real Data Only")
    print("=" * 70)
    print("📍 Server URL: http://localhost:8000")
    print("📊 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🧪 Test Connection: http://localhost:8000/test")
    print("-" * 70)
    print("🎯 IPO Endpoints:")
    print("   • Current IPOs: http://localhost:8000/api/ipo/current")
    print("   • Upcoming IPOs: http://localhost:8000/api/ipo/upcoming")
    print("   • Past IPOs: http://localhost:8000/api/ipo/past")
    print("   • IPO Summary: http://localhost:8000/api/ipo/summary")
    print("   • Search IPOs: http://localhost:8000/api/ipo/search?query=tata")
    print("   • Market Indices: http://localhost:8000/api/ipo/indices")
    print("   • Test NSE: http://localhost:8000/api/ipo/test")
    print("-" * 70)
    print("🔧 Features:")
    print("✅ Real NSE data only (No demo fallbacks)")
    print("✅ Proper error handling for NSE failures")
    print("✅ Session management with retry logic")
    print("✅ Rate limiting to avoid blocks")
    print("✅ Multiple endpoint fallbacks")
    print("✅ Clean MVC architecture")
    print("❌ No auto-generated fallback files")
    print("=" * 70)

def setup_basic_environment():
    """Setup basic environment without creating files"""
    try:
        # Add current directory to Python path
        current_dir = Path(__file__).parent.absolute()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))

        print("📁 Environment setup completed")
        return True

    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False

def check_required_files():
    """Check if required files exist"""
    print("\n🔍 Checking required files...")

    required_files = [
        ("app/main.py", "Main App"),
        ("app/controllers/ipo_controller.py", "IPO Controller"),
        ("app/services/nse_service.py", "NSE Service"),
        ("app/services/data_processor.py", "Data Processor"),
        ("app/routes/ipo_routes.py", "IPO Routes"),
    ]

    missing_files = []

    for file_path, display_name in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {display_name}")
        else:
            missing_files.append((file_path, display_name))
            print(f"   ❌ {display_name} - Missing: {file_path}")

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files!")
        print("📝 Please ensure these files exist:")
        for file_path, display_name in missing_files:
            print(f"   • {file_path}")
        print("\n💡 Create the missing files or check your file structure.")
        return False

    print("✅ All required files found")
    return True

def test_imports():
    """Test if the main modules can be imported"""
    print("\n🧪 Testing imports...")
    
    try:
        from app.main import app
        print("   ✅ Main app imported successfully")
        return True
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   💡 Check your file structure and imports")
        return False
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def main():
    """Main function to start the server"""
    try:
        # Print banner
        print_banner()

        # Setup basic environment
        print("\n🔧 Setting up environment...")
        if not setup_basic_environment():
            print("\n❌ Environment setup failed")
            sys.exit(1)

        # Check required files
        if not check_required_files():
            print("\n❌ Required files missing")
            print("💡 Please create the missing files first")
            sys.exit(1)

        # Test imports
        if not test_imports():
            print("\n❌ Import test failed")
            print("💡 Fix import errors before starting server")
            sys.exit(1)

        print("\n🚀 Starting server...")
        print("💡 Press Ctrl+C to stop the server")
        print("🔄 Server will auto-reload on file changes")
        print("-" * 70)

        # Start the server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True,
            reload_dirs=["app"],
        )

    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        print("Thank you for using NSE IPO Tracker API!")

    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        print("\n🔍 Troubleshooting steps:")
        print("1. Check if port 8000 is available")
        print("2. Ensure all required files exist")
        print("3. Check Python version (3.8+ required)")
        print("4. Install dependencies: pip install fastapi uvicorn requests")
        print("5. Check file permissions")

        # Debug info
        print(f"\n📋 Debug Info:")
        print(f"Python version: {sys.version}")
        print(f"Working directory: {os.getcwd()}")
        print(f"Platform: {sys.platform}")

        sys.exit(1)

if __name__ == "__main__":
    main()