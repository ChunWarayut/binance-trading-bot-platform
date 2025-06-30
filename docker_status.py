#!/usr/bin/env python3
import subprocess
import time
import json
import os
from datetime import datetime

def execute_and_log(cmd, description):
    """Execute command and log result"""
    print(f"Executing: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        status = {
            "command": cmd,
            "description": description,
            "return_code": result.returncode,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat()
        }
        return status
    except Exception as e:
        return {
            "command": cmd,
            "description": description,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Execute Docker startup sequence"""
    log_file = "docker_startup_log.json"
    results = []
    
    print("🐳 DOCKER PRODUCTION STARTUP")
    print("============================")
    
    # Step 1: Stop existing processes
    print("Step 1: Stopping existing processes...")
    results.append(execute_and_log("pkill -9 -f 'python.*main.py'", "Stop main.py"))
    results.append(execute_and_log("pkill -9 -f 'streamlit'", "Stop streamlit"))
    results.append(execute_and_log("pkill -9 -f 'uvicorn'", "Stop uvicorn"))
    
    # Step 2: Clean Docker containers
    print("Step 2: Cleaning Docker containers...")
    results.append(execute_and_log("docker stop crypto-trading-bot", "Stop container"))
    results.append(execute_and_log("docker rm crypto-trading-bot", "Remove container"))
    
    # Step 3: Build Docker image
    print("Step 3: Building Docker image...")
    build_result = execute_and_log("docker build -t crypto-trading-bot .", "Build image")
    results.append(build_result)
    
    if not build_result["success"]:
        print("❌ Docker build failed!")
        with open(log_file, 'w') as f:
            json.dump(results, f, indent=2)
        return
    
    # Step 4: Start container
    print("Step 4: Starting container...")
    docker_cmd = """docker run -d --name crypto-trading-bot --restart unless-stopped \
        -p 8501:8501 -p 8080:8080 \
        -v $(pwd)/logs:/app/logs -v $(pwd):/app \
        crypto-trading-bot"""
    
    start_result = execute_and_log(docker_cmd, "Start container")
    results.append(start_result)
    
    # Step 5: Wait and check status
    print("Step 5: Waiting for services...")
    time.sleep(15)
    
    results.append(execute_and_log("docker ps | grep crypto-trading-bot", "Check container"))
    results.append(execute_and_log("curl -s http://localhost:8080/api/bot_status", "Test API"))
    results.append(execute_and_log("curl -s http://localhost:8501", "Test Streamlit"))
    
    # Save results
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print("Step 6: Creating summary...")
    successful_steps = sum(1 for r in results if r.get("success", False))
    total_steps = len(results)
    
    summary = {
        "total_steps": total_steps,
        "successful_steps": successful_steps,
        "success_rate": f"{successful_steps/total_steps*100:.1f}%",
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if successful_steps >= total_steps * 0.7 else "PARTIAL" if successful_steps > 0 else "FAILED"
    }
    
    with open("docker_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Docker startup completed: {summary['status']}")
    print(f"Results saved to: {log_file}")
    print(f"Summary saved to: docker_summary.json")
    
    return summary["status"] == "SUCCESS"

if __name__ == "__main__":
    main() 