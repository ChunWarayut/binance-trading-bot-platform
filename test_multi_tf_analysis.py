#!/usr/bin/env python3
"""
สคริปต์ทดสอบระบบวิเคราะห์เหรียญ Multi-Timeframe
"""

import asyncio
import json
import time
from trading_bot import TradingBot
from coin_analysis import CoinAnalyzer
from binance.client import Client
import config

async def test_multi_timeframe_analysis():
    """ทดสอบระบบวิเคราะห์ Multi-Timeframe"""
    print("🪙 เริ่มทดสอบระบบวิเคราะห์ Multi-Timeframe...")
    
    try:
        # สร้าง bot instance
        bot = TradingBot()
        
        # ทดสอบการวิเคราะห์เหรียญเดียวแบบ Multi-Timeframe
        print("\n📊 ทดสอบการวิเคราะห์ Multi-Timeframe สำหรับ BTCUSDT...")
        analysis = await bot.coin_analyzer.analyze_coin_multi_tf("BTCUSDT")
        
        if analysis:
            print(f"✅ วิเคราะห์ BTCUSDT สำเร็จ")
            print(f"   ราคาปัจจุบัน: {analysis['current_price']:.2f} USDT")
            print(f"   ขนาด Order: {analysis['categories']['order_size']}")
            print(f"   Leverage: {analysis['categories']['leverage']}")
            print(f"   Position Size Multiplier: {analysis['recommendations']['position_size_multiplier']}")
            print(f"   Recommended Leverage: {analysis['recommendations']['leverage']['recommended']}x")
            
            # แสดงข้อมูล Weighted Metrics
            print(f"\n📈 Weighted Metrics (ค่าเฉลี่ยถ่วงน้ำหนัก):")
            weighted = analysis['weighted_metrics']
            print(f"   ความผันผวน: {weighted['volatility']:.2f}%")
            print(f"   สภาพคล่อง: {weighted['liquidity_score']:.1f}/100")
            print(f"   ปริมาณเฉลี่ย: {weighted['volume_profile']['avg_volume']:,.0f}")
            print(f"   ความแข็งแกร่งของเทรนด์: {weighted['trend_strength']:.1f}/100")
            
            # แสดงข้อมูลแต่ละ Timeframe
            print(f"\n⏰ Timeframe Analysis:")
            tf_analysis = analysis['timeframe_analysis']
            
            timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
            for tf in timeframes:
                if tf in tf_analysis['volatility']:
                    vol = tf_analysis['volatility'][tf]
                    liq = tf_analysis['liquidity_score'][tf]
                    trend = tf_analysis['trend_strength'][tf]
                    print(f"   {tf:>4}: Vol={vol:5.2f}%, Liq={liq:5.1f}, Trend={trend:6.1f}")
            
            # แสดงหมายเหตุ
            notes = analysis['recommendations']['notes']
            if notes:
                print(f"\n📝 หมายเหตุ:")
                for note in notes:
                    print(f"   {note}")
        else:
            print("❌ ไม่สามารถวิเคราะห์ BTCUSDT ได้")
        
        # ทดสอบการวิเคราะห์เหรียญทั้งหมดแบบขนาน
        print(f"\n🔄 ทดสอบการวิเคราะห์เหรียญทั้งหมดแบบขนาน...")
        start_time = time.time()
        
        analyses = await bot.coin_analyzer.analyze_all_coins(config.TRADING_PAIRS[:5])  # ทดสอบแค่ 5 เหรียญ
        
        end_time = time.time()
        duration = end_time - start_time
        
        if analyses:
            print(f"✅ วิเคราะห์เหรียญสำเร็จ {len(analyses)} เหรียญ ในเวลา {duration:.2f} วินาที")
            
            # แสดงผลการวิเคราะห์
            print(f"\n📊 ผลการวิเคราะห์:")
            for symbol, analysis in analyses.items():
                order_size = analysis['categories']['order_size']
                leverage = analysis['categories']['leverage']
                multiplier = analysis['recommendations']['position_size_multiplier']
                recommended_leverage = analysis['recommendations']['leverage']['recommended']
                trend_strength = analysis['weighted_metrics']['trend_strength']
                
                print(f"   {symbol}: {order_size} size, {leverage} leverage ({multiplier:.1f}x, {recommended_leverage}x, Trend: {trend_strength:.1f})")
            
            # สร้างรายงานสรุป
            print(f"\n📋 รายงานสรุป:")
            summary = bot.coin_analyzer.get_summary_report(analyses)
            print(summary)
            
            # บันทึกผลการวิเคราะห์
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"multi_tf_analysis_{timestamp}.json"
            
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(analyses, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 บันทึกผลการวิเคราะห์ลงไฟล์: {filename}")
            
        else:
            print("❌ ไม่สามารถวิเคราะห์เหรียญได้")
        
        print("\n✅ การทดสอบ Multi-Timeframe เสร็จสิ้น!")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการทดสอบ: {e}")

async def test_timeframe_comparison():
    """ทดสอบการเปรียบเทียบระหว่าง Timeframe ต่างๆ"""
    print("\n🔬 ทดสอบการเปรียบเทียบ Timeframe...")
    
    try:
        client = Client(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
        analyzer = CoinAnalyzer(client)
        
        test_symbol = "ETHUSDT"
        
        # ดึงข้อมูลหลาย Timeframe
        timeframe_data = await analyzer.get_market_data_parallel(test_symbol)
        
        if timeframe_data:
            print(f"✅ ดึงข้อมูลหลาย Timeframe สำหรับ {test_symbol} สำเร็จ")
            
            # คำนวณเมตริกแต่ละ Timeframe
            volatility_multi = analyzer.calculate_volatility_multi_tf(timeframe_data)
            liquidity_multi = analyzer.calculate_liquidity_score_multi_tf(timeframe_data)
            trend_multi = analyzer.calculate_trend_strength_multi_tf(timeframe_data)
            
            print(f"\n📊 การเปรียบเทียบ Timeframe:")
            print(f"{'Timeframe':>6} {'Volatility':>10} {'Liquidity':>10} {'Trend':>8}")
            print("-" * 40)
            
            timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
            for tf in timeframes:
                if tf in timeframe_data and not timeframe_data[tf].empty:
                    vol = volatility_multi.get(tf, 0)
                    liq = liquidity_multi.get(tf, 0)
                    trend = trend_multi.get(tf, 0)
                    print(f"{tf:>6} {vol:>10.2f} {liq:>10.1f} {trend:>8.1f}")
            
            # คำนวณค่าเฉลี่ยถ่วงน้ำหนัก
            tf_weights = {
                '1m': 0.05, '5m': 0.1, '15m': 0.15, 
                '1h': 0.25, '4h': 0.25, '1d': 0.2
            }
            
            weighted_vol = sum(volatility_multi.get(tf, 0) * tf_weights.get(tf, 0) for tf in tf_weights)
            weighted_liq = sum(liquidity_multi.get(tf, 0) * tf_weights.get(tf, 0) for tf in tf_weights)
            weighted_trend = sum(trend_multi.get(tf, 0) * tf_weights.get(tf, 0) for tf in tf_weights)
            
            print("-" * 40)
            print(f"{'Weighted':>6} {weighted_vol:>10.2f} {weighted_liq:>10.1f} {weighted_trend:>8.1f}")
            
        else:
            print(f"❌ ไม่สามารถดึงข้อมูลหลาย Timeframe สำหรับ {test_symbol} ได้")
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการทดสอบ Timeframe: {e}")

async def test_parallel_performance():
    """ทดสอบประสิทธิภาพการทำงานแบบขนาน"""
    print("\n⚡ ทดสอบประสิทธิภาพการทำงานแบบขนาน...")
    
    try:
        client = Client(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
        analyzer = CoinAnalyzer(client)
        
        test_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        
        # ทดสอบการวิเคราะห์แบบขนาน
        print(f"🔄 วิเคราะห์ {len(test_symbols)} เหรียญแบบขนาน...")
        start_time = time.time()
        
        tasks = [analyzer.analyze_coin_multi_tf(symbol) for symbol in test_symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        parallel_duration = end_time - start_time
        
        print(f"✅ การวิเคราะห์แบบขนานเสร็จสิ้นใน {parallel_duration:.2f} วินาที")
        
        # ทดสอบการวิเคราะห์แบบลำดับ
        print(f"🔄 วิเคราะห์ {len(test_symbols)} เหรียญแบบลำดับ...")
        start_time = time.time()
        
        sequential_results = []
        for symbol in test_symbols:
            result = await analyzer.analyze_coin_multi_tf(symbol)
            sequential_results.append(result)
        
        end_time = time.time()
        sequential_duration = end_time - start_time
        
        print(f"✅ การวิเคราะห์แบบลำดับเสร็จสิ้นใน {sequential_duration:.2f} วินาที")
        
        # คำนวณความเร็ว
        speedup = sequential_duration / parallel_duration if parallel_duration > 0 else 0
        print(f"🚀 ความเร็วเพิ่มขึ้น: {speedup:.2f}x")
        
        # แสดงผลลัพธ์
        print(f"\n📊 ผลลัพธ์การวิเคราะห์:")
        for i, symbol in enumerate(test_symbols):
            if i < len(results) and not isinstance(results[i], Exception):
                analysis = results[i]
                order_size = analysis['categories']['order_size']
                leverage = analysis['categories']['leverage']
                print(f"   {symbol}: {order_size} size, {leverage} leverage")
            else:
                print(f"   {symbol}: ❌ เกิดข้อผิดพลาด")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการทดสอบประสิทธิภาพ: {e}")

async def main():
    """ฟังก์ชันหลัก"""
    print("🚀 เริ่มการทดสอบระบบวิเคราะห์ Multi-Timeframe")
    print("=" * 60)
    
    # ทดสอบระบบหลัก
    await test_multi_timeframe_analysis()
    
    # ทดสอบการเปรียบเทียบ Timeframe
    await test_timeframe_comparison()
    
    # ทดสอบประสิทธิภาพ
    await test_parallel_performance()
    
    print("\n" + "=" * 60)
    print("🎉 การทดสอบ Multi-Timeframe เสร็จสิ้น!")

if __name__ == "__main__":
    asyncio.run(main()) 