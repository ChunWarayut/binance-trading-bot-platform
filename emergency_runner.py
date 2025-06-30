#!/usr/bin/env python3
"""Emergency Runner - รันเมื่อ terminal มีปัญหา"""

import subprocess
import sys
import os

def run_command(cmd):
    """รันคำสั่งและแสดงผล"""
    print(f"🚀 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print("✅ Output:")
            print(result.stdout)
        if result.stderr:
            print("❌ Errors:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚨 EMERGENCY RUNNER")
    print("=" * 30)
    
    commands = [
        "python --version",
        "python error_checker.py",
        "python quick_start.py",
        "python quick_winrate_test.py"
    ]
    
    for cmd in commands:
        print(f"\n{'='*30}")
        success = run_command(cmd)
        if not success:
            # ลอง python3
            cmd3 = cmd.replace("python ", "python3 ")
            print(f"\n🔄 Trying with python3...")
            run_command(cmd3)

if __name__ == "__main__":
    main()
