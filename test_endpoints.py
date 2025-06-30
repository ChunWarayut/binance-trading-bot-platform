#!/usr/bin/env python3
import requests
import json

def test_services():
    results = {}
    
    # Test API
    try:
        response = requests.get('http://localhost:8080/api/bot_status', timeout=5)
        results['api'] = {
            'status': response.status_code,
            'working': response.status_code == 200,
            'data': response.json() if response.status_code == 200 else None
        }
    except Exception as e:
        results['api'] = {'working': False, 'error': str(e)}
    
    # Test Streamlit
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        results['streamlit'] = {
            'status': response.status_code,
            'working': response.status_code == 200
        }
    except Exception as e:
        results['streamlit'] = {'working': False, 'error': str(e)}
    
    # Save and display
    with open('endpoint_test.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    if results['api']['working']:
        print("✅ API WORKING")
        if results['api']['data']:
            data = results['api']['data']
            print(f"   Bot Running: {'✅' if data.get('running') else '❌'}")
            print(f"   Active Trades: {data.get('active_trades_count', 0)}")
    else:
        print("❌ API NOT WORKING")
    
    if results['streamlit']['working']:
        print("✅ STREAMLIT WORKING")
    else:
        print("❌ STREAMLIT NOT WORKING")

if __name__ == "__main__":
    test_services() 