#!/usr/bin/env python3
import sys
import subprocess
import os

print("Python Environment Check")
print("=======================")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path[0]}")

# Try to install packages
packages = ["python-telegram-bot", "fastapi", "uvicorn", "streamlit"]

for package in packages:
    print(f"\nInstalling {package}...")
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"✅ {package} installed successfully")
        else:
            print(f"❌ {package} installation failed: {result.stderr[:100]}")
    except Exception as e:
        print(f"❌ {package} installation error: {e}")

print("\nTesting imports after installation...")

# Test imports
import_results = {}
try:
    import telegram
    print("✅ telegram now works")
    import_results["telegram"] = True
except Exception as e:
    print(f"❌ telegram still fails: {e}")
    import_results["telegram"] = False

try:
    import fastapi
    print("✅ fastapi now works")
    import_results["fastapi"] = True
except Exception as e:
    print(f"❌ fastapi still fails: {e}")
    import_results["fastapi"] = False

try:
    import streamlit
    print("✅ streamlit now works")
    import_results["streamlit"] = True
except Exception as e:
    print(f"❌ streamlit still fails: {e}")
    import_results["streamlit"] = False

# Save results
import json
with open("env_check.json", "w") as f:
    json.dump({
        "python_version": sys.version,
        "python_executable": sys.executable,
        "imports": import_results
    }, f, indent=2)

print("Environment check completed!") 