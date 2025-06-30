#!/usr/bin/env python3
import subprocess
import time
import json

def run_cmd(cmd, description):
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        success = result.returncode == 0
        print(f"   {'✅' if success else '❌'} {description}: {'SUCCESS' if success else 'FAILED'}")
        if not success and result.stderr:
            print(f"   Error: {result.stderr[:100]}")
        if success and result.stdout:
            print(f"   Output: {result.stdout[:100]}")
        return success, result.stdout, result.stderr
    except Exception as e:
        print(f"   ❌ {description}: EXCEPTION - {e}")
        return False, "", str(e)

def main():
    print("🛠️ MANUAL DOCKER FIX")
    print("===================")
    
    # Step 1: Check Docker
    success, stdout, stderr = run_cmd("docker --version", "Check Docker")
    if not success:
        print("❌ Docker not available!")
        return
    
    # Step 2: Build image
    success, stdout, stderr = run_cmd("docker build -t crypto-trading-bot .", "Build Docker image")
    if not success:
        print("❌ Build failed!")
        return
    
    # Step 3: Start with simpler setup
    docker_cmd = """docker run -d --name crypto-trading-bot \
        -p 8501:8501 -p 8080:8080 \
        crypto-trading-bot"""
    
    success, stdout, stderr = run_cmd(docker_cmd, "Start Docker container")
    if not success:
        print("❌ Container start failed!")
        print(f"Error: {stderr}")
        return
    
    print(f"✅ Container started: {stdout.strip()[:12]}")
    
    # Step 4: Wait and check
    print("⏳ Waiting 15 seconds...")
    time.sleep(15)
    
    # Step 5: Check container status
    success, stdout, stderr = run_cmd("docker ps | grep crypto-trading-bot", "Check container")
    if success:
        print("✅ Container is running!")
        print(f"   Status: {stdout.strip()}")
    else:
        print("❌ Container not found!")
    
    # Step 6: Check logs
    success, stdout, stderr = run_cmd("docker logs crypto-trading-bot 2>&1 | tail -10", "Check logs")
    if success:
        print("📋 Recent logs:")
        for line in stdout.strip().split('\n')[-5:]:
            print(f"   {line}")
    
    # Step 7: Test endpoints
    time.sleep(5)
    success, stdout, stderr = run_cmd("curl -s http://localhost:8080/api/bot_status", "Test API")
    if success and stdout:
        print("✅ API responding!")
        print(f"   Response: {stdout[:100]}")
    else:
        print("❌ API not responding")
    
    print("\n🎯 SETUP COMPLETE!")
    print("Dashboard: http://localhost:8501")
    print("API: http://localhost:8080")

if __name__ == "__main__":
    main() 