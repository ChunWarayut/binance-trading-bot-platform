#!/usr/bin/env python3
"""
Error Checker - ตรวจสอบและแก้ไข error ทั่วไป
"""

import os
import sys
import ast
import json
import importlib.util

def check_python_syntax(filename):
    """ตรวจสอบ syntax ของไฟล์ Python"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        return True, "✅ Syntax ถูกต้อง"
    except SyntaxError as e:
        return False, f"❌ Syntax Error: {e}"
    except Exception as e:
        return False, f"❌ Error: {e}"

def check_imports(filename):
    """ตรวจสอบ imports ในไฟล์"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        missing_modules = []
        for module in imports:
            try:
                if importlib.util.find_spec(module) is None:
                    missing_modules.append(module)
            except:
                missing_modules.append(module)
        
        if missing_modules:
            return False, f"❌ Missing modules: {missing_modules}"
        else:
            return True, "✅ All imports available"
            
    except Exception as e:
        return False, f"❌ Error checking imports: {e}"

def check_json_files():
    """ตรวจสอบไฟล์ JSON"""
    json_files = ['bot_config.json', 'strategy_config.json']
    results = {}
    
    for filename in json_files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    json.load(f)
                results[filename] = "✅ Valid JSON"
            except json.JSONDecodeError as e:
                results[filename] = f"❌ Invalid JSON: {e}"
            except Exception as e:
                results[filename] = f"❌ Error: {e}"
        else:
            results[filename] = "⚠️ File not found"
    
    return results

def check_permissions():
    """ตรวจสอบ permissions ของไฟล์"""
    python_files = [f for f in os.listdir('.') if f.endswith('.py')]
    results = {}
    
    for filename in python_files:
        if os.path.exists(filename):
            if os.access(filename, os.R_OK):
                results[filename] = "✅ Readable"
            else:
                results[filename] = "❌ Not readable"
        else:
            results[filename] = "⚠️ File not found"
    
    return results

def fix_common_issues():
    """แก้ไขปัญหาทั่วไป"""
    fixes = []
    
    # ตรวจสอบและสร้าง __pycache__ directory
    if not os.path.exists('__pycache__'):
        try:
            os.makedirs('__pycache__')
            fixes.append("✅ Created __pycache__ directory")
        except:
            fixes.append("❌ Cannot create __pycache__ directory")
    
    # ตรวจสอบและสร้าง logs directory
    if not os.path.exists('logs'):
        try:
            os.makedirs('logs')
            fixes.append("✅ Created logs directory")
        except:
            fixes.append("❌ Cannot create logs directory")
    
    # ตรวจสอบ requirements.txt
    if os.path.exists('requirements.txt'):
        fixes.append("✅ requirements.txt exists")
    else:
        fixes.append("⚠️ requirements.txt not found")
    
    return fixes

def main():
    """Main function"""
    print("🔍 ERROR CHECKER & DIAGNOSTIC TOOL")
    print("=" * 50)
    
    # ตรวจสอบ Python version
    print(f"🐍 Python Version: {sys.version}")
    print(f"📁 Current Directory: {os.getcwd()}")
    print()
    
    # ตรวจสอบไฟล์หลัก
    main_files = [
        'quick_winrate_test.py',
        'win_rate_optimizer.py',
        'performance_analyzer.py',
        'manual_test_backtest.py',
        'backtest.py',
        'trading_bot.py'
    ]
    
    print("📋 ตรวจสอบไฟล์หลัก:")
    for filename in main_files:
        if os.path.exists(filename):
            # ตรวจสอบ syntax
            syntax_ok, syntax_msg = check_python_syntax(filename)
            print(f"  {filename}: {syntax_msg}")
            
            # ตรวจสอบ imports (เฉพาะไฟล์ที่ syntax ถูกต้อง)
            if syntax_ok:
                import_ok, import_msg = check_imports(filename)
                if not import_ok:
                    print(f"    {import_msg}")
        else:
            print(f"  {filename}: ❌ ไม่พบไฟล์")
    
    print()
    
    # ตรวจสอบไฟล์ JSON
    print("📄 ตรวจสอบไฟล์ JSON:")
    json_results = check_json_files()
    for filename, result in json_results.items():
        print(f"  {filename}: {result}")
    
    print()
    
    # ตรวจสอบ permissions
    print("🔒 ตรวจสอบ Permissions:")
    perm_results = check_permissions()
    for filename, result in perm_results.items():
        if "❌" in result:
            print(f"  {filename}: {result}")
    
    print()
    
    # แก้ไขปัญหาทั่วไป
    print("🔧 แก้ไขปัญหาทั่วไป:")
    fixes = fix_common_issues()
    for fix in fixes:
        print(f"  {fix}")
    
    print()
    
    # คำแนะนำ
    print("💡 คำแนะนำการแก้ไข:")
    print("1. ถ้ามี Syntax Error → แก้ไขโค้ดในไฟล์นั้น")
    print("2. ถ้ามี Import Error → รัน: pip install -r requirements.txt")
    print("3. ถ้ามี JSON Error → ตรวจสอบ syntax ในไฟล์ .json")
    print("4. ถ้ามี Permission Error → รัน: chmod +r *.py")
    print("5. ถ้า terminal ไม่ทำงาน → ใช้ Docker: docker-compose exec trading-bot python [script]")
    
    print()
    print("🚀 หลังจากแก้ไขแล้ว ลองรัน:")
    print("  python quick_start.py")
    print("  หรือ python3 quick_start.py")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error in error checker: {e}")
        import traceback
        traceback.print_exc() 