#!/usr/bin/env python3
"""
Debug Bot - ตรวจสอบและแก้ไข error ของ Trading Bot
"""

import os
import sys
import json
import traceback
import importlib.util

def test_imports():
    """ทดสอบการ import modules ที่จำเป็น"""
    print("🔍 ทดสอบการ Import Modules:")
    
    required_modules = [
        'ccxt',
        'pandas',
        'numpy',
        'ta',
        'binance',
        'requests',
        'websocket',
        'flask',
        'plotly',
        'asyncio',
        'aiohttp'
    ]
    
    results = {}
    for module in required_modules:
        try:
            if module == 'binance':
                __import__('binance.client')
                results[module] = "✅"
            else:
                __import__(module)
                results[module] = "✅"
        except ImportError as e:
            results[module] = f"❌ {str(e)}"
        except Exception as e:
            results[module] = f"⚠️ {str(e)}"
    
    for module, status in results.items():
        print(f"  {module}: {status}")
    
    return results

def test_trading_bot_import():
    """ทดสอบการ import trading_bot.py"""
    print("\n🤖 ทดสอบการ Import Trading Bot:")
    
    try:
        # ทดสอบ import trading_bot
        if os.path.exists('trading_bot.py'):
            spec = importlib.util.spec_from_file_location("trading_bot", "trading_bot.py")
            trading_bot = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(trading_bot)
            print("  ✅ trading_bot.py imported successfully")
            
            # ตรวจสอบ class TradingBot
            if hasattr(trading_bot, 'TradingBot'):
                print("  ✅ TradingBot class found")
                
                # ตรวจสอบ methods ที่สำคัญ
                bot_class = trading_bot.TradingBot
                important_methods = [
                    'check_macd_trend_signal',
                    'check_bollinger_rsi_signal',
                    'check_volume_profile_signal',
                    'check_market_structure_signal',
                    'check_order_flow_signal',
                    'calculate_signal_strength',
                    'get_weighted_signal'
                ]
                
                for method in important_methods:
                    if hasattr(bot_class, method):
                        print(f"    ✅ {method}")
                    else:
                        print(f"    ❌ {method} missing")
                        
            else:
                print("  ❌ TradingBot class not found")
                
        else:
            print("  ❌ trading_bot.py not found")
            
    except Exception as e:
        print(f"  ❌ Error importing trading_bot: {e}")
        traceback.print_exc()

def test_backtest_import():
    """ทดสอบการ import backtest.py"""
    print("\n📊 ทดสอบการ Import Backtest:")
    
    try:
        if os.path.exists('backtest.py'):
            spec = importlib.util.spec_from_file_location("backtest", "backtest.py")
            backtest = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(backtest)
            print("  ✅ backtest.py imported successfully")
            
            # ตรวจสอบ functions
            important_functions = [
                'get_all_signals',
                'determine_trade_signal',
                'calculate_position_size',
                'run_backtest'
            ]
            
            for func in important_functions:
                if hasattr(backtest, func):
                    print(f"    ✅ {func}")
                else:
                    print(f"    ❌ {func} missing")
                    
        else:
            print("  ❌ backtest.py not found")
            
    except Exception as e:
        print(f"  ❌ Error importing backtest: {e}")
        traceback.print_exc()

def test_config_files():
    """ทดสอบไฟล์ config"""
    print("\n⚙️ ทดสอบไฟล์ Config:")
    
    configs = {
        'bot_config.json': ['TRADING_PAIRS', 'LEVERAGE', 'MAX_POSITION_SIZE'],
        'strategy_config.json': ['strategy_weights', 'signal_thresholds']
    }
    
    for filename, required_keys in configs.items():
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                print(f"  ✅ {filename}: Valid JSON")
                
                for key in required_keys:
                    if key in config:
                        print(f"    ✅ {key}")
                    else:
                        print(f"    ❌ {key} missing")
                        
            except json.JSONDecodeError as e:
                print(f"  ❌ {filename}: Invalid JSON - {e}")
            except Exception as e:
                print(f"  ❌ {filename}: Error - {e}")
        else:
            print(f"  ❌ {filename}: Not found")

def test_api_connection():
    """ทดสอบการเชื่อมต่อ API (mock test)"""
    print("\n🌐 ทดสอบการเชื่อมต่อ API:")
    
    try:
        import ccxt
        
        # สร้าง exchange object สำหรับทดสอบ
        exchange = ccxt.binance({
            'apiKey': 'test_key',
            'secret': 'test_secret',
            'sandbox': True,  # ใช้ testnet
            'enableRateLimit': True,
        })
        
        print("  ✅ CCXT Binance exchange created")
        
        # ทดสอบ methods ที่จำเป็น
        required_methods = [
            'fetch_ticker',
            'fetch_ohlcv',
            'create_market_buy_order',
            'create_market_sell_order',
            'fetch_balance'
        ]
        
        for method in required_methods:
            if hasattr(exchange, method):
                print(f"    ✅ {method}")
            else:
                print(f"    ❌ {method} missing")
                
    except ImportError:
        print("  ❌ CCXT not installed")
    except Exception as e:
        print(f"  ❌ Error creating exchange: {e}")

