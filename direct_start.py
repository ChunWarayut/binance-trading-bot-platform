#!/usr/bin/env python3
import subprocess
import time
import os
import signal
import sys

def start_services():
    print("🚀 Starting Crypto Trading Bot Services")
    print("======================================")
    
    # Kill existing processes
    print("1. Cleaning up existing processes...")
    os.system("pkill -f 'python.*main.py' 2>/dev/null || true")
    os.system("pkill -f 'streamlit' 2>/dev/null || true") 
    os.system("pkill -f 'uvicorn' 2>/dev/null || true")
    os.system("pkill -f 'realtime_api' 2>/dev/null || true")
    time.sleep(3)
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Start main bot
    print("2. Starting main trading bot...")
    main_process = subprocess.Popen([
        "python3", "main.py"
    ], stdout=open("logs/main.log", "w"), stderr=subprocess.STDOUT)
    time.sleep(5)
    
    # Start API server
    print("3. Starting API server...")
    api_process = subprocess.Popen([
        "python3", "realtime_api.py"
    ], stdout=open("logs/api.log", "w"), stderr=subprocess.STDOUT)
    time.sleep(5)
    
    # Start Streamlit dashboard
    print("4. Starting Streamlit dashboard...")
    streamlit_process = subprocess.Popen([
        "streamlit", "run", "enhanced_web_ui.py", 
        "--server.port", "8501",
        "--server.headless", "true",
        "--server.enableCORS", "false"
    ], stdout=open("logs/streamlit.log", "w"), stderr=subprocess.STDOUT)
    
    print("5. Waiting for services to start...")
    time.sleep(15)
    
    # Check if processes are running
    processes = [
        ("Main Bot", main_process),
        ("API Server", api_process), 
        ("Streamlit", streamlit_process)
    ]
    
    running_count = 0
    for name, process in processes:
        if process.poll() is None:
            print(f"✅ {name} is running (PID: {process.pid})")
            running_count += 1
        else:
            print(f"❌ {name} failed to start")
    
    if running_count == 3:
        print("\n🎉 All services started successfully!")
        print("📊 Dashboard: http://localhost:8501")
        print("🔌 API: http://localhost:8080/api/")
        print("📝 Logs available in logs/ directory")
        
        # Save process info
        with open("running_processes.txt", "w") as f:
            for name, process in processes:
                if process.poll() is None:
                    f.write(f"{name}: PID {process.pid}\n")
        
        print("\nServices are running in background. Use check_services.py to verify connectivity.")
        return processes
    else:
        print(f"\n⚠️  Only {running_count}/3 services started successfully")
        return processes

def signal_handler(sig, frame):
    print("\n🛑 Stopping services...")
    os.system("pkill -f 'python.*main.py' 2>/dev/null || true")
    os.system("pkill -f 'streamlit' 2>/dev/null || true")
    os.system("pkill -f 'realtime_api' 2>/dev/null || true")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    processes = start_services()
    
    # Save results to file for checking
    with open("startup_results.json", "w") as f:
        import json
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processes_started": len([p for name, p in processes if p.poll() is None]),
            "total_processes": len(processes),
            "success": len([p for name, p in processes if p.poll() is None]) == len(processes)
        }
        json.dump(results, f, indent=2) 