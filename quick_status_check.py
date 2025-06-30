#!/usr/bin/env python3
import subprocess
import requests
import json
from datetime import datetime

def main():
    status = {"timestamp": datetime.now().isoformat()}
    
    # Check Docker
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        status['docker_ps_output'] = result.stdout
        status['docker_container_running'] = 'crypto-trading-bot' in result.stdout
    except Exception as e:
        status['docker_error'] = str(e)
        status['docker_container_running'] = False
    
    # Check API
    try:
        response = requests.get('http://localhost:8080/api/bot_status', timeout=5)
        status['api_working'] = response.status_code == 200
        if response.status_code == 200:
            status['api_data'] = response.json()
    except Exception as e:
        status['api_working'] = False
        status['api_error'] = str(e)
    
    # Check Streamlit
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        status['streamlit_working'] = response.status_code == 200
    except Exception as e:
        status['streamlit_working'] = False
        status['streamlit_error'] = str(e)
    
    # Check processes
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        status['python_main_running'] = 'python' in result.stdout and 'main.py' in result.stdout
        status['uvicorn_running'] = 'uvicorn' in result.stdout
        status['streamlit_process'] = 'streamlit' in result.stdout
    except Exception as e:
        status['process_error'] = str(e)
    
    # Save to file
    with open('status_report.json', 'w') as f:
        json.dump(status, f, indent=2)
    
    # Simple print
    if status.get('docker_container_running'):
        print("✅ Docker container is running")
    elif status.get('api_working'):
        print("✅ API is working (Python mode)")
    else:
        print("❌ No services detected")

if __name__ == "__main__":
    main() 