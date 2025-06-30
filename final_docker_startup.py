#!/usr/bin/env python3
import subprocess
import time
import requests
import json
import signal
import os
from datetime import datetime

def kill_processes():
    """Forcefully kill all trading processes"""
    print("🛑 Stopping all existing processes...")
    
    # Kill Python processes
    for pattern in ['python.*main.py', 'streamlit', 'uvicorn']:
        try:
            subprocess.run(f"pkill -9 -f '{pattern}'", shell=True, timeout=10)
            time.sleep(1)
        except:
            pass
    
    # Kill by port
    for port in [8080, 8501]:
        try:
            subprocess.run(f"fuser -k {port}/tcp", shell=True, timeout=10)
            time.sleep(1)
        except:
            pass
    
    print("✅ Processes terminated")

def cleanup_docker():
    """Clean up Docker containers"""
    print("🗑️ Cleaning Docker containers...")
    
    try:
        # Stop and remove container
        subprocess.run("docker stop crypto-trading-bot", shell=True, timeout=30)
        subprocess.run("docker rm crypto-trading-bot", shell=True, timeout=30)
        print("✅ Docker cleanup complete")
    except:
        print("⚠️ Docker cleanup had issues (may be normal)")

def build_docker():
    """Build Docker image"""
    print("🔨 Building Docker image...")
    
    try:
        result = subprocess.run("docker build -t crypto-trading-bot .", 
                              shell=True, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("✅ Docker build successful")
            return True
        else:
            print(f"❌ Docker build failed: {result.stderr[-200:]}")
            return False
    except Exception as e:
        print(f"❌ Docker build error: {e}")
        return False

def start_docker():
    """Start Docker container"""
    print("🚀 Starting Docker container...")
    
    docker_cmd = """docker run -d --name crypto-trading-bot --restart unless-stopped \
        -p 8501:8501 -p 8080:8080 -p 5001:5001 \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/active_trades.json:/app/active_trades.json \
        -v $(pwd)/bot_status.json:/app/bot_status.json \
        -v $(pwd)/bot_config.json:/app/bot_config.json \
        -v $(pwd)/trade_history.json:/app/trade_history.json \
        -e TZ=Asia/Bangkok \
        crypto-trading-bot"""
    
    try:
        result = subprocess.run(docker_cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✅ Container started: {result.stdout.strip()[:12]}...")
            return True
        else:
            print(f"❌ Container start failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Container start error: {e}")
        return False

def wait_and_test():
    """Wait for services and test them"""
    print("⏳ Waiting for services to initialize...")
    
    # Wait longer for services to start
    for i in range(20):
        time.sleep(1)
        print(f"   Waiting... {i+1}/20")
    
    print("🧪 Testing services...")
    
    # Test API
    api_ok = False
    try:
        response = requests.get("http://localhost:8080/api/bot_status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Service: Working")
            print(f"   Bot Status: {'RUNNING' if data.get('running') else 'STOPPED'}")
            print(f"   Active Trades: {data.get('active_trades_count', 0)}")
            api_ok = True
        else:
            print(f"⚠️ API Service: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ API Service: {str(e)[:50]}")
    
    # Test Streamlit
    streamlit_ok = False
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print("✅ Streamlit: Working")
            streamlit_ok = True
        else:
            print(f"⚠️ Streamlit: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Streamlit: {str(e)[:50]}")
    
    return api_ok, streamlit_ok

def check_container():
    """Check if container is running"""
    try:
        result = subprocess.run("docker ps | grep crypto-trading-bot", 
                              shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            print("✅ Container: Running")
            print(f"   Status: {result.stdout.strip()}")
            return True
        else:
            print("❌ Container: Not found")
            return False
    except:
        print("❌ Container: Check failed")
        return False

def main():
    """Main startup function"""
    print("🐳 FINAL DOCKER PRODUCTION STARTUP")
    print("==================================")
    
    # Step 1: Kill all processes
    kill_processes()
    time.sleep(3)
    
    # Step 2: Clean Docker
    cleanup_docker()
    time.sleep(2)
    
    # Step 3: Build image
    if not build_docker():
        print("❌ FAILED: Could not build Docker image")
        return False
    
    # Step 4: Start container
    if not start_docker():
        print("❌ FAILED: Could not start Docker container")
        return False
    
    # Step 5: Wait and test
    api_ok, streamlit_ok = wait_and_test()
    
    # Step 6: Check container
    container_ok = check_container()
    
    # Final status
    success_count = sum([api_ok, streamlit_ok, container_ok])
    
    print("\n🎯 FINAL RESULTS:")
    print("================")
    print(f"🐳 Docker Container: {'✅' if container_ok else '❌'}")
    print(f"⚡ API Service: {'✅' if api_ok else '❌'}")
    print(f"📱 Streamlit: {'✅' if streamlit_ok else '❌'}")
    print(f"📊 Success Rate: {success_count}/3 ({success_count/3*100:.0f}%)")
    
    if success_count >= 2:
        print("\n🎉 DOCKER PRODUCTION IS RUNNING!")
        print("================================")
        print("📱 Dashboard: http://localhost:8501")
        print("⚡ API: http://localhost:8080")
        print("🔧 API Docs: http://localhost:8080/docs")
        print("\n🛠️ Management Commands:")
        print("   docker logs crypto-trading-bot")
        print("   docker restart crypto-trading-bot")
        print("   docker stop crypto-trading-bot")
        return True
    else:
        print("\n❌ STARTUP INCOMPLETE")
        print("====================")
        print("Some services are not responding properly.")
        print("Check Docker logs: docker logs crypto-trading-bot")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 