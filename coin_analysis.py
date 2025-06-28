import pandas as pd
import numpy as np
from binance.client import Client
import asyncio
from loguru import logger
import config
from typing import Dict, List, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

class CoinAnalyzer:
    def __init__(self, client: Client):
        self.client = client
        self.coin_analysis_cache = {}
        self.cache_duration = 3600  # 1 hour cache
        self.timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']  # Multiple timeframes
        
    async def get_market_data_parallel(self, symbol: str, timeframes: List[str] = None) -> Dict[str, pd.DataFrame]:
        """ดึงข้อมูลตลาดหลาย Timeframe แบบขนาน"""
        if timeframes is None:
            timeframes = self.timeframes
            
        async def fetch_timeframe_data(tf: str) -> Tuple[str, pd.DataFrame]:
            try:
                df = await self.get_market_data(symbol, tf)
                return tf, df
            except Exception as e:
                logger.error(f"Error fetching {symbol} {tf}: {e}")
                return tf, pd.DataFrame()
        
        # รันการดึงข้อมูลแบบขนาน
        tasks = [fetch_timeframe_data(tf) for tf in timeframes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # จัดระเบียบผลลัพธ์
        timeframe_data = {}
        for result in results:
            if isinstance(result, tuple) and len(result) == 2:
                tf, df = result
                timeframe_data[tf] = df
            else:
                logger.error(f"Unexpected result: {result}")
        
        return timeframe_data
    
    async def get_market_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """ดึงข้อมูลตลาดสำหรับการวิเคราะห์"""
        try:
            klines = await self.safe_api_call(
                self.client.futures_klines, 
                symbol=symbol, 
                interval=interval, 
                limit=limit
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error getting market data for {symbol} {interval}: {e}")
            return pd.DataFrame()
    
    async def safe_api_call(self, api_func, *args, **kwargs):
        """Safe API call with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return api_func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(1)
    
    def calculate_volatility_multi_tf(self, timeframe_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """คำนวณความผันผวนหลาย Timeframe"""
        volatility_results = {}
        
        for tf, df in timeframe_data.items():
            if not df.empty:
                volatility = self.calculate_volatility(df)
                volatility_results[tf] = volatility
            else:
                volatility_results[tf] = 0.0
        
        return volatility_results
    
    def calculate_volatility(self, df: pd.DataFrame) -> float:
        """คำนวณความผันผวนของราคา"""
        if df.empty:
            return 0.0
        
        # Calculate daily returns
        df['returns'] = df['close'].pct_change()
        
        # Calculate volatility (standard deviation of returns)
        volatility = df['returns'].std() * np.sqrt(24)  # Annualized (24 hours)
        return volatility * 100  # Convert to percentage
    
    def calculate_volume_profile_multi_tf(self, timeframe_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """วิเคราะห์ปริมาณการซื้อขายหลาย Timeframe"""
        volume_results = {}
        
        for tf, df in timeframe_data.items():
            if not df.empty:
                volume_profile = self.calculate_volume_profile(df)
                volume_results[tf] = volume_profile
            else:
                volume_results[tf] = {'avg_volume': 0, 'volume_stability': 0}
        
        return volume_results
    
    def calculate_volume_profile(self, df: pd.DataFrame) -> Dict[str, float]:
        """วิเคราะห์ปริมาณการซื้อขาย"""
        if df.empty:
            return {'avg_volume': 0, 'volume_stability': 0}
        
        # Average volume
        avg_volume = df['volume'].mean()
        
        # Volume stability (coefficient of variation)
        volume_cv = df['volume'].std() / df['volume'].mean() if df['volume'].mean() > 0 else 0
        volume_stability = 1 / (1 + volume_cv)  # Higher is more stable
        
        return {
            'avg_volume': avg_volume,
            'volume_stability': volume_stability
        }
    
    def calculate_liquidity_score_multi_tf(self, timeframe_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """คำนวณคะแนนสภาพคล่องหลาย Timeframe"""
        liquidity_results = {}
        
        for tf, df in timeframe_data.items():
            if not df.empty:
                liquidity_score = self.calculate_liquidity_score(df)
                liquidity_results[tf] = liquidity_score
            else:
                liquidity_results[tf] = 0.0
        
        return liquidity_results
    
    def calculate_liquidity_score(self, df: pd.DataFrame) -> float:
        """คำนวณคะแนนสภาพคล่อง"""
        if df.empty:
            return 0.0
        
        # Factors for liquidity:
        # 1. Average volume
        # 2. Volume consistency
        # 3. Price spread (high-low ratio)
        
        avg_volume = df['volume'].mean()
        volume_consistency = 1 - (df['volume'].std() / df['volume'].mean()) if df['volume'].mean() > 0 else 0
        
        # Price spread (lower is better for liquidity)
        price_spread = (df['high'] - df['low']) / df['close']
        avg_spread = price_spread.mean()
        spread_score = 1 / (1 + avg_spread)  # Higher is better
        
        # Combined liquidity score (0-100)
        liquidity_score = (
            min(avg_volume / 1000000, 1) * 40 +  # Volume component (40%)
            volume_consistency * 30 +             # Consistency component (30%)
            spread_score * 30                     # Spread component (30%)
        )
        
        return min(liquidity_score * 100, 100)
    
    def calculate_trend_strength_multi_tf(self, timeframe_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """คำนวณความแข็งแกร่งของเทรนด์หลาย Timeframe"""
        trend_results = {}
        
        for tf, df in timeframe_data.items():
            if not df.empty:
                trend_strength = self.calculate_trend_strength(df)
                trend_results[tf] = trend_strength
            else:
                trend_results[tf] = 0.0
        
        return trend_results
    
    def calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """คำนวณความแข็งแกร่งของเทรนด์"""
        if df.empty or len(df) < 20:
            return 0.0
        
        # คำนวณ SMA
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['sma50'] = df['close'].rolling(window=50).mean()
        
        # ดูทิศทางของ SMA
        current_sma20 = df['sma20'].iloc[-1]
        current_sma50 = df['sma50'].iloc[-1]
        
        # คำนวณความชันของ SMA
        sma20_slope = (df['sma20'].iloc[-1] - df['sma20'].iloc[-10]) / df['sma20'].iloc[-10] * 100
        sma50_slope = (df['sma50'].iloc[-1] - df['sma50'].iloc[-10]) / df['sma50'].iloc[-10] * 100
        
        # คำนวณความแข็งแกร่งของเทรนด์
        trend_strength = 0
        
        # ทิศทางของ SMA
        if current_sma20 > current_sma50:
            trend_strength += 25  # Uptrend
        else:
            trend_strength -= 25  # Downtrend
        
        # ความชันของ SMA
        if sma20_slope > 0:
            trend_strength += 25
        else:
            trend_strength -= 25
        
        if sma50_slope > 0:
            trend_strength += 25
        else:
            trend_strength -= 25
        
        # ปริมาณการซื้อขาย
        recent_volume = df['volume'].iloc[-5:].mean()
        avg_volume = df['volume'].mean()
        if recent_volume > avg_volume * 1.2:
            trend_strength += 25  # Volume confirmation
        elif recent_volume < avg_volume * 0.8:
            trend_strength -= 25  # Volume divergence
        
        return max(-100, min(100, trend_strength))
    
    async def analyze_coin_multi_tf(self, symbol: str) -> Dict:
        """วิเคราะห์เหรียญหลาย Timeframe"""
        cache_key = f"{symbol}_{int(time.time() // self.cache_duration)}"
        if cache_key in self.coin_analysis_cache:
            return self.coin_analysis_cache[cache_key]
        
        try:
            # ดึงข้อมูลหลาย Timeframe แบบขนาน
            timeframe_data = await self.get_market_data_parallel(symbol)
            
            if not timeframe_data or all(df.empty for df in timeframe_data.values()):
                return self._get_default_analysis(symbol)
            
            # ใช้ข้อมูล 1h สำหรับราคาปัจจุบัน
            current_price = 0
            if '1h' in timeframe_data and not timeframe_data['1h'].empty:
                current_price = float(timeframe_data['1h']['close'].iloc[-1])
            elif '5m' in timeframe_data and not timeframe_data['5m'].empty:
                current_price = float(timeframe_data['5m']['close'].iloc[-1])
            else:
                # ใช้ Timeframe แรกที่มีข้อมูล
                for tf, df in timeframe_data.items():
                    if not df.empty:
                        current_price = float(df['close'].iloc[-1])
                        break
            
            if current_price == 0:
                return self._get_default_analysis(symbol)
            
            # คำนวณเมตริกหลาย Timeframe
            volatility_multi = self.calculate_volatility_multi_tf(timeframe_data)
            volume_multi = self.calculate_volume_profile_multi_tf(timeframe_data)
            liquidity_multi = self.calculate_liquidity_score_multi_tf(timeframe_data)
            trend_multi = self.calculate_trend_strength_multi_tf(timeframe_data)
            
            # คำนวณค่าเฉลี่ยถ่วงน้ำหนัก (ให้น้ำหนักมากกับ Timeframe ที่นานกว่า)
            tf_weights = {
                '1m': 0.05, '5m': 0.1, '15m': 0.15, 
                '1h': 0.25, '4h': 0.25, '1d': 0.2
            }
            
            # คำนวณค่าเฉลี่ยถ่วงน้ำหนัก
            weighted_volatility = sum(volatility_multi.get(tf, 0) * tf_weights.get(tf, 0) for tf in tf_weights)
            weighted_volume = sum(volume_multi.get(tf, {}).get('avg_volume', 0) * tf_weights.get(tf, 0) for tf in tf_weights)
            weighted_liquidity = sum(liquidity_multi.get(tf, 0) * tf_weights.get(tf, 0) for tf in tf_weights)
            weighted_trend = sum(trend_multi.get(tf, 0) * tf_weights.get(tf, 0) for tf in tf_weights)
            
            # สร้าง volume profile รวม
            combined_volume_profile = {
                'avg_volume': weighted_volume,
                'volume_stability': sum(volume_multi.get(tf, {}).get('volume_stability', 0) * tf_weights.get(tf, 0) for tf in tf_weights)
            }
            
            # กำหนดหมวดหมู่
            order_size_category = self._determine_order_size_category(
                weighted_volatility, combined_volume_profile, weighted_liquidity
            )
            
            leverage_category = self._determine_leverage_category(
                weighted_volatility, combined_volume_profile, weighted_trend
            )
            
            # คำนวณคำแนะนำ
            recommendations = self._calculate_recommendations(
                order_size_category, leverage_category, weighted_volatility, weighted_liquidity
            )
            
            analysis = {
                'symbol': symbol,
                'current_price': current_price,
                'timeframe_analysis': {
                    'volatility': volatility_multi,
                    'volume_profile': volume_multi,
                    'liquidity_score': liquidity_multi,
                    'trend_strength': trend_multi
                },
                'weighted_metrics': {
                    'volatility': weighted_volatility,
                    'volume_profile': combined_volume_profile,
                    'liquidity_score': weighted_liquidity,
                    'trend_strength': weighted_trend
                },
                'categories': {
                    'order_size': order_size_category,
                    'leverage': leverage_category
                },
                'recommendations': recommendations,
                'timestamp': time.time()
            }
            
            # Cache the result
            self.coin_analysis_cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol} with multi-TF: {e}")
            return self._get_default_analysis(symbol)
    
    async def analyze_coin(self, symbol: str) -> Dict:
        """วิเคราะห์เหรียญแบบเดิม (ใช้ 1h timeframe)"""
        return await self.analyze_coin_multi_tf(symbol)
    
    def _determine_order_size_category(self, volatility: float, volume_profile: Dict, 
                                     liquidity_score: float) -> str:
        """กำหนดหมวดหมู่ขนาด order"""
        
        # Scoring system for order size (0-100)
        score = 0
        
        # Volatility factor (lower volatility = larger orders)
        if volatility < 2:
            score += 30  # Low volatility
        elif volatility < 5:
            score += 20  # Medium volatility
        elif volatility < 10:
            score += 10  # High volatility
        else:
            score += 5   # Very high volatility
        
        # Volume factor (higher volume = larger orders)
        if volume_profile['avg_volume'] > 1000000:
            score += 25  # High volume
        elif volume_profile['avg_volume'] > 500000:
            score += 20  # Medium-high volume
        elif volume_profile['avg_volume'] > 100000:
            score += 15  # Medium volume
        else:
            score += 5   # Low volume
        
        # Liquidity factor
        score += liquidity_score * 0.25  # 25% weight
        
        # Determine category
        if score >= 70:
            return "LARGE"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "SMALL"
    
    def _determine_leverage_category(self, volatility: float, volume_profile: Dict, 
                                   trend_strength: float = 0) -> str:
        """กำหนดหมวดหมู่ leverage"""
        
        # Scoring system for leverage (0-100)
        score = 0
        
        # Volatility factor (lower volatility = higher leverage)
        if volatility < 2:
            score += 40  # Low volatility = high leverage
        elif volatility < 5:
            score += 30  # Medium volatility = medium leverage
        elif volatility < 10:
            score += 20  # High volatility = low leverage
        else:
            score += 10  # Very high volatility = very low leverage
        
        # Volume stability factor (stable volume = higher leverage)
        score += volume_profile['volume_stability'] * 30
        
        # เพิ่มปัจจัยความแข็งแกร่งของเทรนด์
        if trend_strength > 50:
            score += 25  # Strong trend
        elif trend_strength > 0:
            score += 15  # Weak trend
        elif trend_strength > -50:
            score += 5   # Sideways
        else:
            score -= 10  # Strong counter-trend
        
        # Determine category
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_recommendations(self, order_size_category: str, leverage_category: str,
                                 volatility: float, liquidity_score: float) -> Dict:
        """คำนวณคำแนะนำเฉพาะ"""
        
        # Position size multipliers
        size_multipliers = {
            "LARGE": 1.0,    # 100% of available balance
            "MEDIUM": 0.6,   # 60% of available balance
            "SMALL": 0.3     # 30% of available balance
        }
        
        # Leverage recommendations
        leverage_recommendations = {
            "HIGH": {"min": 10, "max": 50, "recommended": 20},
            "MEDIUM": {"min": 5, "max": 20, "recommended": 10},
            "LOW": {"min": 1, "max": 10, "recommended": 5}
        }
        
        # Risk management recommendations
        risk_recommendations = {
            "max_positions": 3 if order_size_category == "LARGE" else 5,
            "position_spacing": "2h" if order_size_category == "LARGE" else "1h"
        }
        
        return {
            "position_size_multiplier": size_multipliers[order_size_category],
            "leverage": leverage_recommendations[leverage_category],
            "risk_management": risk_recommendations,
            "notes": self._generate_analysis_notes(order_size_category, leverage_category, volatility, liquidity_score)
        }
    
    def _generate_analysis_notes(self, order_size_category: str, leverage_category: str,
                               volatility: float, liquidity_score: float) -> List[str]:
        """สร้างหมายเหตุการวิเคราะห์"""
        notes = []
        
        # Order size notes
        if order_size_category == "LARGE":
            notes.append("✅ เหมาะสำหรับ order size ใหญ่ - ความผันผวนต่ำ, สภาพคล่องดี")
        elif order_size_category == "MEDIUM":
            notes.append("⚠️ ใช้ order size ปานกลาง - ความสมดุลระหว่างความเสี่ยงและโอกาส")
        else:
            notes.append("🔴 ใช้ order size เล็ก - ความผันผวนสูง, สภาพคล่องต่ำ")
        
        # Leverage notes
        if leverage_category == "HIGH":
            notes.append("🚀 เหมาะสำหรับ leverage สูง - ความผันผวนต่ำ, โมเมนตัมดี")
        elif leverage_category == "MEDIUM":
            notes.append("⚖️ ใช้ leverage ปานกลาง - ความสมดุลระหว่างผลตอบแทนและความเสี่ยง")
        else:
            notes.append("🛡️ ใช้ leverage ต่ำ - ความผันผวนสูง, ควรระมัดระวัง")
        
        # Multi-timeframe notes
        notes.append("📊 วิเคราะห์จากหลาย Timeframe (1m, 5m, 15m, 1h, 4h, 1d)")
        
        # Specific warnings
        if volatility > 10:
            notes.append("⚠️ ความผันผวนสูงมาก - ควรระมัดระวัง")
        
        if liquidity_score < 30:
            notes.append("⚠️ สภาพคล่องต่ำ - อาจมีปัญหาในการปิด position")
        
        return notes
    
    def _get_default_analysis(self, symbol: str) -> Dict:
        """ค่าเริ่มต้นเมื่อไม่สามารถวิเคราะห์ได้"""
        return {
            'symbol': symbol,
            'current_price': 0,
            'timeframe_analysis': {},
            'weighted_metrics': {
                'volatility': 0,
                'volume_profile': {'avg_volume': 0, 'volume_stability': 0},
                'liquidity_score': 0,
                'trend_strength': 0
            },
            'categories': {
                'order_size': 'SMALL',
                'leverage': 'LOW'
            },
            'recommendations': {
                'position_size_multiplier': 0.3,
                'leverage': {'min': 1, 'max': 5, 'recommended': 3},
                'risk_management': {
                    'max_positions': 3,
                    'position_spacing': '2h'
                },
                'notes': ['⚠️ ไม่สามารถวิเคราะห์ได้ - ใช้การตั้งค่าแบบอนุรักษ์นิยม']
            },
            'timestamp': time.time()
        }
    
    async def analyze_all_coins(self, symbols: List[str]) -> Dict[str, Dict]:
        """วิเคราะห์เหรียญทั้งหมดแบบขนาน"""
        results = {}
        
        # สร้าง tasks สำหรับการวิเคราะห์แบบขนาน
        tasks = [self.analyze_coin_multi_tf(symbol) for symbol in symbols]
        
        # รันการวิเคราะห์แบบขนาน
        analyses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # จัดระเบียบผลลัพธ์
        for i, (symbol, analysis) in enumerate(zip(symbols, analyses)):
            if isinstance(analysis, Exception):
                logger.error(f"❌ Failed to analyze {symbol}: {analysis}")
                results[symbol] = self._get_default_analysis(symbol)
            else:
                results[symbol] = analysis
                logger.info(f"✅ Analyzed {symbol}: {analysis['categories']['order_size']} size, {analysis['categories']['leverage']} leverage")
        
        return results
    
    def get_summary_report(self, analyses: Dict[str, Dict]) -> str:
        """สร้างรายงานสรุปการวิเคราะห์"""
        report = "📊 รายงานการวิเคราะห์เหรียญ (Multi-Timeframe)\n\n"
        
        # Categorize coins
        large_orders = []
        medium_orders = []
        small_orders = []
        
        high_leverage = []
        medium_leverage = []
        low_leverage = []
        
        for symbol, analysis in analyses.items():
            order_size = analysis['categories']['order_size']
            leverage = analysis['categories']['leverage']
            
            if order_size == "LARGE":
                large_orders.append(symbol)
            elif order_size == "MEDIUM":
                medium_orders.append(symbol)
            else:
                small_orders.append(symbol)
            
            if leverage == "HIGH":
                high_leverage.append(symbol)
            elif leverage == "MEDIUM":
                medium_leverage.append(symbol)
            else:
                low_leverage.append(symbol)
        
        # Order size summary
        report += "🎯 ขนาด Order:\n"
        report += f"   🔥 ใหญ่ ({len(large_orders)}): {', '.join(large_orders)}\n"
        report += f"   ⚖️ ปานกลาง ({len(medium_orders)}): {', '.join(medium_orders)}\n"
        report += f"   🔴 เล็ก ({len(small_orders)}): {', '.join(small_orders)}\n\n"
        
        # Leverage summary
        report += "🚀 Leverage:\n"
        report += f"   🚀 สูง ({len(high_leverage)}): {', '.join(high_leverage)}\n"
        report += f"   ⚖️ ปานกลาง ({len(medium_leverage)}): {', '.join(medium_leverage)}\n"
        report += f"   🛡️ ต่ำ ({len(low_leverage)}): {', '.join(low_leverage)}\n\n"
        
        # Multi-timeframe info
        report += "📊 การวิเคราะห์:\n"
        report += "   • ใช้ข้อมูลจาก 6 Timeframes: 1m, 5m, 15m, 1h, 4h, 1d\n"
        report += "   • คำนวณค่าเฉลี่ยถ่วงน้ำหนัก (ให้น้ำหนักมากกับ Timeframe ที่นานกว่า)\n"
        report += "   • วิเคราะห์ความแข็งแกร่งของเทรนด์จากหลาย Timeframe\n\n"
        
        # Recommendations
        report += "💡 คำแนะนำ:\n"
        if large_orders:
            report += f"   • ใช้ order size ใหญ่กับ: {', '.join(large_orders[:3])}\n"
        if high_leverage:
            report += f"   • ใช้ leverage สูงกับ: {', '.join(high_leverage[:3])}\n"
        if small_orders:
            report += f"   • ระมัดระวังกับ: {', '.join(small_orders[:3])}\n"
        
        return report

    def confirm_signal_across_timeframes(self, signals: Dict[str, str], min_confirm: int = 3) -> str:
        """
        signals: dict เช่น {'1m': 'buy', '5m': 'buy', '15m': 'sell', ...}
        min_confirm: จำนวนไทม์เฟรมขั้นต่ำที่ต้องให้สัญญาณเดียวกัน
        return: 'buy', 'sell', 'hold' หรือ None ถ้าไม่ผ่านเกณฑ์
        """
        if not signals:
            return None
        counter = Counter(signals.values())
        most_common_signal, count = counter.most_common(1)[0]
        if count >= min_confirm:
            return most_common_signal
        return None  # ไม่เปิดออเดอร์

    # ตัวอย่างการใช้งาน (ใน analyze_coin_multi_tf หรือ trading_bot)
    # signals = {'1m': 'buy', '5m': 'buy', '15m': 'sell', '1h': 'buy'}
    # confirmed_signal = self.confirm_signal_across_timeframes(signals, min_confirm=3)
    # if confirmed_signal:
    #     # ดำเนินการเปิดออเดอร์ตาม confirmed_signal
    #     pass 