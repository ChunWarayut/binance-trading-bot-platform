#!/usr/bin/env python3
"""
Test script for enhanced trading strategies
"""

import asyncio
import json
import logging
from binance.client import Client
import pandas as pd
import pandas_ta as ta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyTester:
    def __init__(self):
        self.client = Client("", "")  # No API keys needed for public data
        
    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        df['sma20'] = df.ta.sma(length=25)
        df['sma50'] = df.ta.sma(length=60)
        df['rsi'] = df.ta.rsi(length=28)
        
        macd = df.ta.macd(fast=14, slow=30, signal=12)
        df['macd'] = macd['MACD_14_30_12']
        df['macd_signal'] = macd['MACDs_14_30_12']
        df['macd_hist'] = macd['MACDh_14_30_12']
        
        bb = df.ta.bbands(length=20, std=2)
        df['bb_upper'] = bb['BBU_20_2.0']
        df['bb_middle'] = bb['BBM_20_2.0']
        df['bb_lower'] = bb['BBL_20_2.0']
        
        stoch = df.ta.stoch(high='high', low='low', close='close', k=14, d=3)
        df['stoch_k'] = stoch['STOCHk_14_3_3']
        df['stoch_d'] = stoch['STOCHd_14_3_3']
        
        df['williams_r'] = df.ta.willr(high='high', low='low', close='close', length=14)
        df['volume_sma20'] = df.ta.sma(length=35, close='volume')
        
        # Fill NaN values
        indicator_columns = ['sma20', 'sma50', 'rsi', 'macd', 'macd_signal', 'macd_hist', 
                           'bb_upper', 'bb_middle', 'bb_lower', 'stoch_k', 'stoch_d', 
                           'williams_r', 'volume_sma20']
        
        for col in indicator_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if col in ['rsi', 'stoch_k', 'stoch_d', 'williams_r']:
                    df[col] = df[col].fillna(50)
                else:
                    df[col] = df[col].fillna(0)
        
        return df

    def check_macd_trend_signal(self, df):
        """MACD crossover + SMA trend confirmation"""
        try:
            current_macd = float(df['macd'].iloc[-1])
            current_signal = float(df['macd_signal'].iloc[-1])
            prev_macd = float(df['macd'].iloc[-2])
            prev_signal = float(df['macd_signal'].iloc[-2])
            sma20 = float(df['sma20'].iloc[-1])
            sma50 = float(df['sma50'].iloc[-1])

            bullish = prev_macd <= prev_signal and current_macd > current_signal and sma20 > sma50
            bearish = prev_macd >= prev_signal and current_macd < current_signal and sma20 < sma50

            if bullish:
                return "BUY"
            elif bearish:
                return "SELL"
            return None
        except Exception as e:
            logger.warning(f"Error in MACD Trend signal: {e}")
            return None

    def check_momentum_signal(self, df):
        """Simple price momentum + volume spike + RSI momentum"""
        try:
            current_price = float(df['close'].iloc[-1])
            prev_price = float(df['close'].iloc[-2])
            price_mom = (current_price - prev_price) / prev_price * 100

            current_volume = float(df['volume'].iloc[-1])
            avg_volume = float(df['volume_sma20'].iloc[-1])
            volume_spike = current_volume > avg_volume * 1.3

            current_rsi = float(df['rsi'].iloc[-1])
            prev_rsi = float(df['rsi'].iloc[-2])
            rsi_mom = current_rsi - prev_rsi

            if price_mom > 0.2 and volume_spike and rsi_mom > 0.5:
                return "BUY"
            elif price_mom < -0.2 and volume_spike and rsi_mom < -0.5:
                return "SELL"
            return None
        except Exception as e:
            logger.warning(f"Error in Momentum signal: {e}")
            return None

    def check_volume_profile_signal(self, df):
        """Volume Profile Analysis"""
        try:
            current_volume = float(df['volume'].iloc[-1])
            avg_volume = float(df['volume_sma20'].iloc[-1])
            current_price = float(df['close'].iloc[-1])
            current_rsi = float(df['rsi'].iloc[-1])
            
            volume_ratio = current_volume / avg_volume
            prev_price = float(df['close'].iloc[-2])
            price_change = (current_price - prev_price) / prev_price * 100
            
            if volume_ratio > 1.5:
                if price_change > 1.0 and current_rsi < 70:
                    return "BUY"
                elif price_change < -1.0 and current_rsi > 30:
                    return "SELL"
            
            if volume_ratio > 1.3:
                if price_change < 0.5 and current_rsi < 40:
                    return "BUY"
                elif price_change > 0.5 and current_rsi > 60:
                    return "SELL"
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in Volume Profile signal: {e}")
            return None

    def check_market_structure_signal(self, df):
        """Market Structure Analysis"""
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            current_price = float(close.iloc[-1])
            
            recent_highs = high.tail(20).nlargest(3)
            recent_lows = low.tail(20).nsmallest(3)
            
            resistance = recent_highs.mean()
            support = recent_lows.mean()
            
            distance_to_resistance = (resistance - current_price) / current_price * 100
            distance_to_support = (current_price - support) / current_price * 100
            
            current_rsi = float(df['rsi'].iloc[-1])
            
            if distance_to_resistance < 2.0 and current_rsi > 55:
                return "SELL"
            elif distance_to_support < 2.0 and current_rsi < 45:
                return "BUY"
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in Market Structure signal: {e}")
            return None

    def check_order_flow_signal(self, df):
        """Order Flow Analysis"""
        try:
            open_prices = df['open'].astype(float)
            close_prices = df['close'].astype(float)
            volumes = df['volume'].astype(float)
            
            current_open = float(open_prices.iloc[-1])
            current_close = float(close_prices.iloc[-1])
            current_volume = float(volumes.iloc[-1])
            prev_volume = float(volumes.iloc[-2])
            
            bullish_candle = current_close > current_open
            bearish_candle = current_close < current_open
            volume_increase = current_volume > prev_volume * 1.1
            
            body_size = abs(current_close - current_open)
            avg_body = abs(close_prices - open_prices).tail(10).mean()
            strong_move = body_size > avg_body * 1.3
            
            if bullish_candle and volume_increase and strong_move:
                return "BUY"
            elif bearish_candle and volume_increase and strong_move:
                return "SELL"
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in Order Flow signal: {e}")
            return None

    def check_bollinger_rsi_signal(self, df):
        """Bollinger Bands + RSI combo"""
        try:
            current_rsi = float(df['rsi'].iloc[-1])
            bb_upper = float(df['bb_upper'].iloc[-1])
            bb_lower = float(df['bb_lower'].iloc[-1])
            current_price = float(df['close'].iloc[-1])

            price_upper = current_price >= bb_upper
            price_lower = current_price <= bb_lower

            if price_lower and current_rsi < 30:
                return "BUY"
            elif price_upper and current_rsi > 70:
                return "SELL"
            return None
        except Exception as e:
            logger.warning(f"Error in Bollinger RSI signal: {e}")
            return None

    def check_stochastic_williams_signal(self, df):
        """Stochastic %K + Williams %R combo"""
        try:
            stoch_k = float(df['stoch_k'].iloc[-1])
            will_r = float(df['williams_r'].iloc[-1])

            if stoch_k < 20 and will_r < -80:
                return "BUY"
            elif stoch_k > 80 and will_r > -20:
                return "SELL"
            return None
        except Exception as e:
            logger.warning(f"Error in Stochastic Williams signal: {e}")
            return None

    def check_parabolic_sar_adx_signal(self, df):
        """Parabolic SAR with ADX confirmation (simplified)"""
        try:
            psar_df = ta.psar(df['high'], df['low'], df['close'])
            if psar_df is None or psar_df.empty:
                return None
            df['psar'] = psar_df.iloc[:, -1]
            adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
            if adx_df is None or adx_df.empty:
                return None
            df['adx'] = adx_df['ADX_14']
            df['plus_di'] = adx_df['DMP_14']
            df['minus_di'] = adx_df['DMN_14']

            current_price = float(df['close'].iloc[-1])
            psar = float(df['psar'].iloc[-1])
            adx_val = float(df['adx'].iloc[-1])
            plus_di = float(df['plus_di'].iloc[-1])
            minus_di = float(df['minus_di'].iloc[-1])

            strong_trend = adx_val > 20
            bull = current_price > psar and plus_di > minus_di and strong_trend
            bear = current_price < psar and minus_di > plus_di and strong_trend

            if bull:
                return "BUY"
            elif bear:
                return "SELL"
            return None
        except Exception as e:
            logger.warning(f"Error in Parabolic SAR ADX signal: {e}")
            return None

    def check_chaikin_money_flow_macd_signal(self, df):
        """Chaikin Money Flow with MACD direction (simplified)"""
        try:
            cmf_series = ta.cmf(df['high'], df['low'], df['close'], df['volume'], length=20)
            if cmf_series is None:
                return None
            df['cmf'] = cmf_series

            macd_df = ta.macd(df['close'])
            if macd_df is None or macd_df.empty:
                return None
            df['macd'] = macd_df.iloc[:, 0]
            df['macd_signal'] = macd_df.iloc[:, 1]

            cmf_val = float(df['cmf'].iloc[-1])
            macd_val = float(df['macd'].iloc[-1])
            macd_sig = float(df['macd_signal'].iloc[-1])

            bull = cmf_val > 0 and macd_val > macd_sig
            bear = cmf_val < 0 and macd_val < macd_sig
            if bull:
                return "BUY"
            elif bear:
                return "SELL"
            return None
        except Exception as e:
            logger.warning(f"Error in Chaikin Money Flow MACD signal: {e}")
            return None

    def get_weighted_signal(self, signals_dict):
        """Get weighted signal"""
        try:
            buy_signals = []
            sell_signals = []
            
            signal_weights = {
                'MACD Trend': 0.15,
                'Bollinger RSI': 0.12,
                'Stochastic Williams': 0.10,
                'Parabolic SAR ADX': 0.14,
                'Chaikin Money Flow MACD': 0.10,
                'Momentum': 0.08,
                'Volume Profile': 0.13,
                'Market Structure': 0.11,
                'Order Flow': 0.11
            }
            
            for signal_name, signal_value in signals_dict.items():
                if signal_value == "BUY":
                    weight = signal_weights.get(signal_name, 0.05)
                    buy_signals.append(weight)
                elif signal_value == "SELL":
                    weight = signal_weights.get(signal_name, 0.05)
                    sell_signals.append(weight)
            
            buy_score = sum(buy_signals)
            sell_score = sum(sell_signals)
            
            if buy_score > 0.3 and buy_score > sell_score * 1.5:
                return ("BUY", buy_score)
            elif sell_score > 0.3 and sell_score > buy_score * 1.5:
                return ("SELL", sell_score)
            
            return (None, 0)
            
        except Exception as e:
            logger.warning(f"Error in weighted signal calculation: {e}")
            return (None, 0)

    async def test_strategies(self, symbol="BTCUSDT"):
        """Test enhanced strategies on a symbol"""
        try:
            logger.info(f"🧪 Testing enhanced strategies for {symbol}")
            
            # Get recent data
            klines = self.client.futures_klines(
                symbol=symbol,
                interval='1h',   # 1-hour candles for noise reduction
                limit=1000       # up to ~42 days
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            df['open'] = pd.to_numeric(df['open'])
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Test advanced strategies
            signals = {}
            
            # Test MACD Trend
            macd_signal = self.check_macd_trend_signal(df)
            signals['MACD Trend'] = macd_signal
            logger.info(f"📈 MACD Trend Signal: {macd_signal}")

            # Test Momentum
            mom_signal = self.check_momentum_signal(df)
            signals['Momentum'] = mom_signal
            logger.info(f"⚡ Momentum Signal: {mom_signal}")

            # Test Volume Profile
            volume_signal = self.check_volume_profile_signal(df)
            signals['Volume Profile'] = volume_signal
            logger.info(f"📊 Volume Profile Signal: {volume_signal}")
            
            # Test Market Structure
            structure_signal = self.check_market_structure_signal(df)
            signals['Market Structure'] = structure_signal
            logger.info(f"🏗️ Market Structure Signal: {structure_signal}")
            
            # Test Order Flow
            flow_signal = self.check_order_flow_signal(df)
            signals['Order Flow'] = flow_signal
            logger.info(f"🌊 Order Flow Signal: {flow_signal}")

            # Test Bollinger RSI
            bb_signal = self.check_bollinger_rsi_signal(df)
            signals['Bollinger RSI'] = bb_signal
            logger.info(f"🎯 Bollinger RSI Signal: {bb_signal}")

            # Test Stochastic Williams
            sw_signal = self.check_stochastic_williams_signal(df)
            signals['Stochastic Williams'] = sw_signal
            logger.info(f"🎯 Stochastic Williams Signal: {sw_signal}")

            # Test Parabolic SAR ADX
            psar_signal = self.check_parabolic_sar_adx_signal(df)
            signals['Parabolic SAR ADX'] = psar_signal
            logger.info(f"📐 Parabolic SAR ADX Signal: {psar_signal}")

            # Test Chaikin Money Flow MACD
            cmf_signal = self.check_chaikin_money_flow_macd_signal(df)
            signals['Chaikin Money Flow MACD'] = cmf_signal
            logger.info(f"💰 CMF MACD Signal: {cmf_signal}")
            
            # Get weighted signal
            weighted_signal, confidence = self.get_weighted_signal(signals)
            logger.info(f"🎯 Weighted Signal: {weighted_signal} (Confidence: {confidence:.2f})")
            
            # Summary
            logger.info(f"\n📋 Strategy Test Summary for {symbol}:")
            logger.info(f"MACD Trend: {macd_signal}")
            logger.info(f"Momentum: {mom_signal}")
            logger.info(f"Volume Profile: {volume_signal}")
            logger.info(f"Market Structure: {structure_signal}")
            logger.info(f"Order Flow: {flow_signal}")
            logger.info(f"Bollinger RSI: {bb_signal}")
            logger.info(f"Stochastic Williams: {sw_signal}")
            logger.info(f"Parabolic SAR ADX: {psar_signal}")
            logger.info(f"Chaikin Money Flow MACD: {cmf_signal}")
            logger.info(f"Weighted Signal: {weighted_signal} (Confidence: {confidence:.2f})")
            
            return {
                'symbol': symbol,
                'signals': signals,
                'weighted_signal': weighted_signal,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Error testing strategies: {e}")
            return None

async def main():
    """Main test function"""
    tester = StrategyTester()
    
    # Test on multiple symbols
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    
    results = []
    for symbol in symbols:
        result = await tester.test_strategies(symbol)
        if result:
            results.append(result)
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    logger.info(f"\n🎯 Overall Test Results:")
    for result in results:
        logger.info(f"{result['symbol']}: {result['weighted_signal']} (Confidence: {result['confidence']:.2f})")

if __name__ == "__main__":
    asyncio.run(main()) 