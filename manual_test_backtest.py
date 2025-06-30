#!/usr/bin/env python3
"""
Manual Backtest Test - ทดสอบ backtest แบบ manual
รันด้วยคำสั่ง: python manual_test_backtest.py
"""

print("🧪 เริ่มทดสอบ Enhanced Backtest Engine")
print("=" * 50)

# Test 1: Import modules
print("📦 ทดสอบการ import modules...")
try:
    from backtest import BacktestEngine
    from trading_bot import TradingBot
    print("✅ Import modules สำเร็จ")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)

# Test 2: Create BacktestEngine
print("\n🏗️ ทดสอบการสร้าง BacktestEngine...")
try:
    engine = BacktestEngine('2024-01-01', '2024-01-03', 1000)
    print("✅ สร้าง BacktestEngine สำเร็จ")
    print(f"📅 Period: {engine.start_date.date()} to {engine.end_date.date()}")
    print(f"💰 Initial balance: ${engine.initial_balance:,.2f}")
except Exception as e:
    print(f"❌ Error creating BacktestEngine: {e}")
    exit(1)

# Test 3: Test signal functions with dummy data
print("\n📊 ทดสอบ Signal Functions...")
try:
    import pandas as pd
    import numpy as np
    
    # สร้างข้อมูลทดสอบ 100 candles
    np.random.seed(42)  # ให้ผลลัพธ์เหมือนเดิม
    dates = pd.date_range('2024-01-01', periods=100, freq='1H')
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': 45000 + np.random.normal(0, 1000, 100).cumsum(),
        'high': 45000 + np.random.normal(500, 1000, 100).cumsum(),
        'low': 45000 + np.random.normal(-500, 1000, 100).cumsum(),
        'close': 45000 + np.random.normal(0, 1000, 100).cumsum(),
        'volume': np.random.uniform(100, 1000, 100)
    })
    
    # ปรับให้ high >= max(open, close) และ low <= min(open, close)
    df['high'] = np.maximum(df['high'], np.maximum(df['open'], df['close']))
    df['low'] = np.minimum(df['low'], np.minimum(df['open'], df['close']))
    
    print(f"📈 สร้างข้อมูลทดสอบ {len(df)} candles")
    print(f"💹 Price range: ${df['low'].min():,.0f} - ${df['high'].max():,.0f}")
    
    # คำนวณ indicators
    df = engine.calculate_indicators(df)
    print("✅ คำนวณ indicators สำเร็จ")
    
    # ทดสอบ signals
    current_price = float(df['close'].iloc[-1])
    signals = engine.get_all_signals(df, current_price)
    
    print("✅ Signal functions ทำงานได้")
    print(f"📊 Total signals: {len(signals)}")
    
    # นับ signals ที่ active
    buy_signals = sum(1 for s in signals.values() if s == "BUY")
    sell_signals = sum(1 for s in signals.values() if s == "SELL")
    none_signals = sum(1 for s in signals.values() if s is None)
    
    print(f"🟢 BUY signals: {buy_signals}")
    print(f"🔴 SELL signals: {sell_signals}")
    print(f"⚪ None signals: {none_signals}")
    
    # แสดง active signals
    active_signals = {k: v for k, v in signals.items() if v is not None}
    if active_signals:
        print("🎯 Active signals:")
        for name, signal in active_signals.items():
            print(f"  • {name}: {signal}")
    else:
        print("⚠️ ไม่มี active signals")
    
    # ทดสอบ determine_trade_signal
    final_signal, strategy = engine.determine_trade_signal(signals)
    print(f"🎯 Final signal: {final_signal} ({strategy})")
    
except Exception as e:
    print(f"❌ Signal test error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n🎉 การทดสอบพื้นฐานสำเร็จทั้งหมด!")
print("✅ Backtest engine พร้อมใช้งาน")

print("\n" + "=" * 50)
print("📋 วิธีใช้งานต่อ:")
print("1. รัน full backtest: python backtest.py")
print("2. ทดสอบ strategies: python test_enhanced_strategies.py")
print("3. รัน bot จริง: python main.py")
print("4. ดู web UI: python web_ui.py")
print("=" * 50) 