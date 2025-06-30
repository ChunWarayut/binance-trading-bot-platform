#!/usr/bin/env python3
"""
Startup script for Real-time Trading Bot Dashboard
"""

import subprocess
import time
import sys
import signal
import os
from datetime import datetime

def log_message(message):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def start_service(name, command, port=None):
    """Start a service and return the process"""
    try:
        log_message(f"🚀 Starting {name}...")
        if port:
            log_message(f"   → Will be available at http://localhost:{port}")
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # Give it time to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            log_message(f"✅ {name} started successfully (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            log_message(f"❌ {name} failed to start:")
            if stderr:
                log_message(f"   Error: {stderr.decode()}")
            return None
            
    except Exception as e:
        log_message(f"❌ Error starting {name}: {e}")
        return None

def cleanup(processes):
    """Clean up processes on exit"""
    log_message("🛑 Shutting down services...")
    
    for name, process in processes.items():
        if process and process.poll() is None:
            try:
                # Kill process group to ensure child processes are also terminated
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                log_message(f"✅ {name} stopped")
            except Exception as e:
                log_message(f"⚠️  Error stopping {name}: {e}")

def main():
    """Main function to start all services"""
    print("=" * 60)
    print("🚀 CRYPTO TRADING BOT - REAL-TIME DASHBOARD")
    print("=" * 60)
    
    processes = {}
    
    try:
        # Start Real-time API Server
        processes['Real-time API'] = start_service(
            "Real-time API Server",
            "python3 realtime_api.py",
            8080
        )
        
        # Start Enhanced Web UI
        processes['Streamlit Dashboard'] = start_service(
            "Enhanced Web Dashboard", 
            "streamlit run enhanced_web_ui.py --server.port 8501 --server.address 0.0.0.0 --server.headless true",
            8501
        )
        
        # Check which services started successfully
        running_services = [name for name, proc in processes.items() if proc and proc.poll() is None]
        
        if not running_services:
            log_message("❌ No services started successfully!")
            return 1
        
        print("\n" + "=" * 60)
        print("✅ DASHBOARD READY!")
        print("=" * 60)
        
        # Display access URLs
        print("🌐 ACCESS URLS:")
        if processes.get('Real-time API'):
            print("   • Real-time API: http://localhost:8080")
            print("   • Simple Dashboard: http://localhost:8080/dashboard")
            print("   • API Health: http://localhost:8080/health")
        
        if processes.get('Streamlit Dashboard'):
            print("   • Enhanced Dashboard: http://localhost:8501")
        
        print("\n📊 AVAILABLE FEATURES:")
        print("   • Real-time WebSocket updates")
        print("   • Live trading status")
        print("   • Performance charts")
        print("   • Bot controls (Start/Stop/Restart)")
        print("   • Configuration management")
        print("   • Real-time logs")
        
        print("\n💡 USAGE:")
        print("   • Open browser to http://localhost:8501 for best experience")
        print("   • Press Ctrl+C to stop all services")
        
        print("\n" + "=" * 60)
        
        # Keep services running
        log_message("📡 Services running... Press Ctrl+C to stop")
        
        while True:
            # Check if processes are still alive
            alive_services = []
            for name, proc in processes.items():
                if proc and proc.poll() is None:
                    alive_services.append(name)
                else:
                    log_message(f"⚠️  {name} has stopped")
            
            if not alive_services:
                log_message("❌ All services have stopped!")
                break
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        log_message("🛑 Received shutdown signal...")
    except Exception as e:
        log_message(f"❌ Unexpected error: {e}")
    finally:
        cleanup(processes)
        log_message("👋 Dashboard shutdown complete")
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 