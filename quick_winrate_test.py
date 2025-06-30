#!/usr/bin/env python3
"""
Quick Win Rate Test - ทดสอบ Win Rate แบบเร็ว
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta
from backtest import BacktestEngine

# ปิด logging ที่ไม่จำเป็น
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('binance').setLevel(logging.WARNING)

async def quick_test_winrate(symbols=['BTCUSDT'], days=7, interval='1h'):
    """ทดสอบ Win Rate แบบเร็ว"""
    
    print("⚡ QUICK WIN RATE TEST")
    print("=" * 40)
    print(f"📊 Symbols: {', '.join(symbols)}")
    print(f"📅 Period: {days} days")
    print(f"⏰ Interval: {interval}")
    print()
    
    # คำนวณวันที่
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    results_summary = []
    
    for symbol in symbols:
        try:
            print(f"🧪 Testing {symbol}...")
            
            # สร้าง backtest engine
            engine = BacktestEngine(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                1000
            )
            
            # รัน backtest
            result = await engine.run_backtest(symbol, interval)
            
            if result and result.get('total_trades', 0) > 0:
                win_rate = result.get('win_rate_pct', 0)
                total_trades = result.get('total_trades', 0)
                final_balance = result.get('final_balance', 0)
                total_return = result.get('total_return_pct', 0)
                
                # ประเมิน Win Rate
                if win_rate >= 60:
                    rating = "🏆 ยอดเยี่ยม"
                elif win_rate >= 55:
                    rating = "✅ ดีมาก"
                elif win_rate >= 50:
                    rating = "👍 ดี"
                elif win_rate >= 45:
                    rating = "⚠️ ปานกลาง"
                else:
                    rating = "❌ ต้องปรับปรุง"
                
                results_summary.append({
                    'symbol': symbol,
                    'win_rate': win_rate,
                    'total_trades': total_trades,
                    'final_balance': final_balance,
                    'total_return': total_return,
                    'rating': rating
                })
                
                print(f"  📈 Win Rate: {win_rate:.1f}% {rating}")
                print(f"  📊 Trades: {total_trades}")
                print(f"  💰 Return: {total_return:.2f}%")
                print()
                
            else:
                print(f"  ⚠️ No trades for {symbol}")
                print()
                
        except Exception as e:
            print(f"  ❌ Error testing {symbol}: {e}")
            print()
    
    # สรุปผลลัพธ์
    if results_summary:
        print("📋 SUMMARY RESULTS")
        print("=" * 40)
        
        total_win_rate = sum(r['win_rate'] for r in results_summary) / len(results_summary)
        total_trades_all = sum(r['total_trades'] for r in results_summary)
        avg_return = sum(r['total_return'] for r in results_summary) / len(results_summary)
        
        print(f"📊 Average Win Rate: {total_win_rate:.1f}%")
        print(f"📈 Total Trades: {total_trades_all}")
        print(f"💰 Average Return: {avg_return:.2f}%")
        print()
        
        # ประเมินโดยรวม
        if total_win_rate >= 55:
            print("🎉 ผลลัพธ์ดี! Win Rate อยู่ในเป้าหมาย")
            print("✅ สามารถใช้ config นี้ได้")
        else:
            gap = 55 - total_win_rate
            print(f"📈 ต้องปรับปรุง Win Rate อีก {gap:.1f}%")
            print("🔧 แนะนำใช้ Win Rate Optimizer:")
            print("   python win_rate_optimizer.py")
        
        print()
        
        # แสดงผลลัพธ์แต่ละ symbol
        print("📊 รายละเอียดแต่ละ Symbol:")
        for result in results_summary:
            print(f"  • {result['symbol']}: {result['win_rate']:.1f}% ({result['total_trades']} trades) {result['rating']}")
    
    else:
        print("❌ ไม่มีผลลัพธ์ที่ใช้ได้")
        print("🔧 ลองปรับแต่ง parameters หรือเพิ่มระยะเวลาทดสอบ")

async def main():
    """Main function"""
    print("⚡ เริ่มทดสอบ Win Rate แบบเร็ว...")
    
    # ทดสอบกับ 3 symbols หลัก
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    try:
        await quick_test_winrate(symbols, days=7, interval='1h')
        
        print("\n" + "=" * 40)
        print("🚀 ขั้นตอนต่อไป:")
        print("1. หาก Win Rate ดี (>55%) → รัน full backtest")
        print("2. หาก Win Rate ไม่ดี → ใช้ win_rate_optimizer.py")
        print("3. ทดสอบ paper trading")
        print("4. Deploy bot จริง")
        
    except KeyboardInterrupt:
        print("\n⏹️ การทดสอบถูกยกเลิก")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # ตั้งค่า event loop
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main()) 