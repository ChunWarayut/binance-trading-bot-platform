#!/usr/bin/env python3
import subprocess
import time
import requests
import sys
import os

def test_service():
    print("🔧 Simple Service Test")
    print("=====================")
    
    # Kill any existing processes
    print("1. Cleaning up processes...")
    subprocess.run("pkill -f 'python.*main.py' 2>/dev/null || true", shell=True)
    subprocess.run("pkill -f 'streamlit' 2>/dev/null || true", shell=True)
    subprocess.run("pkill -f 'uvicorn' 2>/dev/null || true", shell=True)
    time.sleep(3)
    
    # Start main bot
    print("2. Starting main bot...")
    subprocess.Popen(["python3", "main.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    
    # Start API
    print("3. Starting API...")
    subprocess.Popen(["python3", "realtime_api.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5)
    
    # Start Streamlit
    print("4. Starting Streamlit...")
    subprocess.Popen(["streamlit", "run", "enhanced_web_ui.py", "--server.port", "8501"], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(10)
    
    # Test connectivity
    print("5. Testing connectivity...")
    
    # Test API
    try:
        response = requests.get("http://localhost:8080/api/bot_status", timeout=5)
        if response.status_code == 200:
            print("✅ API is working!")
            print(f"   Status: {response.json().get('status', 'Unknown')}")
        else:
            print(f"❌ API returned {response.status_code}")
    except Exception as e:
        print(f"❌ API not accessible: {e}")
    
    # Test Streamlit
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit is working!")
        else:
            print(f"❌ Streamlit returned {response.status_code}")
    except Exception as e:
        print(f"❌ Streamlit not accessible: {e}")
    
    print("\n🎯 Access URLs:")
    print("📊 Dashboard: http://localhost:8501")
    print("🔌 API: http://localhost:8080/api/")
    print("✅ Test completed!")

if __name__ == "__main__":
    test_service() 