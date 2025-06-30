#!/usr/bin/env python3
"""
Performance Analyzer - วิเคราะห์ผลลัพธ์ trading bot และแนะนำการปรับปรุง
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import os

class PerformanceAnalyzer:
    def __init__(self):
        self.performance_thresholds = {
            'win_rate': {
                'excellent': 60,
                'very_good': 55,
                'good': 50,
                'average': 45,
                'poor': 0
            },
            'profit_factor': {
                'excellent': 2.0,
                'very_good': 1.5,
                'good': 1.2,
                'average': 1.0,
                'poor': 0
            },
            'max_drawdown': {
                'excellent': 10,
                'very_good': 15,
                'good': 20,
                'average': 30,
                'poor': 100
            },
            'sharpe_ratio': {
                'excellent': 2.0,
                'very_good': 1.5,
                'good': 1.0,
                'average': 0.5,
                'poor': 0
            }
        }
    
    def load_backtest_results(self, file_path='backtest_report.json'):
        """โหลดผลลัพธ์ backtest"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                print(f"❌ ไม่พบไฟล์ {file_path}")
                return None
        except Exception as e:
            print(f"❌ Error loading results: {e}")
            return None
    
    def evaluate_metric(self, value, metric_name, reverse=False):
        """ประเมินค่า metric"""
        thresholds = self.performance_thresholds[metric_name]
        
        if reverse:  # สำหรับ drawdown (ยิ่งน้อยยิ่งดี)
            if value <= thresholds['excellent']:
                return 'excellent', '🏆'
            elif value <= thresholds['very_good']:
                return 'very_good', '✅'
            elif value <= thresholds['good']:
                return 'good', '👍'
            elif value <= thresholds['average']:
                return 'average', '⚠️'
            else:
                return 'poor', '❌'
        else:  # สำหรับ metrics อื่นๆ (ยิ่งมากยิ่งดี)
            if value >= thresholds['excellent']:
                return 'excellent', '🏆'
            elif value >= thresholds['very_good']:
                return 'very_good', '✅'
            elif value >= thresholds['good']:
                return 'good', '👍'
            elif value >= thresholds['average']:
                return 'average', '⚠️'
            else:
                return 'poor', '❌'
    
    def analyze_performance(self, results):
        """วิเคราะห์ performance แบบละเอียด"""
        if not results:
            return None
        
        analysis = {
            'overall_score': 0,
            'metrics': {},
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }
        
        # วิเคราะห์แต่ละ metric
        metrics_to_analyze = [
            ('win_rate_pct', 'win_rate', False),
            ('profit_factor', 'profit_factor', False),
            ('max_drawdown_pct', 'max_drawdown', True),
            ('sharpe_ratio', 'sharpe_ratio', False)
        ]
        
        total_score = 0
        metric_count = 0
        
        for result_key, threshold_key, reverse in metrics_to_analyze:
            if result_key in results:
                value = results[result_key]
                rating, emoji = self.evaluate_metric(value, threshold_key, reverse)
                
                analysis['metrics'][result_key] = {
                    'value': value,
                    'rating': rating,
                    'emoji': emoji
                }
                
                # คำนวณคะแนน
                score_map = {'excellent': 5, 'very_good': 4, 'good': 3, 'average': 2, 'poor': 1}
                total_score += score_map[rating]
                metric_count += 1
                
                # เก็บจุดแข็งและจุดอ่อน
                if rating in ['excellent', 'very_good']:
                    analysis['strengths'].append(f"{result_key}: {value:.2f} {emoji}")
                elif rating == 'poor':
                    analysis['weaknesses'].append(f"{result_key}: {value:.2f} {emoji}")
        
        # คำนวณคะแนนรวม
        if metric_count > 0:
            analysis['overall_score'] = (total_score / (metric_count * 5)) * 100
        
        # สร้างคำแนะนำ
        analysis['recommendations'] = self.generate_recommendations(analysis['metrics'], results)
        
        return analysis
    
    def generate_recommendations(self, metrics, results):
        """สร้างคำแนะนำการปรับปรุง"""
        recommendations = []
        
        # Win Rate
        if 'win_rate_pct' in metrics:
            win_rate = metrics['win_rate_pct']['value']
            if win_rate < 50:
                recommendations.append("🎯 ปรับ strategy weights ให้เน้น conservative strategies")
                recommendations.append("📊 เพิ่ม confirmation signals ก่อนเข้า trade")
                recommendations.append("⏰ ใช้ multiple timeframe analysis")
        
        # Profit Factor
        if 'profit_factor' in metrics:
            pf = metrics['profit_factor']['value']
            if pf < 1.2:
                recommendations.append("💰 ปรับ take-profit levels ให้สูงขึ้น")
                recommendations.append("🛑 เพิ่ม stop-loss เพื่อลดความเสียหาย")
                recommendations.append("📈 เน้น trend-following strategies")
        
        # Max Drawdown
        if 'max_drawdown_pct' in metrics:
            dd = metrics['max_drawdown_pct']['value']
            if dd > 20:
                recommendations.append("🔒 ลด position size (ปัจจุบัน 10% → 5%)")
                recommendations.append("⚡ เพิ่ม emergency exit conditions")
                recommendations.append("🎚️ ปรับ risk management parameters")
        
        # Sharpe Ratio
        if 'sharpe_ratio' in metrics:
            sr = metrics['sharpe_ratio']['value']
            if sr < 1.0:
                recommendations.append("📉 ปรับ portfolio diversification")
                recommendations.append("⏱️ เปลี่ยน trading frequency")
                recommendations.append("🎯 เลือก symbols ที่มี volatility เหมาะสม")
        
        # Strategy-specific recommendations
        if 'strategy_performance' in results:
            strategy_perf = results['strategy_performance']
            best_strategies = []
            worst_strategies = []
            
            for strategy, perf in strategy_perf.items():
                if perf['win_rate'] > 65:
                    best_strategies.append(strategy)
                elif perf['win_rate'] < 40:
                    worst_strategies.append(strategy)
            
            if best_strategies:
                recommendations.append(f"⭐ เพิ่ม weight ให้ strategies ที่ดี: {', '.join(best_strategies)}")
            
            if worst_strategies:
                recommendations.append(f"🔻 ลด weight หรือปิด strategies ที่แย่: {', '.join(worst_strategies)}")
        
        return recommendations
    
    def print_analysis(self, analysis):
        """แสดงผลการวิเคราะห์"""
        if not analysis:
            print("❌ ไม่มีข้อมูลสำหรับวิเคราะห์")
            return
        
        print("📊 PERFORMANCE ANALYSIS REPORT")
        print("=" * 50)
        
        # Overall Score
        score = analysis['overall_score']
        if score >= 80:
            score_emoji = "🏆"
            score_text = "ยอดเยี่ยม"
        elif score >= 70:
            score_emoji = "✅"
            score_text = "ดีมาก"
        elif score >= 60:
            score_emoji = "👍"
            score_text = "ดี"
        elif score >= 50:
            score_emoji = "⚠️"
            score_text = "ปานกลาง"
        else:
            score_emoji = "❌"
            score_text = "ต้องปรับปรุง"
        
        print(f"🎯 Overall Score: {score:.1f}/100 {score_emoji} ({score_text})")
        print()
        
        # Detailed Metrics
        print("📈 DETAILED METRICS:")
        for metric, data in analysis['metrics'].items():
            print(f"  • {metric}: {data['value']:.2f} {data['emoji']} ({data['rating']})")
        print()
        
        # Strengths
        if analysis['strengths']:
            print("💪 STRENGTHS:")
            for strength in analysis['strengths']:
                print(f"  • {strength}")
            print()
        
        # Weaknesses
        if analysis['weaknesses']:
            print("⚠️ WEAKNESSES:")
            for weakness in analysis['weaknesses']:
                print(f"  • {weakness}")
            print()
        
        # Recommendations
        if analysis['recommendations']:
            print("🔧 RECOMMENDATIONS:")
            for i, rec in enumerate(analysis['recommendations'], 1):
                print(f"  {i}. {rec}")
            print()
    
    def generate_improvement_config(self, analysis, results):
        """สร้าง config ที่ปรับปรุงแล้ว"""
        try:
            # โหลด config ปัจจุบัน
            with open('strategy_config.json', 'r') as f:
                config = json.load(f)
            
            # ปรับแต่งตาม recommendations
            if 'max_drawdown_pct' in analysis['metrics']:
                if analysis['metrics']['max_drawdown_pct']['rating'] == 'poor':
                    # ลด confidence threshold
                    config['signal_thresholds']['confidence_threshold'] = 0.5
                    # เพิ่ม consensus threshold
                    config['signal_thresholds']['consensus_threshold'] = 4
            
            if 'win_rate_pct' in analysis['metrics']:
                if analysis['metrics']['win_rate_pct']['value'] < 50:
                    # เพิ่ม strength threshold
                    config['signal_thresholds']['strength_threshold'] = 60
                    # ปรับ volume thresholds
                    config['volume_analysis']['volume_spike_threshold'] = 1.8
            
            # บันทึก config ใหม่
            with open('strategy_config_improved.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✅ สร้าง strategy_config_improved.json แล้ว")
            return config
            
        except Exception as e:
            print(f"❌ Error generating improved config: {e}")
            return None

def main():
    """Main function"""
    print("🧪 TRADING BOT PERFORMANCE ANALYZER")
    print("=" * 50)
    
    analyzer = PerformanceAnalyzer()
    
    # ลองโหลดผลลัพธ์ backtest
    results = analyzer.load_backtest_results()
    
    if results:
        print("✅ พบผลลัพธ์ backtest")
        analysis = analyzer.analyze_performance(results)
        analyzer.print_analysis(analysis)
        
        # สร้าง improved config
        analyzer.generate_improvement_config(analysis, results)
        
    else:
        print("⚠️ ไม่พบผลลัพธ์ backtest")
        print("📋 วิธีใช้งาน:")
        print("1. รัน backtest ก่อน: python backtest.py")
        print("2. จากนั้นรัน analyzer: python performance_analyzer.py")
        print()
        
        # แสดงตัวอย่างการวิเคราะห์
        print("📊 ตัวอย่างเกณฑ์การประเมิน:")
        print("Win Rate:")
        print("  🏆 > 60% = ยอดเยี่ยม")
        print("  ✅ 55-60% = ดีมาก") 
        print("  👍 50-55% = ดี")
        print("  ⚠️ 45-50% = ปานกลาง")
        print("  ❌ < 45% = ต้องปรับปรุง")

if __name__ == "__main__":
    main() 