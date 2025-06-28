#!/usr/bin/env python3
"""
สคริปต์ทดสอบระบบวิเคราะห์เหรียญ
"""

import asyncio
import json
from trading_bot import TradingBot
from coin_analysis import CoinAnalyzer
from binance.client import Client
import config

async def test_coin_analysis():
    """ทดสอบระบบวิเคราะห์เหรียญ"""
    print("🪙 เริ่มทดสอบระบบวิเคราะห์เหรียญ...")
    
    try:
        # สร้าง bot instance
        bot = TradingBot()
        
        # ทดสอบการวิเคราะห์เหรียญทั้งหมด
        print("\n📊 ทดสอบการวิเคราะห์เหรียญทั้งหมด...")
        analyses = await bot.analyze_coins()
        
        if analyses:
            print(f"✅ วิเคราะห์เหรียญสำเร็จ {len(analyses)} เหรียญ")
            
            # แสดงผลการวิเคราะห์
            for symbol, analysis in analyses.items():
                print(f"\n🔍 {symbol}:")
                print(f"   ราคาปัจจุบัน: {analysis['current_price']:.2f} USDT")
                print(f"   ขนาด Order: {analysis['categories']['order_size']}")
                print(f"   Leverage: {analysis['categories']['leverage']}")
                print(f"   Position Size Multiplier: {analysis['recommendations']['position_size_multiplier']}")
                print(f"   Recommended Leverage: {analysis['recommendations']['leverage']['recommended']}x")
                print(f"   ความผันผวน: {analysis['metrics']['volatility']:.2f}%")
                print(f"   สภาพคล่อง: {analysis['metrics']['liquidity_score']:.1f}/100")
                print(f"   ปริมาณเฉลี่ย: {analysis['metrics']['volume_profile']['avg_volume']:,.0f}")
                
                # แสดงหมายเหตุ
                notes = analysis['recommendations']['notes']
                if notes:
                    print("   📝 หมายเหตุ:")
                    for note in notes[:2]:  # แสดงแค่ 2 หมายเหตุแรก
                        print(f"      {note}")
        else:
            print("❌ ไม่สามารถวิเคราะห์เหรียญได้")
        
        # ทดสอบการวิเคราะห์เหรียญเฉพาะ
        print("\n🎯 ทดสอบการวิเคราะห์เหรียญเฉพาะ...")
        test_symbol = "BTCUSDT"
        if test_symbol in config.TRADING_PAIRS:
            recommendation = await bot.get_coin_recommendations(test_symbol)
            if recommendation:
                print(f"✅ วิเคราะห์ {test_symbol} สำเร็จ")
                print(f"   ขนาด Order: {recommendation['categories']['order_size']}")
                print(f"   Leverage: {recommendation['categories']['leverage']}")
            else:
                print(f"❌ ไม่สามารถวิเคราะห์ {test_symbol} ได้")
        
        # สร้างรายงานสรุป
        print("\n📋 สร้างรายงานสรุป...")
        if analyses:
            summary = bot.coin_analyzer.get_summary_report(analyses)
            print("✅ รายงานสรุป:")
            print(summary)
        
        # ทดสอบการคำนวณ position size
        print("\n💰 ทดสอบการคำนวณ position size...")
        test_symbol = "ETHUSDT"
        if test_symbol in config.TRADING_PAIRS:
            try:
                # ดึงราคาปัจจุบัน
                ticker = await bot.safe_api_call(bot.client.futures_symbol_ticker, symbol=test_symbol)
                current_price = float(ticker['price'])
                
                # คำนวณ position size
                quantity = await bot.calculate_position_size(test_symbol, current_price)
                if quantity:
                    print(f"✅ คำนวณ position size สำหรับ {test_symbol} สำเร็จ")
                    print(f"   ราคา: {current_price:.2f} USDT")
                    print(f"   จำนวน: {quantity}")
                    print(f"   มูลค่า: {quantity * current_price:.2f} USDT")
                else:
                    print(f"❌ ไม่สามารถคำนวณ position size สำหรับ {test_symbol} ได้")
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดในการคำนวณ position size: {e}")
        
        print("\n✅ การทดสอบเสร็จสิ้น!")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการทดสอบ: {e}")

async def test_individual_metrics():
    """ทดสอบการคำนวณเมตริกแต่ละตัว"""
    print("\n🔬 ทดสอบการคำนวณเมตริกแต่ละตัว...")
    
    try:
        client = Client(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
        analyzer = CoinAnalyzer(client)
        
        test_symbol = "BTCUSDT"
        
        # ดึงข้อมูลตลาด
        df = await analyzer.get_market_data(test_symbol)
        if not df.empty:
            print(f"✅ ดึงข้อมูลตลาดสำหรับ {test_symbol} สำเร็จ")
            
            # คำนวณความผันผวน
            volatility = analyzer.calculate_volatility(df)
            print(f"   ความผันผวน: {volatility:.2f}%")
            
            # คำนวณปริมาณการซื้อขาย
            volume_profile = analyzer.calculate_volume_profile(df)
            print(f"   ปริมาณเฉลี่ย: {volume_profile['avg_volume']:,.0f}")
            print(f"   ความเสถียรของปริมาณ: {volume_profile['volume_stability']:.3f}")
            
            # คำนวณสภาพคล่อง
            liquidity_score = analyzer.calculate_liquidity_score(df)
            print(f"   คะแนนสภาพคล่อง: {liquidity_score:.1f}/100")
            
            # ทดสอบการกำหนดหมวดหมู่
            order_size_category = analyzer._determine_order_size_category(
                volatility, volume_profile, liquidity_score
            )
            leverage_category = analyzer._determine_leverage_category(
                volatility, volume_profile
            )
            
            print(f"   หมวดหมู่ขนาด Order: {order_size_category}")
            print(f"   หมวดหมู่ Leverage: {leverage_category}")
            
        else:
            print(f"❌ ไม่สามารถดึงข้อมูลตลาดสำหรับ {test_symbol} ได้")
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการทดสอบเมตริก: {e}")

def save_test_results(analyses):
    """บันทึกผลการทดสอบ"""
    try:
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(analyses, f, indent=2, ensure_ascii=False)
        print("💾 บันทึกผลการทดสอบลงไฟล์ test_results.json สำเร็จ")
    except Exception as e:
        print(f"❌ ไม่สามารถบันทึกผลการทดสอบได้: {e}")

async def main():
    """ฟังก์ชันหลัก"""
    print("🚀 เริ่มการทดสอบระบบวิเคราะห์เหรียญ")
    print("=" * 50)
    
    # ทดสอบระบบหลัก
    await test_coin_analysis()
    
    # ทดสอบเมตริกแต่ละตัว
    await test_individual_metrics()
    
    print("\n" + "=" * 50)
    print("🎉 การทดสอบเสร็จสิ้น!")

if __name__ == "__main__":
    asyncio.run(main()) 