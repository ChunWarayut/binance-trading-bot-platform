#!/usr/bin/env python3
"""Quick Start - เริ่มต้นใช้งานเร็ว"""

import os

print("🚀 TRADING BOT QUICK START")
print("=" * 40)

# ตรวจสอบไฟล์
files = ['quick_winrate_test.py', 'win_rate_optimizer.py', 'manual_test_backtest.py']
print("📁 ตรวจสอบไฟล์:")
for f in files:
    status = "✅" if os.path.exists(f) else "❌"
    print(f"  {status} {f}")

print("\n📋 คำสั่งสำหรับทดสอบ:")
print("1. python quick_winrate_test.py      # ทดสอบ Win Rate")
print("2. python win_rate_optimizer.py      # ปรับปรุง Win Rate")
print("3. python manual_test_backtest.py    # ทดสอบพื้นฐาน")
print("4. python backtest.py                # Full Backtest")
print("5. python performance_analyzer.py    # วิเคราะห์ผลลัพธ์")

print("\n🎯 เป้าหมาย: Win Rate > 55%")
print("📖 อ่านเพิ่มเติม: MANUAL_TESTING_STEPS.md")
print("🐳 Docker: docker-compose exec trading-bot python [script]") 