#!/usr/bin/env python3
"""
Fix Errors - แก้ไข error อัตโนมัติ
"""

import os
import sys
import json
import shutil
from datetime import datetime

def backup_file(filename):
    """สำรองไฟล์ก่อนแก้ไข"""
    if os.path.exists(filename):
        backup_name = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filename, backup_name)
        return backup_name
    return None

def fix_json_syntax():
    """แก้ไข JSON syntax errors"""
    json_files = ['bot_config.json', 'strategy_config.json']
    fixes = []
    
    for filename in json_files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # ลองโหลด JSON
                json.loads(content)
                fixes.append(f"✅ {filename}: JSON valid")
                
            except json.JSONDecodeError as e:
                fixes.append(f"❌ {filename}: JSON Error - {e}")
                
                # พยายามแก้ไขปัญหาทั่วไป
                try:
                    # แก้ไข trailing comma
                    fixed_content = content.replace(',}', '}').replace(',]', ']')
                    
                    # ทดสอบ JSON ที่แก้ไขแล้ว
                    json.loads(fixed_content)
                    
                    # สำรองไฟล์เดิม
                    backup_file(filename)
                    
                    # เขียนไฟล์ใหม่
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    fixes.append(f"✅ {filename}: Fixed trailing comma")
                    
                except:
                    fixes.append(f"❌ {filename}: Cannot auto-fix")
            
            except Exception as e:
                fixes.append(f"❌ {filename}: Error - {e}")
        else:
            fixes.append(f"⚠️ {filename}: File not found")
    
    return fixes

def fix_import_errors():
    """แก้ไข import errors"""
    fixes = []
    
    # ตรวจสอบ requirements.txt
    if not os.path.exists('requirements.txt'):
        # สร้าง requirements.txt พื้นฐาน
        requirements = [
            "ccxt>=4.0.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "ta>=0.10.2",
            "python-binance>=1.0.17",
            "requests>=2.31.0",
            "websocket-client>=1.6.0",
            "python-dotenv>=1.0.0",
            "flask>=2.3.0",
            "plotly>=5.15.0",
            "asyncio",
            "aiohttp>=3.8.0"
        ]
        
        with open('requirements.txt', 'w') as f:
            f.write('\n'.join(requirements))
        
        fixes.append("✅ Created requirements.txt")
    else:
        fixes.append("✅ requirements.txt exists")
    
    return fixes

def fix_directory_structure():
    """แก้ไข directory structure"""
    fixes = []
    
    # สร้าง directories ที่จำเป็น
    required_dirs = ['logs', '__pycache__']
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name)
                fixes.append(f"✅ Created directory: {dir_name}")
            except:
                fixes.append(f"❌ Cannot create directory: {dir_name}")
        else:
            fixes.append(f"✅ Directory exists: {dir_name}")
    
    return fixes

def fix_file_permissions():
    """แก้ไข file permissions"""
    fixes = []
    
    # ตรวจสอบไฟล์ Python
    python_files = [f for f in os.listdir('.') if f.endswith('.py')]
    
    for filename in python_files:
        try:
            if not os.access(filename, os.R_OK):
                os.chmod(filename, 0o644)
                fixes.append(f"✅ Fixed permissions: {filename}")
            else:
                # fixes.append(f"✅ Permissions OK: {filename}")
                pass
        except:
            fixes.append(f"❌ Cannot fix permissions: {filename}")
    
    if not fixes:
        fixes.append("✅ All file permissions OK")
    
    return fixes

def fix_config_files():
    """แก้ไขไฟล์ config"""
    fixes = []
    
    # ตรวจสอบ bot_config.json
    if not os.path.exists('bot_config.json'):
        # สร้าง config พื้นฐาน
        default_config = {
            "api_key": "your_api_key_here",
            "api_secret": "your_api_secret_here",
            "testnet": True,
            "leverage": 3,
            "position_size_percent": 20,
            "stop_loss_percent": 5,
            "take_profit_percent": 10,
            "max_daily_trades": 50,
            "max_daily_loss_percent": 5,
            "trading_pairs": ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        }
        
        with open('bot_config.json', 'w') as f:
            json.dump(default_config, f, indent=2)
        
        fixes.append("✅ Created default bot_config.json")
    
    # ตรวจสอบ strategy_config.json
    if not os.path.exists('strategy_config.json'):
        # สร้าง strategy config พื้นฐาน
        default_strategy = {
            "strategy_weights": {
                "MACD Trend": 0.15,
                "Bollinger RSI": 0.12,
                "Parabolic SAR ADX": 0.14,
                "Volume Profile": 0.13,
                "Market Structure": 0.11,
                "Order Flow": 0.11,
                "Stochastic Williams": 0.10,
                "Chaikin Money Flow MACD": 0.10,
                "Momentum": 0.08
            },
            "confidence_threshold": 0.4,
            "strength_threshold": 50,
            "min_signals_required": 3
        }
        
        with open('strategy_config.json', 'w') as f:
            json.dump(default_strategy, f, indent=2)
        
        fixes.append("✅ Created default strategy_config.json")
    
    return fixes