def test_data_analysis():
    """ทดสอบการวิเคราะห์ข้อมูล"""
    print("\n📈 ทดสอบการวิเคราะห์ข้อมูล:")
    
    try:
        import pandas as pd
        import numpy as np
        import ta
        
        # สร้างข้อมูลทดสอบ
        dates = pd.date_range('2024-01-01', periods=100, freq='1H')
        prices = np.random.random(100) * 1000 + 50000  # ราคา BTC สมมติ
        volumes = np.random.random(100) * 1000 + 100
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': prices * 1.01,
            'low': prices * 0.99,
            'close': prices,
            'volume': volumes
        })
        
        print("  ✅ Sample data created")
        
        # ทดสอบ indicators
        try:
            # RSI
            df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
            print("    ✅ RSI calculation")
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            print("    ✅ MACD calculation")
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(df['close'])
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            print("    ✅ Bollinger Bands calculation")
            
            # Volume indicators
            df['volume_sma'] = ta.volume.VolumeSMAIndicator(df['close'], df['volume']).volume_sma()
            print("    ✅ Volume SMA calculation")
            
        except Exception as e:
            print(f"    ❌ Indicator calculation error: {e}")
            
    except ImportError as e:
        print(f"  ❌ Missing module: {e}")
    except Exception as e:
        print(f"  ❌ Data analysis error: {e}")

def test_file_permissions():
    """ทดสอบ file permissions"""
    print("\n🔒 ทดสอบ File Permissions:")
    
    important_files = [
        'trading_bot.py',
        'backtest.py',
        'bot_config.json',
        'strategy_config.json',
        'quick_winrate_test.py',
        'win_rate_optimizer.py'
    ]
    
    for filename in important_files:
        if os.path.exists(filename):
            readable = os.access(filename, os.R_OK)
            writable = os.access(filename, os.W_OK)
            executable = os.access(filename, os.X_OK)
            
            status = []
            if readable: status.append("R")
            if writable: status.append("W")
            if executable: status.append("X")
            
            print(f"  {filename}: {''.join(status) if status else 'No permissions'}")
        else:
            print(f"  {filename}: ❌ Not found")

def create_test_summary():
    """สร้างสรุปการทดสอบ"""
    print("\n📋 สร้างไฟล์สรุปการทดสอบ...")
    
    summary = {
        "test_timestamp": str(pd.Timestamp.now()) if 'pd' in globals() else "N/A",
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "files_checked": [f for f in os.listdir('.') if f.endswith('.py')],
        "recommendations": [
            "หากมี Import Error: pip install -r requirements.txt",
            "หากมี Permission Error: chmod +r *.py",
            "หากมี JSON Error: ตรวจสอบ syntax ในไฟล์ config",
            "หาก Terminal ไม่ทำงาน: ใช้ Docker"
        ]
    }
    
    try:
        with open('debug_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        print("  ✅ debug_summary.json created")
    except Exception as e:
        print(f"  ❌ Cannot create summary: {e}")

def main():
    """Main function"""
    print("🔧 TRADING BOT DEBUG TOOL")
    print("=" * 50)
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Directory: {os.getcwd()}")
    print(f"⏰ Time: {pd.Timestamp.now() if 'pd' in sys.modules else 'N/A'}")
    print()
    
    try:
        # ทดสอบทีละขั้นตอน
        test_imports()
        test_config_files()
        test_trading_bot_import()
        test_backtest_import()
        test_api_connection()
        test_data_analysis()
        test_file_permissions()
        create_test_summary()
        
        print("\n🎯 สรุปการแก้ไข:")
        print("1. หากมี ❌ Import Error:")
        print("   pip install -r requirements.txt")
        print("2. หากมี ❌ Config Error:")
        print("   python fix_errors.py")
        print("3. หากมี ❌ Permission Error:")
        print("   chmod +r *.py")
        print("4. หากทุกอย่างเป็น ✅:")
        print("   python quick_start.py")
        
        print("\n🚀 Docker Alternative:")
        print("docker-compose exec trading-bot python debug_bot.py")
        
    except Exception as e:
        print(f"\n❌ Critical Error in debug_bot: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        import pandas as pd
    except ImportError:
        pass
    
    main() 