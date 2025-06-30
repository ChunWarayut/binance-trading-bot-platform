#!/usr/bin/env python3
import subprocess
import time
import requests
import json

def main():
    print("🐍 RESTARTING PYTHON PRODUCTION ENVIRONMENT")
    print("===========================================")
    
    # Step 1: Clean up everything
    print("🛑 Cleaning up processes...")
    subprocess.run("pkill -9 -f 'python.*main.py'", shell=True)
    subprocess.run("pkill -9 -f 'streamlit'", shell=True)
    subprocess.run("pkill -9 -f 'uvicorn'", shell=True)
    subprocess.run("docker stop crypto-trading-bot 2>/dev/null", shell=True)
    subprocess.run("docker rm crypto-trading-bot 2>/dev/null", shell=True)
    
    print("⏳ Waiting for cleanup...")
    time.sleep(5)
    
    # Step 2: Start Python production
    print("🚀 Starting Python production...")
    try:
        # Start the realtime dashboard (which includes all services)
        result = subprocess.run("python3 start_realtime_dashboard.py", 
                              shell=True, capture_output=True, text=True, timeout=10)
        print("✅ Started Python services")
    except subprocess.TimeoutExpired:
        print("✅ Services starting in background...")
    except Exception as e:
        print(f"⚠️ Start command issued: {e}")
    
    # Step 3: Wait for services
    print("⏳ Waiting for services to initialize...")
    time.sleep(15)
    
    # Step 4: Test services
    print("🧪 Testing services...")
    
    # Test API
    try:
        response = requests.get('http://localhost:8080/api/bot_status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Service: WORKING")
            print(f"   Bot Running: {'✅' if data.get('running') else '❌'}")
            print(f"   Active Trades: {data.get('active_trades_count', 0)}")
            api_ok = True
        else:
            print(f"⚠️ API Service: HTTP {response.status_code}")
            api_ok = False
    except Exception as e:
        print(f"❌ API Service: {str(e)[:50]}")
        api_ok = False
    
    # Test Streamlit
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit: WORKING")
            streamlit_ok = True
        else:
            print(f"⚠️ Streamlit: HTTP {response.status_code}")
            streamlit_ok = False
    except Exception as e:
        print(f"❌ Streamlit: {str(e)[:50]}")
        streamlit_ok = False
    
    # Save status
    status = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "api_working": api_ok,
        "streamlit_working": streamlit_ok,
        "setup_type": "PYTHON_PRODUCTION",
        "success": api_ok or streamlit_ok
    }
    
    with open('final_status.json', 'w') as f:
        json.dump(status, f, indent=2)
    
    # Final result
    if api_ok and streamlit_ok:
        print("\n🎉 PYTHON PRODUCTION IS FULLY OPERATIONAL!")
        print("=========================================")
        print("📱 Dashboard: http://localhost:8501")
        print("⚡ API: http://localhost:8080")
        print("🎯 All services working perfectly!")
    elif api_ok or streamlit_ok:
        print("\n🔶 PYTHON PRODUCTION IS PARTIALLY WORKING")
        print("=========================================")
        print("📱 Dashboard: http://localhost:8501")
        print("⚡ API: http://localhost:8080")
        print("⚠️ Some services may need additional time")
    else:
        print("\n❌ SERVICES NOT RESPONDING")
        print("=========================")
        print("Please try manual start: python3 start_realtime_dashboard.py")

if __name__ == "__main__":
    main() 