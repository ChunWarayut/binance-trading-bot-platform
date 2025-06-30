#!/usr/bin/env python3
import os
import subprocess
import time
import requests

def run_command(cmd, check=True):
    """Run shell command and return result"""
    print(f"🔧 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        if result.stderr and check:
            print(f"⚠️ Error: {result.stderr.strip()}")
        return result
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    print("🐳 DOCKER TRADING BOT STARTUP")
    print("============================")
    
    # Stop existing processes
    print("\n🛑 Stopping existing processes...")
    run_command("pkill -9 -f 'python.*main.py'", check=False)
    run_command("pkill -9 -f 'streamlit'", check=False)
    run_command("pkill -9 -f 'uvicorn'", check=False)
    
    # Remove existing container
    print("\n🗑️ Cleaning up existing containers...")
    run_command("docker stop crypto-trading-bot", check=False)
    run_command("docker rm crypto-trading-bot", check=False)
    
    # Build Docker image
    print("\n🔨 Building Docker image...")
    result = run_command("docker build -t crypto-trading-bot .")
    if result and result.returncode != 0:
        print("❌ Docker build failed!")
        return False
    
    # Start container
    print("\n🚀 Starting Docker container...")
    docker_cmd = """docker run -d \
        --name crypto-trading-bot \
        --restart unless-stopped \
        -p 8501:8501 \
        -p 8080:8080 \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd):/app \
        crypto-trading-bot"""
    
    result = run_command(docker_cmd)
    if result and result.returncode != 0:
        print("❌ Docker run failed!")
        return False
    
    # Wait and test
    print("\n⏳ Waiting for services to start...")
    time.sleep(10)
    
    print("\n🧪 Testing services...")
    try:
        # Test API
        response = requests.get("http://localhost:8080/api/bot_status", timeout=5)
        if response.status_code == 200:
            print("✅ API is working!")
        else:
            print(f"⚠️ API returned status {response.status_code}")
    except Exception as e:
        print(f"❌ API test failed: {e}")
    
    print("\n🎉 DOCKER STARTUP COMPLETE!")
    print("📱 Dashboard: http://localhost:8501")
    print("⚡ API: http://localhost:8080")
    print("🐳 Container: crypto-trading-bot")
    
    # Show container status
    run_command("docker ps | grep crypto-trading-bot")
    
    return True

if __name__ == "__main__":
    main() 