def fix_common_python_errors():
    """แก้ไข Python errors ทั่วไป"""
    fixes = []
    
    # ตรวจสอบไฟล์ที่มี syntax errors
    problem_files = []
    python_files = [f for f in os.listdir('.') if f.endswith('.py')]
    
    for filename in python_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # ตรวจสอบ syntax
            compile(content, filename, 'exec')
            
        except SyntaxError as e:
            problem_files.append((filename, str(e)))
        except Exception:
            pass
    
    if problem_files:
        fixes.append("❌ Syntax errors found:")
        for filename, error in problem_files:
            fixes.append(f"  {filename}: {error}")
    else:
        fixes.append("✅ No syntax errors found")
    
    return fixes

def create_emergency_runner():
    """สร้าง emergency runner สำหรับกรณี terminal ไม่ทำงาน"""
    content = '''#!/usr/bin/env python3
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
        print(f"\\n{'='*30}")
        success = run_command(cmd)
        if not success:
            # ลอง python3
            cmd3 = cmd.replace("python ", "python3 ")
            print(f"\\n🔄 Trying with python3...")
            run_command(cmd3)

if __name__ == "__main__":
    main()
'''
    
    with open('emergency_runner.py', 'w') as f:
        f.write(content)
    
    return "✅ Created emergency_runner.py"

def main():
    """Main function"""
    print("🔧 ERROR FIXER - แก้ไข error อัตโนมัติ")
    print("=" * 50)
    print(f"📁 Working Directory: {os.getcwd()}")
    print(f"🐍 Python Version: {sys.version}")
    print()
    
    all_fixes = []
    
    # 1. แก้ไข JSON files
    print("1️⃣ แก้ไข JSON Files:")
    json_fixes = fix_json_syntax()
    all_fixes.extend(json_fixes)
    for fix in json_fixes:
        print(f"  {fix}")
    print()
    
    # 2. แก้ไข Import errors
    print("2️⃣ แก้ไข Import Errors:")
    import_fixes = fix_import_errors()
    all_fixes.extend(import_fixes)
    for fix in import_fixes:
        print(f"  {fix}")
    print()
    
    # 3. แก้ไข Directory structure
    print("3️⃣ แก้ไข Directory Structure:")
    dir_fixes = fix_directory_structure()
    all_fixes.extend(dir_fixes)
    for fix in dir_fixes:
        print(f"  {fix}")
    print()
    
    # 4. แก้ไข File permissions
    print("4️⃣ แก้ไข File Permissions:")
    perm_fixes = fix_file_permissions()
    all_fixes.extend(perm_fixes)
    for fix in perm_fixes:
        print(f"  {fix}")
    print()
    
    # 5. แก้ไข Config files
    print("5️⃣ แก้ไข Config Files:")
    config_fixes = fix_config_files()
    all_fixes.extend(config_fixes)
    for fix in config_fixes:
        print(f"  {fix}")
    print()
    
    # 6. ตรวจสอบ Python syntax
    print("6️⃣ ตรวจสอบ Python Syntax:")
    syntax_fixes = fix_common_python_errors()
    all_fixes.extend(syntax_fixes)
    for fix in syntax_fixes:
        print(f"  {fix}")
    print()
    
    # 7. สร้าง Emergency runner
    print("7️⃣ สร้าง Emergency Tools:")
    emergency_fix = create_emergency_runner()
    all_fixes.append(emergency_fix)
    print(f"  {emergency_fix}")
    print()
    
    # สรุปผล
    success_count = len([f for f in all_fixes if "✅" in f])
    error_count = len([f for f in all_fixes if "❌" in f])
    warning_count = len([f for f in all_fixes if "⚠️" in f])
    
    print("📊 สรุปผลการแก้ไข:")
    print(f"  ✅ สำเร็จ: {success_count}")
    print(f"  ❌ ล้มเหลว: {error_count}")
    print(f"  ⚠️ คำเตือน: {warning_count}")
    print()
    
    print("🚀 ขั้นตอนต่อไป:")
    print("1. รัน: python error_checker.py")
    print("2. รัน: python quick_start.py")
    print("3. หาก terminal ไม่ทำงาน: python emergency_runner.py")
    print("4. หาก Python ไม่ทำงาน: ใช้ Docker")
    print("   docker-compose exec trading-bot python error_checker.py")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error in fix_errors: {e}")
        import traceback
        traceback.print_exc() 