#!/usr/bin/env python3
"""
Win Rate Optimizer - เครื่องมือปรับปรุง Win Rate ให้ > 55%
"""

import json
import os
from datetime import datetime

class WinRateOptimizer:
    def __init__(self):
        self.target_win_rate = 55  # เป้าหมาย Win Rate > 55%
        
        # กลยุทธ์สำหรับปรับปรุง Win Rate
        self.optimization_strategies = {
            'conservative': {
                'description': 'เน้นความปลอดภัย ลดความเสี่ยง',
                'confidence_threshold': 0.6,
                'strength_threshold': 65,
                'consensus_threshold': 4,
                'volume_spike_threshold': 1.8,
                'position_size_multiplier': 0.7  # ลด position size
            },
            'selective': {
                'description': 'เลือกสรร signals ที่ดีที่สุด',
                'confidence_threshold': 0.5,
                'strength_threshold': 60,
                'consensus_threshold': 5,
                'volume_spike_threshold': 2.2,
                'position_size_multiplier': 0.8
            },
            'confirmation_heavy': {
                'description': 'เน้น confirmation หนัก',
                'confidence_threshold': 0.45,
                'strength_threshold': 55,
                'consensus_threshold': 6,
                'volume_spike_threshold': 2.5,
                'position_size_multiplier': 0.9
            }
        }
        
        # Strategies ที่มักให้ Win Rate สูง
        self.high_winrate_strategies = {
            'MACD Trend': 0.18,
            'Bollinger RSI': 0.15,
            'Parabolic SAR ADX': 0.16,
            'Strong Trend': 0.20,
            'Emergency': 0.22,
            'Volume Profile': 0.14,
            'Market Structure': 0.12
        }
        
        # Strategies ที่ควรลด weight
        self.risky_strategies = {
            'Momentum': 0.05,
            'Fibonacci RSI': 0.04,
            'Breakout': 0.08,
            'Momentum Acceleration': 0.08
        }

    def load_current_config(self):
        """โหลด config ปัจจุบัน"""
        try:
            with open('strategy_config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return None

    def analyze_current_performance(self):
        """วิเคราะห์ performance ปัจจุบัน"""
        try:
            if os.path.exists('backtest_report.json'):
                with open('backtest_report.json', 'r') as f:
                    results = json.load(f)
                    
                current_win_rate = results.get('win_rate_pct', 0)
                print(f"📊 Win Rate ปัจจุบัน: {current_win_rate:.2f}%")
                
                if current_win_rate >= self.target_win_rate:
                    print(f"🎉 Win Rate อยู่ในเป้าหมายแล้ว! (> {self.target_win_rate}%)")
                    return True, current_win_rate
                else:
                    gap = self.target_win_rate - current_win_rate
                    print(f"📈 ต้องปรับปรุง Win Rate อีก {gap:.2f}% เพื่อให้ถึงเป้าหมาย")
                    return False, current_win_rate
            else:
                print("⚠️ ไม่พบผลลัพธ์ backtest - ต้องรัน backtest ก่อน")
                return False, 0
        except Exception as e:
            print(f"❌ Error analyzing performance: {e}")
            return False, 0

    def generate_optimized_config(self, optimization_type='conservative'):
        """สร้าง config ที่ปรับปรุงแล้ว"""
        config = self.load_current_config()
        if not config:
            return None
        
        strategy = self.optimization_strategies[optimization_type]
        
        print(f"🔧 ใช้กลยุทธ์: {optimization_type}")
        print(f"📝 {strategy['description']}")
        
        # ปรับ signal thresholds
        config['signal_thresholds']['confidence_threshold'] = strategy['confidence_threshold']
        config['signal_thresholds']['strength_threshold'] = strategy['strength_threshold']
        config['signal_thresholds']['consensus_threshold'] = strategy['consensus_threshold']
        
        # ปรับ volume analysis
        config['volume_analysis']['volume_spike_threshold'] = strategy['volume_spike_threshold']
        
        # ปรับ strategy weights เน้น high win rate strategies
        new_weights = {}
        
        # เพิ่ม weight สำหรับ strategies ที่ดี
        for strategy_name, weight in self.high_winrate_strategies.items():
            if strategy_name in config['strategy_weights']:
                new_weights[strategy_name] = weight
        
        # ลด weight สำหรับ strategies ที่เสี่ยง
        for strategy_name, weight in self.risky_strategies.items():
            if strategy_name in config['strategy_weights']:
                new_weights[strategy_name] = weight
        
        # เก็บ strategies อื่นๆ ที่ไม่ได้กำหนด
        for strategy_name, current_weight in config['strategy_weights'].items():
            if strategy_name not in new_weights:
                new_weights[strategy_name] = current_weight * 0.8  # ลดลง 20%
        
        config['strategy_weights'] = new_weights
        
        return config

    def save_optimized_config(self, config, optimization_type):
        """บันทึก config ที่ปรับปรุงแล้ว"""
        try:
            filename = f'strategy_config_winrate_{optimization_type}.json'
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ บันทึก {filename} แล้ว")
            
            # สร้างไฟล์สำรอง
            backup_filename = f'strategy_config_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            original_config = self.load_current_config()
            if original_config:
                with open(backup_filename, 'w') as f:
                    json.dump(original_config, f, indent=2)
                print(f"💾 สำรอง config เดิมเป็น {backup_filename}")
            
            return filename
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return None

    def print_optimization_summary(self, config, optimization_type):
        """แสดงสรุปการปรับปรุง"""
        strategy = self.optimization_strategies[optimization_type]
        
        print("\n🎯 WIN RATE OPTIMIZATION SUMMARY")
        print("=" * 50)
        print(f"📊 เป้าหมาย: Win Rate > {self.target_win_rate}%")
        print(f"🔧 กลยุทธ์: {optimization_type}")
        print(f"📝 คำอธิบาย: {strategy['description']}")
        print()
        
        print("⚙️ การปรับแต่งหลัก:")
        print(f"  • Confidence Threshold: {strategy['confidence_threshold']}")
        print(f"  • Strength Threshold: {strategy['strength_threshold']}")
        print(f"  • Consensus Threshold: {strategy['consensus_threshold']}")
        print(f"  • Volume Spike Threshold: {strategy['volume_spike_threshold']}")
        print()
        
        print("📈 Top Strategies (เพิ่ม weight):")
        for strategy_name, weight in self.high_winrate_strategies.items():
            if strategy_name in config['strategy_weights']:
                print(f"  • {strategy_name}: {weight:.2f}")
        print()
        
        print("📉 Risky Strategies (ลด weight):")
        for strategy_name, weight in self.risky_strategies.items():
            if strategy_name in config['strategy_weights']:
                print(f"  • {strategy_name}: {weight:.2f}")
        print()

    def generate_test_plan(self, optimization_type):
        """สร้างแผนการทดสอบ"""
        print("🧪 แผนการทดสอบ Win Rate Optimization:")
        print("=" * 50)
        print("1. รัน backtest ด้วย config ใหม่:")
        print(f"   cp strategy_config_winrate_{optimization_type}.json strategy_config.json")
        print("   python backtest.py")
        print()
        print("2. ตรวจสอบผลลัพธ์:")
        print("   python performance_analyzer.py")
        print()
        print("3. หาก Win Rate ยังไม่ถึงเป้าหมาย:")
        print("   - ลองใช้ optimization_type อื่น")
        print("   - ปรับ thresholds เพิ่มเติม")
        print("   - ลดจำนวน strategies ที่ใช้")
        print()
        print("4. หาก Win Rate ดีแล้ว:")
        print("   - ทดสอบ paper trading")
        print("   - รัน bot จริงด้วยเงินน้อย")
        print()

def main():
    """Main function"""
    print("🎯 WIN RATE OPTIMIZER")
    print("เป้าหมาย: ปรับปรุง Win Rate ให้ > 55%")
    print("=" * 50)
    
    optimizer = WinRateOptimizer()
    
    # วิเคราะห์ performance ปัจจุบัน
    is_good, current_rate = optimizer.analyze_current_performance()
    
    if is_good:
        print("🎉 Win Rate อยู่ในเป้าหมายแล้ว!")
        return
    
    print("\n🔧 เลือกกลยุทธ์การปรับปรุง:")
    print("1. conservative - เน้นความปลอดภัย (แนะนำสำหรับ Win Rate < 45%)")
    print("2. selective - เลือกสรร signals ดีๆ (แนะนำสำหรับ Win Rate 45-50%)")
    print("3. confirmation_heavy - เน้น confirmation (แนะนำสำหรับ Win Rate 50-55%)")
    
    # เลือกกลยุทธ์อัตโนมัติตาม current win rate
    if current_rate < 45:
        optimization_type = 'conservative'
        print(f"\n🤖 แนะนำ: {optimization_type} (Win Rate ต่ำกว่า 45%)")
    elif current_rate < 50:
        optimization_type = 'selective'
        print(f"\n🤖 แนะนำ: {optimization_type} (Win Rate อยู่ที่ 45-50%)")
    else:
        optimization_type = 'confirmation_heavy'
        print(f"\n🤖 แนะนำ: {optimization_type} (Win Rate อยู่ที่ 50-55%)")
    
    # สร้าง optimized config
    config = optimizer.generate_optimized_config(optimization_type)
    if not config:
        print("❌ ไม่สามารถสร้าง optimized config ได้")
        return
    
    # บันทึก config
    filename = optimizer.save_optimized_config(config, optimization_type)
    if not filename:
        return
    
    # แสดงสรุป
    optimizer.print_optimization_summary(config, optimization_type)
    
    # แสดงแผนการทดสอบ
    optimizer.generate_test_plan(optimization_type)
    
    print("🚀 พร้อมทดสอบ! ใช้คำสั่ง:")
    print(f"cp {filename} strategy_config.json && python backtest.py")

if __name__ == "__main__":
    main() 