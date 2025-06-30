#!/usr/bin/env python3
"""
Simple Backtest Test - ทดสอบ backtest engine แบบง่าย
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from backtest import BacktestEngine
import sys
import os

# ปิด logging ที่ไม่จำเป็น
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('binance').setLevel(logging.WARNING)

def test_import():
    """ทดสอบการ import modules"""
    try:
        from backtest import BacktestEngine
        from trading_bot import TradingBot
        print("✅ Import modules สำเร็จ")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_backtest_creation():
    """ทดสอบการสร้าง BacktestEngine"""
    try:
        engine = BacktestEngine('2024-01-01', '2024-01-05', 1000)
        print("✅ สร้าง BacktestEngine สำเร็จ")
        return engine
    except Exception as e:
        print(f"❌ Error creating BacktestEngine: {e}")
        return None

async def test_signal_functions(engine):
    """ทดสอบ signal functions"""
    try:
        # สร้าง dummy DataFrame
        import pandas as pd
        import numpy as np
        
        # สร้างข้อมูลทดสอบ
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': np.random.uniform(40000, 50000, 100),
            'high': np.random.uniform(45000, 55000, 100),
            'low': np.random.uniform(35000, 45000, 100),
            'close': np.random.uniform(40000, 50000, 100),
            'volume': np.random.uniform(100, 1000, 100)
        })
        
        # คำนวณ indicators
        df = engine.calculate_indicators(df)
        
        # ทดสอบ signals
        signals = engine.get_all_signals(df, 45000.0)
        
        print("✅ Signal functions ทำงานได้")
        print(f"📊 Signals ที่ได้: {len([s for s in signals.values() if s is not None])}/{len(signals)}")
        
        # แสดง signals ที่ได้
        active_signals = {k: v for k, v in signals.items() if v is not None}
        if active_signals:
            print("🎯 Active signals:")
            for name, signal in active_signals.items():
                print(f"  • {name}: {signal}")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mini_backtest(engine):
    """ทดสอบ backtest แบบสั้น"""
    try:
        print("🧪 เริ่มทดสอบ mini backtest...")
        
        # ทดสอบกับข้อมูลสั้นๆ
        result = await engine.run_backtest('BTCUSDT', '1h')
        
        if result:
            print("✅ Mini backtest สำเร็จ!")
            print(f"📈 Total trades: {result.get('total_trades', 0)}")
            print(f"💰 Final balance: ${result.get('final_balance', 0):,.2f}")
            print(f"📊 Return: {result.get('total_return_pct', 0):.2f}%")
            return True
        else:
            print("⚠️ Backtest ไม่มีผลลัพธ์")
            return False
            
    except Exception as e:
        print(f"❌ Mini backtest error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("🧪 เริ่มทดสอบ Enhanced Backtest Engine")
    print("=" * 50)
    
    # Test 1: Import
    if not test_import():
        return
    
    # Test 2: Create engine
    engine = test_backtest_creation()
    if not engine:
        return
    
    # Test 3: Signal functions
    print("\n📊 ทดสอบ Signal Functions...")
    if not await test_signal_functions(engine):
        return
    
    # Test 4: Mini backtest
    print("\n🚀 ทดสอบ Mini Backtest...")
    if await test_mini_backtest(engine):
        print("\n🎉 การทดสอบสำเร็จทั้งหมด!")
        print("✅ Backtest engine พร้อมใช้งาน")
    else:
        print("\n⚠️ การทดสอบมีปัญหาบางส่วน")

if __name__ == "__main__":
    # ตั้งค่า event loop สำหรับ Windows
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ การทดสอบถูกยกเลิก")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc() 