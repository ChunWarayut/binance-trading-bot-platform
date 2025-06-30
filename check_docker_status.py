#!/usr/bin/env python3
import subprocess
import requests
import time
import json

def check_docker():
    """Check Docker container status"""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if 'crypto-trading-bot' in result.stdout:
            return True, "Container is running"
        else:
            return False, "Container not found"
    except Exception as e:
        return False, f"Docker error: {e}"

def check_api():
    """Check API status"""
    try:
        response = requests.get('http://localhost:8080/api/bot_status', timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"API error: {e}"

def check_streamlit():
    """Check Streamlit status"""
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        return response.status_code == 200, f"HTTP {response.status_code}"
    except Exception as e:
        return False, f"Streamlit error: {e}"

def main():
    print("🔍 DOCKER TRADING BOT STATUS CHECK")
    print("==================================")
    
    # Check Docker container
    docker_ok, docker_msg = check_docker()
    print(f"🐳 Docker Container: {'✅' if docker_ok else '❌'} {docker_msg}")
    
    # Check API
    api_ok, api_data = check_api()
    print(f"⚡ API Service: {'✅' if api_ok else '❌'} {api_data if not api_ok else 'Working'}")
    if api_ok and isinstance(api_data, dict):
        print(f"   - Bot Running: {'✅' if api_data.get('running') else '❌'}")
        print(f"   - Active Trades: {api_data.get('active_trades_count', 0)}")
    
    # Check Streamlit
    streamlit_ok, streamlit_msg = check_streamlit()
    print(f"📱 Streamlit: {'✅' if streamlit_ok else '❌'} {streamlit_msg}")
    
    # Overall status
    all_ok = docker_ok and api_ok and streamlit_ok
    print(f"\n🎯 Overall Status: {'✅ ALL SYSTEMS OPERATIONAL' if all_ok else '⚠️ SOME ISSUES DETECTED'}")
    
    if all_ok:
        print("\n🚀 ACCESS POINTS:")
        print("📱 Dashboard: http://localhost:8501")
        print("⚡ API: http://localhost:8080")
        print("📚 API Docs: http://localhost:8080/docs")
    else:
        print("\n🔧 SUGGESTED ACTIONS:")
        if not docker_ok:
            print("- Start Docker container: python3 run_docker_now.py")
        if not api_ok:
            print("- Check API logs: docker logs crypto-trading-bot")
        if not streamlit_ok:
            print("- Check Streamlit logs: docker logs crypto-trading-bot")

if __name__ == "__main__":
    main() 