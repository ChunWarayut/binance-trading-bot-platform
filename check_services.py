#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime

def check_services():
    results = {
        "timestamp": datetime.now().isoformat(),
        "api_status": False,
        "streamlit_status": False,
        "api_data": None,
        "errors": []
    }
    
    # Check API
    try:
        response = requests.get("http://localhost:8080/api/bot_status", timeout=5)
        if response.status_code == 200:
            results["api_status"] = True
            results["api_data"] = response.json()
        else:
            results["errors"].append(f"API returned status {response.status_code}")
    except Exception as e:
        results["errors"].append(f"API error: {str(e)}")
    
    # Check Streamlit
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            results["streamlit_status"] = True
        else:
            results["errors"].append(f"Streamlit returned status {response.status_code}")
    except Exception as e:
        results["errors"].append(f"Streamlit error: {str(e)}")
    
    # Save results
    with open("service_check.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    check_services() 