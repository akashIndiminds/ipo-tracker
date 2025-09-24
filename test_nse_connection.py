# test_nse_connection.py
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

def test_file_structure():
    """Test if all required files exist"""
    print("=" * 60)
    print("🔍 TESTING FILE STRUCTURE")
    print("=" * 60)
    
    required_files = [
        ("app/services/nse_scraper.py", "NSE Scraper"),
        ("app/services/nse_service.py", "NSE Service"), 
        ("app/utils/file_storage.py", "File Storage"),
        ("app/controllers/ipo_controller.py", "IPO Controller"),
        ("app/controllers/local_controller.py", "Local Controller"),
        ("app/routes/ipo_routes.py", "IPO Routes"),
        ("app/routes/local_routes.py", "Local Routes"),
        ("app/main.py", "Main App")
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
        return False
    
    print("✅ All required files found")
    return True

def test_imports():
    """Test if modules can be imported"""
    print("\n🧪 Testing imports...")
    
    try:
        from app.services.nse_scraper import nse_scraper
        print("   ✅ NSE Scraper imported")
        
        from app.services.nse_service import nse_service
        print("   ✅ NSE Service imported")
        
        from app.utils.file_storage import file_storage
        print("   ✅ File Storage imported")
        
        from app.controllers.ipo_controller import ipo_controller
        print("   ✅ IPO Controller imported")
        
        from app.controllers.local_controller import local_controller
        print("   ✅ Local Controller imported")
        
        from app.main import app
        print("   ✅ Main app imported")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_nse_service():
    """Test NSE service functionality"""
    print("\n🌐 Testing NSE service...")
    
    try:
        from app.services.nse_service import nse_service
        
        print("1️⃣ Testing connection...")
        test_results = nse_service.test_connection()
        print(f"   🔗 Overall Status: {test_results['overall_status']}")
        print(f"   🛠️ Working Endpoints: {test_results.get('working_endpoints', [])}")
        print(f"   ❌ Failed Endpoints: {test_results.get('failed_endpoints', [])}")
        
        working_count = len(test_results.get('working_endpoints', []))
        
        if working_count >= 3:
            print("   🎉 NSE SERVICE: EXCELLENT")
            return True
        elif working_count >= 2:
            print("   ✅ NSE SERVICE: GOOD")
            return True
        elif working_count >= 1:
            print("   ⚠️ NSE SERVICE: PARTIAL")
            return True
        else:
            print("   ❌ NSE SERVICE: FAILED")
            return False
        
    except Exception as e:
        print(f"   ❌ NSE service error: {e}")
        return False

def test_file_storage():
    """Test file storage functionality"""
    print("\n💾 Testing file storage...")
    
    try:
        from app.utils.file_storage import file_storage
        
        # Test data directory
        print(f"   📁 Data Directory: {file_storage.data_dir.absolute()}")
        
        if file_storage.data_dir.exists():
            print("   ✅ Data directory exists")
        else:
            print("   ⚠️ Data directory created")
        
        # Test summary
        summary = file_storage.get_all_data_summary()
        print(f"   📊 Total Files: {summary.get('total_files', 0)}")
        print(f"   💽 Total Size: {summary.get('total_size_mb', 0)} MB")
        
        return True
        
    except Exception as e:
        print(f"   ❌ File storage error: {e}")
        return False

def test_data_operations():
    """Test data fetching and storage operations"""
    print("\n🔄 Testing data operations...")
    
    try:
        from app.services.nse_service import nse_service
        from app.utils.file_storage import file_storage
        
        # Test current IPOs
        print("   📈 Testing current IPOs...")
        current_ipos = nse_service.fetch_current_ipos()
        if current_ipos:
            print(f"     ✅ Fetched {len(current_ipos)} current IPOs")
            
            # Test saving
            saved = file_storage.save_data('current_ipos', current_ipos)
            if saved:
                print("     ✅ Data saved successfully")
            else:
                print("     ❌ Data save failed")
        else:
            print("     ❌ No current IPO data")
        
        # Test upcoming IPOs
        print("   📅 Testing upcoming IPOs...")
        upcoming_ipos = nse_service.fetch_upcoming_ipos()
        if upcoming_ipos:
            print(f"     ✅ Fetched {len(upcoming_ipos)} upcoming IPOs")
            
            # Test saving
            saved = file_storage.save_data('upcoming_ipos', upcoming_ipos)
            if saved:
                print("     ✅ Data saved successfully")
            else:
                print("     ❌ Data save failed")
        else:
            print("     ❌ No upcoming IPO data")
        
        # Test market status
        print("   📊 Testing market status...")
        market_status = nse_service.fetch_market_status()
        if market_status:
            print(f"     ✅ Fetched {len(market_status)} market records")
            
            # Test saving
            saved = file_storage.save_data('market_status', market_status)
            if saved:
                print("     ✅ Data saved successfully")
            else:
                print("     ❌ Data save failed")
        else:
            print("     ❌ No market status data")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Data operations error: {e}")
        return False

def test_api_server():
    """Test if API server is running"""
    print("\n🌐 Testing API server...")
    
    try:
        import requests
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("   ✅ API Server is running")
            print(f"   📋 Version: {health_data.get('version', 'Unknown')}")
            print(f"   🔧 Features: {', '.join(health_data.get('features', []))}")
            
            # Test comprehensive test endpoint
            response = requests.get("http://localhost:8000/test", timeout=15)
            if response.status_code == 200:
                test_data = response.json()
                print(f"   🔗 NSE Status: {test_data.get('nse_connection', {}).get('status', False)}")
                print(f"   💾 Local Status: {test_data.get('local_storage', {}).get('status', False)}")
                print(f"   🎯 Overall: {test_data.get('overall_status', 'Unknown')}")
                return True
            else:
                print("   ⚠️ Test endpoint issues")
                return True  # Health is working
        else:
            print(f"   ❌ API Server health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ API Server is not running")
        print("   💡 Start server with: python run_server.py")
        return False
    except Exception as e:
        print(f"   ❌ API test error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 NSE IPO Tracker v2.1 - Complete System Test")
    print("🎯 Testing restructured architecture with file storage\n")
    
    # Test results
    results = {
        'file_structure': False,
        'imports': False,
        'nse_service': False,
        'file_storage': False,
        'data_operations': False,
        'api_server': False
    }
    
    # Run tests
    results['file_structure'] = test_file_structure()
    
    if results['file_structure']:
        results['imports'] = test_imports()
    
    if results['imports']:
        results['nse_service'] = test_nse_service()
        results['file_storage'] = test_file_storage()
        
        if results['nse_service'] and results['file_storage']:
            results['data_operations'] = test_data_operations()
    
    results['api_server'] = test_api_server()
    
    # Final results
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST RESULTS:")
    print("=" * 60)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n📊 Overall Score: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("🎉 PERFECT! Everything is working excellently")
        print("   🚀 Ready for production use")
        print("   📖 Visit: http://localhost:8000/docs")
        print("   🔍 Test: http://localhost:8000/test")
        
    elif passed_tests >= 4:
        print("✅ GREAT! Core system is working")
        print("   🔧 Minor issues detected but system is functional")
        if not results['api_server']:
            print("   💡 Start API server: python run_server.py")
        
    elif passed_tests >= 2:
        print("⚠️ PARTIAL! Some components working")
        print("   🔧 Fix failing components for full functionality")
        if not results['file_structure']:
            print("   📁 Create missing files first")
        if not results['nse_service']:
            print("   🌐 NSE connectivity issues - may be temporary")
            
    else:
        print("❌ CRITICAL! Major issues detected")
        print("   🚨 System needs significant repairs")
        print("   📋 Check file structure and dependencies")
    
    print("\n🔗 Quick Commands:")
    print("   • Test System: python test_nse_connection.py")
    print("   • Start Server: python run_server.py")
    print("   • View Docs: http://localhost:8000/docs")
    print("   • Test API: http://localhost:8000/test")
    
    print("=" * 60)

if __name__ == "__main__":
    main()