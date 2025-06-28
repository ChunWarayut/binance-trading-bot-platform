#!/usr/bin/env python3
"""
สคริปต์สำหรับรันระบบวิเคราะห์เหรียญ
"""

import asyncio
import json
import time
from trading_bot import TradingBot
import config

async def run_coin_analysis():
    """รันระบบวิเคราะห์เหรียญ"""
    print("🪙 เริ่มระบบวิเคราะห์เหรียญ...")
    
    try:
        # สร้าง bot instance
        bot = TradingBot()
        
        # ตั้งค่า bot
        await bot.setup_bot()
        
        print("✅ ตั้งค่า bot สำเร็จ")
        print(f"📊 จำนวนเหรียญที่จะวิเคราะห์: {len(config.TRADING_PAIRS)}")
        print(f"🪙 เหรียญ: {', '.join(config.TRADING_PAIRS)}")
        
        # วิเคราะห์เหรียญครั้งแรก
        print("\n🔄 เริ่มวิเคราะห์เหรียญครั้งแรก...")
        analyses = await bot.analyze_coins()
        
        if analyses:
            print(f"✅ วิเคราะห์เหรียญสำเร็จ {len(analyses)} เหรียญ")
            
            # แสดงผลการวิเคราะห์
            print("\n📊 ผลการวิเคราะห์:")
            for symbol, analysis in analyses.items():
                order_size = analysis['categories']['order_size']
                leverage = analysis['categories']['leverage']
                multiplier = analysis['recommendations']['position_size_multiplier']
                recommended_leverage = analysis['recommendations']['leverage']['recommended']
                
                print(f"   {symbol}: {order_size} size, {leverage} leverage ({multiplier:.1f}x, {recommended_leverage}x)")
            
            # สร้างรายงานสรุป
            print("\n📋 รายงานสรุป:")
            summary = bot.coin_analyzer.get_summary_report(analyses)
            print(summary)
            
            # บันทึกผลการวิเคราะห์
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"coin_analysis_{timestamp}.json"
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(analyses, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 บันทึกผลการวิเคราะห์ลงไฟล์: {filename}")
            
        else:
            print("❌ ไม่สามารถวิเคราะห์เหรียญได้")
        
        print("\n✅ ระบบวิเคราะห์เหรียญเสร็จสิ้น!")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

async def run_continuous_analysis():
    """รันการวิเคราะห์ต่อเนื่อง"""
    print("🔄 เริ่มการวิเคราะห์ต่อเนื่อง...")
    
    try:
        bot = TradingBot()
        await bot.setup_bot()
        
        print("✅ ตั้งค่า bot สำเร็จ")
        print("🔄 เริ่มการวิเคราะห์ต่อเนื่อง (ทุกชั่วโมง)")
        print("กด Ctrl+C เพื่อหยุด")
        
        while True:
            try:
                print(f"\n⏰ {time.strftime('%Y-%m-%d %H:%M:%S')} - เริ่มวิเคราะห์เหรียญ...")
                
                analyses = await bot.analyze_coins()
                
                if analyses:
                    print(f"✅ วิเคราะห์เหรียญสำเร็จ {len(analyses)} เหรียญ")
                    
                    # แสดงสรุป
                    large_orders = [s for s, a in analyses.items() if a['categories']['order_size'] == 'LARGE']
                    high_leverage = [s for s, a in analyses.items() if a['categories']['leverage'] == 'HIGH']
                    
                    print(f"   🔥 Order ใหญ่: {', '.join(large_orders[:3])}")
                    print(f"   🚀 Leverage สูง: {', '.join(high_leverage[:3])}")
                else:
                    print("❌ ไม่สามารถวิเคราะห์เหรียญได้")
                
                # รอ 1 ชั่วโมง
                print("⏳ รอ 1 ชั่วโมง...")
                await asyncio.sleep(3600)  # 1 hour
                
            except KeyboardInterrupt:
                print("\n🛑 หยุดการวิเคราะห์ต่อเนื่อง")
                break
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดในการวิเคราะห์: {e}")
                await asyncio.sleep(300)  # รอ 5 นาทีแล้วลองใหม่
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

def main():
    """ฟังก์ชันหลัก"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # รันการวิเคราะห์ต่อเนื่อง
        asyncio.run(run_continuous_analysis())
    else:
        # รันการวิเคราะห์ครั้งเดียว
        asyncio.run(run_coin_analysis())

if __name__ == "__main__":
    main() 