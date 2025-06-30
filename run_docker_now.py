#!/usr/bin/env python3
import subprocess
import time
import sys
import requests
import json

def run_cmd(cmd):
    """Execute command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1

def main():
    print("🐳 STARTING DOCKER PRODUCTION ENVIRONMENT")
    print("=========================================")
    
    # 1. Stop existing processes
    print("\n🛑 Step 1: Stopping existing processes...")
    for proc in ["python.*main.py", "streamlit", "uvicorn"]:
        stdout, stderr, code = run_cmd(f"pkill -9 -f '{proc}'")
        print(f"   Stopped {proc}: {'✅' if code == 0 or 'no process found' in stderr.lower() else '⚠️'}")
    
    # 2. Clean Docker containers
    print("\n🗑️ Step 2: Cleaning Docker containers...")
    run_cmd("docker stop crypto-trading-bot")
    run_cmd("docker rm crypto-trading-bot")
    print("   Cleaned up existing containers ✅")
    
    # 3. Build Docker image
    print("\n🔨 Step 3: Building Docker image...")
    stdout, stderr, code = run_cmd("docker build -t crypto-trading-bot . --no-cache")
    if code == 0:
        print("   Docker build: ✅ SUCCESS")
    else:
        print(f"   Docker build: ❌ FAILED - {stderr[-200:]}")
        return False
    
    # 4. Start container
    print("\n🚀 Step 4: Starting container...")
    docker_run = """docker run -d \
        --name crypto-trading-bot \
        --restart unless-stopped \
        -p 8501:8501 \
        -p 8080:8080 \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd):/app \
        crypto-trading-bot"""
    
    stdout, stderr, code = run_cmd(docker_run)
    if code == 0:
        print("   Container start: ✅ SUCCESS")
        print(f"   Container ID: {stdout.strip()[:12]}...")
    else:
        print(f"   Container start: ❌ FAILED - {stderr}")
        return False
    
    # 5. Wait and test
    print("\n⏳ Step 5: Waiting for services (15 seconds)...")
    time.sleep(15)
    
    # 6. Test services
    print("\n🧪 Step 6: Testing services...")
    
    # Test API
    try:
        response = requests.get("http://localhost:8080/api/bot_status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("   API Service: ✅ WORKING")
            print(f"   Bot Status: {'RUNNING' if data.get('running') else 'STOPPED'}")
            print(f"   Active Trades: {data.get('active_trades_count', 0)}")
        else:
            print(f"   API Service: ⚠️ HTTP {response.status_code}")
    except Exception as e:
        print(f"   API Service: ❌ ERROR - {str(e)[:50]}")
    
    # Test Streamlit
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        print(f"   Streamlit: {'✅ WORKING' if response.status_code == 200 else '⚠️ ISSUE'}")
    except Exception as e:
        print(f"   Streamlit: ❌ ERROR - {str(e)[:50]}")
    
    # 7. Show status
    print("\n🐳 Step 7: Container status...")
    stdout, stderr, code = run_cmd("docker ps | grep crypto-trading-bot")
    if stdout:
        print("   Container: ✅ RUNNING")
        print(f"   Status: {stdout.strip()}")
    else:
        print("   Container: ❌ NOT FOUND")
    
    # 8. Show logs
    print("\n📊 Step 8: Recent logs...")
    stdout, stderr, code = run_cmd("docker logs crypto-trading-bot 2>&1 | tail -5")
    if stdout:
        for line in stdout.strip().split('\n'):
            print(f"   {line}")
    
    print("\n🎉 DOCKER STARTUP COMPLETE!")
    print("==========================")
    print("📱 Dashboard: http://localhost:8501")
    print("⚡ API: http://localhost:8080")
    print("🐳 Container: crypto-trading-bot")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 