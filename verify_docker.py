#!/usr/bin/env python3
import subprocess
import requests
import json
from datetime import datetime

def check_status():
    """Check all service status"""
    results = {}
    
    # Check Docker container
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        results['docker_container'] = 'crypto-trading-bot' in result.stdout
    except:
        results['docker_container'] = False
    
    # Check API
    try:
        response = requests.get('http://localhost:8080/api/bot_status', timeout=5)
        results['api_status'] = response.status_code == 200
        results['api_data'] = response.json() if response.status_code == 200 else None
    except:
        results['api_status'] = False
        results['api_data'] = None
    
    # Check Streamlit
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        results['streamlit_status'] = response.status_code == 200
    except:
        results['streamlit_status'] = False
    
    # Check processes
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        output = result.stdout.lower()
        results['python_main'] = 'python' in output and 'main.py' in output
        results['streamlit_process'] = 'streamlit' in output
        results['uvicorn_process'] = 'uvicorn' in output
    except:
        results['python_main'] = False
        results['streamlit_process'] = False
        results['uvicorn_process'] = False
    
    # Overall status
    docker_running = results['docker_container']
    api_working = results['api_status']
    
    if docker_running and api_working:
        results['overall_status'] = 'DOCKER_SUCCESS'
    elif api_working and not docker_running:
        results['overall_status'] = 'PYTHON_SUCCESS'
    else:
        results['overall_status'] = 'NEEDS_ATTENTION'
    
    results['timestamp'] = datetime.now().isoformat()
    
    return results

def main():
    """Main verification function"""
    status = check_status()
    
    # Save to file
    with open('current_status.json', 'w') as f:
        json.dump(status, f, indent=2)
    
    # Print summary
    print("🔍 CURRENT SYSTEM STATUS")
    print("========================")
    print(f"🐳 Docker Container: {'✅' if status['docker_container'] else '❌'}")
    print(f"⚡ API Service: {'✅' if status['api_status'] else '❌'}")
    print(f"📱 Streamlit: {'✅' if status['streamlit_status'] else '❌'}")
    print(f"🎯 Overall: {status['overall_status']}")
    
    if status['api_data']:
        print(f"🤖 Bot Running: {'✅' if status['api_data'].get('running') else '❌'}")
        print(f"💰 Active Trades: {status['api_data'].get('active_trades_count', 0)}")
    
    if status['overall_status'] == 'DOCKER_SUCCESS':
        print("\n🎉 DOCKER PRODUCTION IS RUNNING!")
        print("📱 Dashboard: http://localhost:8501")
        print("⚡ API: http://localhost:8080")
    elif status['overall_status'] == 'PYTHON_SUCCESS':
        print("\n🐍 PYTHON PRODUCTION IS RUNNING!")
        print("📱 Dashboard: http://localhost:8501")
        print("⚡ API: http://localhost:8080")
    else:
        print("\n⚠️ NEEDS ATTENTION - Some services not responding")
    
    return status

if __name__ == "__main__":
    main() 