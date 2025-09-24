# test_connection.py
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

def test_nse_service():
    """Test NSE service with working SSL fixes"""
    print("=" * 60)
    print("🧪 TESTING NSE SERVICE - SSL FIXED")
    print("=" * 60)
    
    try:
        print("1️⃣ Importing NSE Service...")
        from app.services.nse_service import nse_service
        print("   ✅ NSE Service imported successfully")
        
        print("\n2️⃣ Testing connection...")
        test_results = nse_service.test_connection()
        
        print(f"   🔗 Overall Status: {test_results['overall_status']}")
        print(f"   🛠️  Working Scrapers: {test_results.get('scrapers_working', [])}")
        print(f"   ❌ Failed Scrapers: {test_results.get('scrapers_failed', [])}")
        
        print("\n3️⃣ Testing current IPOs...")
        current_ipos = nse_service.fetch_current_ipos()
        if current_ipos and len(current_ipos) > 0:
            print(f"   ✅ Got {len(current_ipos)} current IPOs")
            
            # Show sample data
            sample = current_ipos[0]
            print(f"   📊 Sample IPO:")
            print(f"      Company: {sample.get('company_name', 'N/A')}")
            print(f"      Symbol: {sample.get('symbol', 'N/A')}")
            print(f"      Status: {sample.get('status', 'N/A')}")
            print(f"      Price: {sample.get('issue_price', 'N/A')}")
        else:
            print("   ❌ No current IPO data")
        
        print("\n4️⃣ Testing upcoming IPOs...")
        upcoming_ipos = nse_service.fetch_upcoming_ipos()
        if upcoming_ipos and len(upcoming_ipos) > 0:
            print(f"   ✅ Got {len(upcoming_ipos)} upcoming IPOs")
            
            # Show sample data
            sample = upcoming_ipos[0]
            print(f"   📅 Sample Upcoming IPO:")
            print(f"      Company: {sample.get('company_name', 'N/A')}")
            print(f"      Symbol: {sample.get('symbol', 'N/A')}")
            print(f"      Start Date: {sample.get('issue_start_date', 'N/A')}")
            print(f"      End Date: {sample.get('issue_end_date', 'N/A')}")
        else:
            print("   ❌ No upcoming IPO data")
        
        print("\n5️⃣ Testing market status...")
        market_status = nse_service.fetch_market_status()
        if market_status and len(market_status) > 0:
            print(f"   ✅ Got {len(market_status)} market records")
            
            # Show sample data
            sample = market_status[0]
            print(f"   📊 Sample Market Status:")
            print(f"      Market: {sample.get('market', 'N/A')}")
            print(f"      Status: {sample.get('market_status', 'N/A')}")
            print(f"      Date: {sample.get('trade_date', 'N/A')}")
        else:
            print("   ❌ No market status data")
        
        print("\n6️⃣ Session information...")
        session_info = nse_service.get_session_info()
        print(f"   🔗 Active: {session_info.get('session_active', False)}")
        print(f"   🛠️  Current Scraper: {session_info.get('current_scraper', 'Unknown')}")
        print(f"   📊 Total Requests: {session_info.get('request_count', 0)}")
        print(f"   🕒 Last Request: {session_info.get('last_request_seconds_ago', 0):.1f}s ago")
        
        # Calculate results
        print("\n" + "=" * 60)
        print("📊 DETAILED RESULTS:")
        print("=" * 60)
        
        working_services = 0
        total_services = 3
        
        if current_ipos and len(current_ipos) > 0:
            working_services += 1
            print("✅ Current IPOs: WORKING")
            print(f"   📋 Records: {len(current_ipos)}")
        else:
            print("❌ Current IPOs: NO DATA")
        
        if upcoming_ipos and len(upcoming_ipos) > 0:
            working_services += 1
            print("✅ Upcoming IPOs: WORKING")
            print(f"   📋 Records: {len(upcoming_ipos)}")
        else:
            print("❌ Upcoming IPOs: NO DATA")
        
        if market_status and len(market_status) > 0:
            working_services += 1
            print("✅ Market Status: WORKING")
            print(f"   📋 Records: {len(market_status)}")
        else:
            print("❌ Market Status: NO DATA")
        
        print(f"\n🎯 Working Services: {working_services}/{total_services}")
        print(f"📈 Success Rate: {(working_services/total_services)*100:.1f}%")
        
        # Final verdict
        if working_services >= 3:
            print("\n🎉 EXCELLENT: All NSE services working!")
        elif working_services >= 2:
            print("\n✅ GOOD: Most NSE services working!")
        elif working_services >= 1:
            print("\n⚠️  PARTIAL: Some NSE services working")
        else:
            print("\n❌ FAILED: No NSE services working")
        
        print("=" * 60)
        
        # Cleanup
        nse_service.cleanup()
        
        return working_services >= 1
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure the nse_service.py file is updated")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_server():
    """Test if API server is running"""
    print("\n🌐 Testing API Server...")
    
    try:
        import requests
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ API Server is running")
                
                # Test current IPOs endpoint
                try:
                    response = requests.get("http://localhost:8000/api/ipo/current", timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Current IPOs API working")
                        print(f"   📊 Success: {data.get('success', False)}")
                        print(f"   📋 Count: {data.get('count', 0)}")
                        print(f"   📡 Source: {data.get('source', 'Unknown')}")
                        return True
                    elif response.status_code == 503:
                        print("⚠️  Current IPOs API responding but NSE unavailable")
                        print("   💡 This is expected if NSE is blocking")
                        return True
                    else:
                        print(f"❌ Current IPOs API status: {response.status_code}")
                        try:
                            error_data = response.json()
                            print(f"   📄 Error: {error_data.get('detail', 'Unknown error')}")
                        except:
                            pass
                        return False
                except Exception as e:
                    print(f"❌ Current IPOs API test failed: {e}")
                    return False
            else:
                print(f"❌ API Server health check failed: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ API Server is not running")
            print("💡 Start server with: python run_server.py")
            return False
            
    except ImportError:
        print("❌ requests module not available")
        print("💡 Install with: pip install requests")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 NSE IPO Tracker - Complete Connection Test")
    print("🎯 Testing with SSL fixes and working scrapers\n")
    
    # Test NSE service directly
    service_working = test_nse_service()
    
    # Test API server
    api_working = test_api_server()
    
    # Final recommendations
    print("\n" + "=" * 60)
    print("🎯 FINAL RECOMMENDATIONS:")
    print("=" * 60)
    
    if service_working and api_working:
        print("🎉 PERFECT SETUP!")
        print("   ✅ NSE Service: WORKING")
        print("   ✅ API Server: WORKING")
        print("\n💡 Everything is ready:")
        print("   • Visit: http://localhost:8000/docs")
        print("   • Test: http://localhost:8000/api/ipo/current")
        print("   • View: http://localhost:8000/api/ipo/test")
        
    elif service_working and not api_working:
        print("✅ NSE Service working, API server not running")
        print("\n💡 Next steps:")
        print("   1. Start API server: python run_server.py")
        print("   2. Test endpoints: http://localhost:8000/docs")
        print("   3. Monitor logs for any issues")
        
    elif not service_working and api_working:
        print("⚠️  API Server running but NSE service has issues")
        print("\n💡 Troubleshooting:")
        print("   1. Check NSE connectivity")
        print("   2. Test connection: http://localhost:8000/api/ipo/test")
        print("   3. Try refreshing: http://localhost:8000/api/ipo/refresh")
        
    else:
        print("❌ Both NSE service and API server have issues")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Check internet connection")
        print("   2. Verify all files are created correctly")
        print("   3. NSE servers might be down")
        print("   4. Try using VPN if blocked")
        print("   5. Wait and retry later")
    
    print("\n📋 Quick Commands:")
    print("   • Test Service: python test_connection.py")
    print("   • Start Server: python run_server.py")
    print("   • SSL Test: python test_ssl_fix.py")
    
    print("=" * 60)

if __name__ == "__main__":
    main()# test_connection.py
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

def test_nse_service():
    """Test NSE service directly"""
    print("=" * 50)
    print("🧪 TESTING NSE SERVICE")
    print("=" * 50)
    
    try:
        print("1️⃣ Importing NSE Service...")
        from app.services.nse_service import nse_service
        print("   ✅ NSE Service imported")
        
        print("\n2️⃣ Testing connection...")
        test_results = nse_service.test_connection()
        print(f"   🔗 Overall Status: {test_results['overall_status']}")
        
        print("\n3️⃣ Testing current IPOs...")
        current_ipos = nse_service.fetch_current_ipos()
        if current_ipos:
            print(f"   ✅ Got {len(current_ipos)} current IPOs")
            # Show first IPO
            first = current_ipos[0]
            print(f"   📊 Sample: {first.get('company_name', 'N/A')}")
        else:
            print("   ❌ No current IPO data")
        
        print("\n4️⃣ Testing upcoming IPOs...")
        upcoming_ipos = nse_service.fetch_upcoming_ipos()
        if upcoming_ipos:
            print(f"   ✅ Got {len(upcoming_ipos)} upcoming IPOs")
        else:
            print("   ❌ No upcoming IPO data")
        
        print("\n5️⃣ Testing market status...")
        market_status = nse_service.fetch_market_status()
        if market_status:
            print(f"   ✅ Got market status")
        else:
            print("   ❌ No market status")
        
        print("\n6️⃣ Session info...")
        session_info = nse_service.get_session_info()
        print(f"   🔗 Active: {session_info.get('session_active', False)}")
        print(f"   📊 Requests: {session_info.get('request_count', 0)}")
        
        # Results
        print("\n" + "=" * 50)
        print("📊 RESULTS:")
        working_services = 0
        total_services = 3
        
        if current_ipos:
            working_services += 1
            print("✅ Current IPOs: WORKING")
        else:
            print("❌ Current IPOs: FAILED")
        
        if upcoming_ipos:
            working_services += 1
            print("✅ Upcoming IPOs: WORKING")
        else:
            print("❌ Upcoming IPOs: FAILED")
        
        if market_status:
            working_services += 1
            print("✅ Market Status: WORKING")
        else:
            print("❌ Market Status: FAILED")
        
        print(f"\n🎯 Working: {working_services}/{total_services}")
        
        if working_services >= 2:
            print("🎉 NSE SERVICE IS WORKING!")
        elif working_services >= 1:
            print("⚠️  NSE SERVICE PARTIALLY WORKING")
        else:
            print("❌ NSE SERVICE FAILED")
        
        print("=" * 50)
        
        # Cleanup
        nse_service.cleanup()
        
        return working_services >= 1
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_server():
    """Test if API server is running"""
    print("\n🌐 Testing API Server...")
    
    try:
        import requests
        
        # Test health
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Server is running")
            
            # Test IPO endpoint
            response = requests.get("http://localhost:8000/api/ipo/current", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ IPO API working - {data.get('count', 0)} records")
                return True
            elif response.status_code == 503:
                print("⚠️  IPO API responding but NSE blocked")
                return True
            else:
                print(f"❌ IPO API status: {response.status_code}")
        else:
            print(f"❌ API Server status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API Server not running: {e}")
        print("💡 Start with: python run_server.py")
        return False
    
    return False

def main():
    """Main test function"""
    print("🧪 NSE IPO Tracker Connection Test")
    
    # Test service
    service_ok = test_nse_service()
    
    # Test API
    api_ok = test_api_server()
    
    # Final recommendations
    print("\n" + "=" * 50)
    print("🎯 FINAL RECOMMENDATIONS:")
    print("=" * 50)
    
    if service_ok and api_ok:
        print("🎉 EVERYTHING WORKING!")
        print("   Visit: http://localhost:8000/docs")
    elif service_ok:
        print("✅ NSE Service working")
        print("   Run: python run_server.py")
    elif api_ok:
        print("✅ API running but NSE issues")
        print("   Check: http://localhost:8000/api/ipo/test")
    else:
        print("❌ Both service and API have issues")
        print("   • Check internet connection")
        print("   • NSE may be blocking requests")
        print("   • Try again later")
    
    print("=" * 50)

if __name__ == "__main__":
    main()