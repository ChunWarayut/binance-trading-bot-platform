from binance.client import Client
from binance.enums import *
import pandas as pd
import numpy as np
from loguru import logger
import config
import asyncio
from notifications import NotificationSystem
import time
import pandas_ta as ta
from binance.exceptions import BinanceAPIException, BinanceOrderException
import json
import os
from coin_analysis import CoinAnalyzer
from typing import Dict
from binance.enums import SIDE_BUY, SIDE_SELL, FUTURE_ORDER_TYPE_MARKET
import sys
from datetime import datetime

class TradingBot:
    def __init__(self):
        self.client = Client(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
        self.notification = NotificationSystem()
        self.active_trades = {}
        self.setup_logging()
        self.last_heartbeat = time.time()
        self.account_balance = None
        self.last_rsi = {}
        self.coin_analyzer = CoinAnalyzer(self.client)
        self.coin_analyses = {}
        self.last_analysis_time = 0
        self.analysis_interval = 3600  # 1 hour
        
        # Risk Management Variables
        self.daily_pnl = 0.0
        self.daily_trades_count = 0
        self.last_trade_date = None
        self.circuit_breaker_triggered = False
        self.initial_balance = None
        
        # Notification Rate Limiting
        self.last_notification_time = {}  # เก็บเวลาแจ้งเตือนล่าสุดสำหรับแต่ละเหรียญ
        self.notification_interval = 1800  # ส่งแจ้งเตือน RSI ทุก 30 นาที

    def setup_logging(self):
        """Configure Loguru for clear, color-coded console logs and tidy file logs."""
        # Remove default handler to avoid duplicate outputs
        logger.remove()

        # Console – colorized for quick scan
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "{message}"
        )

        # File – plain text, same columns (without color codes)
        file_format = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"

        # Add handlers
        logger.add(sys.stdout, format=console_format, colorize=True, level=config.LOG_LEVEL)
        logger.add(
            config.LOG_FILE,
            format=file_format,
            rotation="5 MB",
            retention="7 days",
            encoding="utf-8",
            level=config.LOG_LEVEL,
        )

    async def safe_api_call(self, api_func, *args, max_retries=5, delay=0.5, **kwargs):
        for attempt in range(max_retries):
            try:
                result = api_func(*args, **kwargs)
                await asyncio.sleep(delay)
                return result
            except BinanceAPIException as e:
                if e.code in [-1003, -1015]:  # Rate limit
                    logger.warning(f"Rate limit hit. Retrying in {delay} seconds... (Attempt {attempt+1})")
                    await asyncio.sleep(delay)
                    delay *= 2
                elif e.code == -2015:  # Invalid API-key, IP, or permissions
                    logger.error("❌ Invalid API key or permissions.")
                    await self.notification.notify("❌ Invalid API key or permissions. Please check your API key settings.")
                    raise
                elif e.code == -2019:  # Margin is insufficient
                    logger.error("❌ Margin is insufficient.")
                    await self.notification.notify("❌ Margin is insufficient. Please check your balance.")
                    raise
                else:
                    logger.error(f"BinanceAPIException: {e} (code: {e.code})")
                    await self.notification.notify(f"BinanceAPIException: {e} (code: {e.code})")
                    raise
            except BinanceOrderException as e:
                logger.error(f"BinanceOrderException: {e}")
                await self.notification.notify(f"BinanceOrderException: {e}")
                raise
            except asyncio.TimeoutError:
                logger.error("⏰ API call timed out. Retrying...")
                await asyncio.sleep(delay)
            except ConnectionError:
                logger.error("🌐 Network error. Retrying...")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await self.notification.notify(f"Unexpected error: {e}")
                raise
        logger.error("Max retries reached for API call.")
        await self.notification.notify("Max retries reached for API call.")
        raise Exception("Max retries reached for API call.")

    async def initialize(self):
        for symbol in config.TRADING_PAIRS:
            try:
                # First check if the symbol exists and is available for futures trading
                try:
                    exchange_info = await self.safe_api_call(self.client.futures_exchange_info)
                    symbol_info = None
                    for s in exchange_info['symbols']:
                        if s['symbol'] == symbol and s['status'] == 'TRADING':
                            symbol_info = s
                            break
                    
                    if not symbol_info:
                        logger.warning(f"Symbol {symbol} is not available for futures trading or not in TRADING status")
                        await self.notification.notify(f"⚠️ Symbol {symbol} not available for futures trading")
                        continue
                        
                except Exception as e:
                    logger.warning(f"Could not verify symbol {symbol} availability: {e}")
                    # Continue with leverage setting attempt
                
                # Set leverage
                await self.safe_api_call(self.client.futures_change_leverage, symbol=symbol, leverage=config.LEVERAGE)
                logger.info(f"Set leverage for {symbol} to {config.LEVERAGE}x")
                
                # Get current price
                try:
                    ticker = await self.safe_api_call(self.client.futures_symbol_ticker, symbol=symbol)
                    current_price = ticker['price']
                    logger.info(f"Current price for {symbol}: {current_price}")
                    
                    # ส่งแจ้งเตือนการ initialize แค่เมื่อ bot เริ่มครั้งแรก
                    if symbol not in self.last_notification_time:
                        await self.notification.notify(
                            f"✅ Initialized {symbol}\n"
                            f"Leverage: {config.LEVERAGE}x\n"
                            f"Current Price: {current_price}"
                        )
                except Exception as price_error:
                    logger.error(f"Failed to get price for {symbol}: {str(price_error)}")
                    await self.notification.notify(
                        f"⚠️ Initialized {symbol} with leverage {config.LEVERAGE}x\n"
                        f"⚠️ Could not get current price: {str(price_error)}"
                    )
                    
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg or "symbol" in error_msg.lower():
                    logger.warning(f"Symbol {symbol} may not be available for futures trading: {error_msg}")
                    await self.notification.notify(f"⚠️ Symbol {symbol} not available: {error_msg}")
                else:
                    logger.error(f"Failed to set leverage for {symbol}: {error_msg}")
                    await self.notification.notify(f"❌ Failed to initialize {symbol}: {error_msg}")

    def send_heartbeat(self):
        current_time = time.time()
        if current_time - self.last_heartbeat >= 60:  # Send heartbeat every minute
            logger.info("Bot is running and monitoring markets...")
            self.last_heartbeat = current_time

    async def send_technical_indicators(self, symbol, current_price, current_rsi):
        # Rate limiting: ส่งแจ้งเตือนเฉพาะเมื่อ:
        # 1. ยังไม่เคยส่งสำหรับเหรียญนี้ หรือ
        # 2. เวลาผ่านไปแล้วมากกว่า notification_interval หรือ
        # 3. RSI เข้าสู่ oversold (<30) หรือ overbought (>70) zones
        current_time = time.time()
        last_sent = self.last_notification_time.get(symbol, 0)
        time_elapsed = current_time - last_sent
        
        # เงื่อนไขสำหรับการส่งแจ้งเตือน: ส่งเฉพาะ oversold/overbought หรือเวลาผ่านไปนานแล้ว
        is_significant_rsi = current_rsi <= 30 or current_rsi >= 70
        should_notify = (
            is_significant_rsi or  # RSI oversold/overbought (สำคัญ)
            (time_elapsed >= self.notification_interval and symbol in self.last_notification_time)  # เวลาผ่านไป 30 นาที (เฉพาะถ้าเคยส่งแล้ว)
        )
        
        if should_notify:
            # เพิ่มสัญลักษณ์เตือนสำหรับ oversold/overbought
            indicator = ""
            if current_rsi <= 30:
                indicator = " 🟢 OVERSOLD"
            elif current_rsi >= 70:
                indicator = " 🔴 OVERBOUGHT"
            
            await self.notification.notify(
                f"📊 RSI Indicator for {symbol}{indicator}\n"
                f"Price: {current_price:.2f}\n"
                f"RSI: {current_rsi:.2f}"
            )
            
            # อัปเดตเวลาแจ้งเตือนล่าสุด
            self.last_notification_time[symbol] = current_time

    def calculate_indicators(self, df):
        # Calculate SMA with longer periods for smoother signals
        df['sma20'] = df.ta.sma(length=25)  # Changed from 20 to 25
        df['sma50'] = df.ta.sma(length=60)  # Changed from 50 to 60
        
        # Calculate RSI with longer period for smoother signals
        df['rsi'] = df.ta.rsi(length=28)
        
        # Calculate MACD with more relaxed parameters
        macd = df.ta.macd(
            fast=14,  # Changed from 12 to 14
            slow=30,  # Changed from 26 to 30
            signal=12  # Changed from 9 to 12
        )
        df['macd'] = macd['MACD_14_30_12']
        df['macd_signal'] = macd['MACDs_14_30_12']
        df['macd_hist'] = macd['MACDh_14_30_12']
        
        # Calculate Bollinger Bands
        bb = df.ta.bbands(length=20, std=2)
        df['bb_upper'] = bb['BBU_20_2.0']
        df['bb_middle'] = bb['BBM_20_2.0']
        df['bb_lower'] = bb['BBL_20_2.0']
        
        # Calculate Stochastic Oscillator
        stoch = df.ta.stoch(high='high', low='low', close='close', k=14, d=3)
        df['stoch_k'] = stoch['STOCHk_14_3_3']
        df['stoch_d'] = stoch['STOCHd_14_3_3']
        
        # Calculate Williams %R
        df['williams_r'] = df.ta.willr(high='high', low='low', close='close', length=14)
        
        # Calculate Volume SMA with longer period
        df['volume_sma20'] = df.ta.sma(length=35, close='volume')  # Changed from 30 to 35
        
        # Ensure all indicator columns are numeric and handle NaN values
        indicator_columns = ['sma20', 'sma50', 'rsi', 'macd', 'macd_signal', 'macd_hist', 
                           'bb_upper', 'bb_middle', 'bb_lower', 'stoch_k', 'stoch_d', 
                           'williams_r', 'volume_sma20']
        
        for col in indicator_columns:
            if col in df.columns:
                # Convert to numeric, coercing errors to NaN
                df[col] = pd.to_numeric(df[col], errors='coerce')
                # Fill NaN values with 0 or appropriate default
                if col in ['rsi', 'stoch_k', 'stoch_d', 'williams_r']:
                    df[col] = df[col].fillna(50)  # Neutral values for oscillators
                else:
                    df[col] = df[col].fillna(0)
        
        return df

    def check_macd_trend_signal(self, df):
        """Check MACD + Trend signal"""
        try:
            current_macd = float(df['macd'].iloc[-1])
            current_signal = float(df['macd_signal'].iloc[-1])
            prev_macd = float(df['macd'].iloc[-2])
            prev_signal = float(df['macd_signal'].iloc[-2])
            
            # Trend direction
            sma20 = float(df['sma20'].iloc[-1])
            sma50 = float(df['sma50'].iloc[-1])
            trend_up = sma20 > sma50
            
            # MACD bullish crossover
            bullish_crossover = prev_macd <= prev_signal and current_macd > current_signal
            # MACD bearish crossover
            bearish_crossover = prev_macd >= prev_signal and current_macd < current_signal
            
            if bullish_crossover and trend_up:
                return "BUY"
            elif bearish_crossover and not trend_up:
                return "SELL"
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in MACD trend signal calculation: {e}")
            return None

    def check_bollinger_rsi_signal(self, df, current_price):
        """Check Bollinger Bands + RSI signal"""
        try:
            current_rsi = float(df['rsi'].iloc[-1])
            bb_upper = float(df['bb_upper'].iloc[-1])
            bb_lower = float(df['bb_lower'].iloc[-1])
            
            # Price at Bollinger Bands
            price_at_upper = current_price >= bb_upper
            price_at_lower = current_price <= bb_lower
            
            # RSI conditions
            rsi_oversold = current_rsi < 30
            rsi_overbought = current_rsi > 70
            
            if price_at_lower and rsi_oversold:
                return "BUY"
            elif price_at_upper and rsi_overbought:
                return "SELL"
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Bollinger RSI signal calculation: {e}")
            return None

    def check_stochastic_williams_signal(self, df):
        """Check Stochastic + Williams %R signal"""
        try:
            current_stoch_k = float(df['stoch_k'].iloc[-1])
            current_williams_r = float(df['williams_r'].iloc[-1])
            
            # Stochastic conditions
            stoch_oversold = current_stoch_k < 20
            stoch_overbought = current_stoch_k > 80
            
            # Williams %R conditions
            williams_oversold = current_williams_r < -80
            williams_overbought = current_williams_r > -20
            
            if stoch_oversold and williams_oversold:
                return "BUY"
            elif stoch_overbought and williams_overbought:
                return "SELL"
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Stochastic Williams signal calculation: {e}")
            return None

    def check_momentum_signal(self, df):
        """Improved momentum signal – returns BUY / SELL / None
        Conditions (example):
        • Price momentum > 0.3 % and volume spike and positive RSI momentum → BUY
        • Price momentum < −0.3 % and volume spike and negative RSI momentum → SELL
        Otherwise → None
        """
        try:
            current_price = float(df['close'].iloc[-1])
            prev_price = float(df['close'].iloc[-2])
            price_momentum = (current_price - prev_price) / prev_price * 100

            current_volume = float(df['volume'].iloc[-1])
            avg_volume = float(df['volume_sma20'].iloc[-1])
            volume_spike = current_volume > avg_volume * 1.5

            current_rsi = float(df['rsi'].iloc[-1])
            prev_rsi = float(df['rsi'].iloc[-2])
            rsi_momentum = current_rsi - prev_rsi

            # Thresholds – you can fine-tune in config later
            pct_threshold = 0.3  # 0.3 % intrabar move
            rsi_threshold = 1.0

            if price_momentum > pct_threshold and volume_spike and rsi_momentum > rsi_threshold:
                return "BUY"
            elif price_momentum < -pct_threshold and volume_spike and rsi_momentum < -rsi_threshold:
                return "SELL"
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in momentum signal calculation: {e}")
            return None

    def check_fibonacci_rsi_signal(self, df):
        """Check Fibonacci RSI signal"""
        try:
            current_rsi = float(df['rsi'].iloc[-1])
            prev_rsi = float(df['rsi'].iloc[-2])
            
            # Fibonacci RSI conditions
            rsi_oversold = current_rsi < 30
            rsi_overbought = current_rsi > 70
            
            if rsi_oversold:
                return "BUY"
            elif rsi_overbought:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Fibonacci RSI signal calculation: {e}")
            return None

    def check_parabolic_sar_adx_signal(self, df):
        """Check Parabolic SAR + ADX signal"""
        try:
            # Calculate Parabolic SAR manually
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            
            # Manual Parabolic SAR calculation
            af = 0.02  # Acceleration factor
            max_af = 0.2  # Maximum acceleration factor
            sar = []
            ep = []  # Extreme point
            af_list = []
            
            # Initialize
            sar.append(low.iloc[0])
            ep.append(high.iloc[0])
            af_list.append(af)
            
            # Calculate SAR for each period
            for i in range(1, len(df)):
                if close.iloc[i] > ep[i-1]:
                    # Bullish trend
                    sar.append(sar[i-1])
                    ep.append(max(high.iloc[i], ep[i-1]))
                    af_list.append(min(af_list[i-1] + af, max_af))
                else:
                    # Bearish trend
                    sar.append(sar[i-1])
                    ep.append(min(low.iloc[i], ep[i-1]))
                    af_list.append(min(af_list[i-1] + af, max_af))
                
                # Adjust SAR
                if close.iloc[i] > ep[i-1]:
                    sar[i] = sar[i] + af_list[i] * (ep[i] - sar[i])
                else:
                    sar[i] = sar[i] + af_list[i] * (ep[i] - sar[i])
                
                # Ensure SAR doesn't go beyond previous high/low
                if i > 0:
                    if close.iloc[i] > ep[i-1]:
                        sar[i] = min(sar[i], low.iloc[i-1])
                    else:
                        sar[i] = max(sar[i], high.iloc[i-1])
            
            df['sar'] = sar
            
            # Calculate ADX
            adx = ta.adx(high=high, low=low, close=close, length=14)
            df['adx'] = adx['ADX_14']
            df['plus_di'] = adx['DMP_14']
            df['minus_di'] = adx['DMN_14']
            
            current_price = float(close.iloc[-1])
            current_sar = float(sar[-1])
            current_adx = float(df['adx'].iloc[-1])
            current_plus_di = float(df['plus_di'].iloc[-1])
            current_minus_di = float(df['minus_di'].iloc[-1])
            
            # Strong trend condition
            strong_trend = current_adx > 25
            
            # Parabolic SAR signals
            sar_bullish = current_price > current_sar
            sar_bearish = current_price < current_sar
            
            # DI signals
            di_bullish = current_plus_di > current_minus_di
            di_bearish = current_plus_di < current_minus_di
            
            if sar_bullish and di_bullish and strong_trend:
                return "BUY"
            elif sar_bearish and di_bearish and strong_trend:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Parabolic SAR ADX signal calculation: {e}")
            return None

    def check_keltner_cci_signal(self, df):
        """Check Keltner Channel + CCI signal"""
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            
            # Manual Keltner Channels calculation
            def calculate_keltner_channels(high_prices, low_prices, close_prices, length=20, multiplier=2):
                # Calculate EMA
                ema = close_prices.ewm(span=length).mean()
                
                # Calculate ATR
                tr1 = high_prices - low_prices
                tr2 = abs(high_prices - close_prices.shift(1))
                tr3 = abs(low_prices - close_prices.shift(1))
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr = tr.ewm(span=length).mean()
                
                # Calculate Keltner Channels
                upper = ema + (multiplier * atr)
                middle = ema
                lower = ema - (multiplier * atr)
                
                return upper, middle, lower
            
            kc_upper, kc_middle, kc_lower = calculate_keltner_channels(high, low, close, 20, 2)
            df['kc_upper'] = kc_upper
            df['kc_middle'] = kc_middle
            df['kc_lower'] = kc_lower
            
            # Calculate CCI
            cci = ta.cci(high=high, low=low, close=close, length=20)
            df['cci'] = cci
            
            current_price = float(close.iloc[-1])
            kc_upper = float(df['kc_upper'].iloc[-1])
            kc_lower = float(df['kc_lower'].iloc[-1])
            current_cci = float(df['cci'].iloc[-1])
            
            # CCI conditions
            cci_oversold = current_cci < -100
            cci_overbought = current_cci > 100
            
            # Keltner Channel conditions
            price_at_upper = current_price >= kc_upper
            price_at_lower = current_price <= kc_lower
            
            if price_at_lower and cci_oversold:
                return "BUY"
            elif price_at_upper and cci_overbought:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Keltner CCI signal calculation: {e}")
            return None

    def check_pivot_points_rsi_signal(self, df):
        """Check Pivot Points + RSI signal"""
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            
            # Calculate Pivot Points (using previous day's data)
            prev_high = float(high.iloc[-2])
            prev_low = float(low.iloc[-2])
            prev_close = float(close.iloc[-2])
            
            # Pivot Point calculation
            pivot = (prev_high + prev_low + prev_close) / 3
            r1 = 2 * pivot - prev_low
            s1 = 2 * pivot - prev_high
            r2 = pivot + (prev_high - prev_low)
            s2 = pivot - (prev_high - prev_low)
            
            current_price = float(close.iloc[-1])
            current_rsi = float(df['rsi'].iloc[-1])
            
            # Support and resistance levels
            near_support = current_price <= s1 * 1.01  # Within 1% of support
            near_resistance = current_price >= r1 * 0.99  # Within 1% of resistance
            
            # RSI conditions
            rsi_oversold = current_rsi < 30
            rsi_overbought = current_rsi > 70
            
            if near_support and rsi_oversold:
                return "BUY"
            elif near_resistance and rsi_overbought:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Pivot Points RSI signal calculation: {e}")
            return None

    def check_money_flow_volume_signal(self, df):
        """Check Money Flow Index (MFI) + Volume signal"""
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            volume = df['volume'].astype(float)
            
            # Manual MFI calculation
            def calculate_mfi(high_prices, low_prices, close_prices, volume_prices, length=14):
                mfi_values = []
                for i in range(len(close_prices)):
                    if i < length - 1:
                        mfi_values.append(50)  # Neutral value
                    else:
                        positive_money_flow = 0
                        negative_money_flow = 0
                        
                        for j in range(length):
                            idx = i - j
                            if idx > 0:  # Need previous price for comparison
                                current_high = high_prices[idx]
                                current_low = low_prices[idx]
                                current_close = close_prices[idx]
                                current_volume = volume_prices[idx]
                                prev_high = high_prices[idx-1]
                                prev_low = low_prices[idx-1]
                                prev_close = close_prices[idx-1]
                                
                                # Calculate typical price
                                typical_price = (current_high + current_low + current_close) / 3
                                prev_typical_price = (prev_high + prev_low + prev_close) / 3
                                
                                # Calculate money flow
                                if typical_price > prev_typical_price:
                                    positive_money_flow += typical_price * current_volume
                                elif typical_price < prev_typical_price:
                                    negative_money_flow += typical_price * current_volume
                        
                        if negative_money_flow != 0:
                            money_ratio = positive_money_flow / negative_money_flow
                            mfi = 100 - (100 / (1 + money_ratio))
                        else:
                            mfi = 100
                        
                        mfi_values.append(mfi)
                return mfi_values
            
            mfi_values = calculate_mfi(high.values, low.values, close.values, volume.values, 14)
            df['mfi'] = mfi_values
            
            current_mfi = float(df['mfi'].iloc[-1])
            current_volume = float(volume.iloc[-1])
            avg_volume = float(df['volume_sma20'].iloc[-1])
            
            # MFI conditions
            mfi_oversold = current_mfi < 20
            mfi_overbought = current_mfi > 80
            
            # Volume conditions
            high_volume = current_volume > avg_volume * 1.5
            
            if mfi_oversold and high_volume:
                return "BUY"
            elif mfi_overbought and high_volume:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Money Flow Volume signal calculation: {e}")
            return None

    def check_atr_moving_average_signal(self, df):
        """Check Average True Range (ATR) + Moving Average signal"""
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            
            # Calculate ATR
            atr = ta.atr(high=high, low=low, close=close, length=14)
            df['atr'] = atr
            
            # Calculate additional moving averages
            df['sma10'] = df.ta.sma(length=10)
            df['sma30'] = df.ta.sma(length=30)
            
            current_price = float(close.iloc[-1])
            current_atr = float(df['atr'].iloc[-1])
            sma10 = float(df['sma10'].iloc[-1])
            sma30 = float(df['sma30'].iloc[-1])
            
            # Volatility condition
            high_volatility = current_atr > df['atr'].rolling(window=20).mean().iloc[-1]
            
            # Moving average conditions
            ma_bullish = sma10 > sma30 and current_price > sma10
            ma_bearish = sma10 < sma30 and current_price < sma10
            
            if ma_bullish and high_volatility:
                return "BUY"
            elif ma_bearish and high_volatility:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in ATR Moving Average signal calculation: {e}")
            return None

    def check_rvi_stochastic_signal(self, df):
        """Check Relative Vigor Index (RVI) + Stochastic signal"""
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            
            # Manual RVI calculation
            def calculate_rvi(close_prices, length=14):
                rvi_values = []
                for i in range(len(close_prices)):
                    if i < length - 1:
                        rvi_values.append(0)
                    else:
                        # Calculate numerator (close - open) for the period
                        numerator = 0
                        denominator = 0
                        for j in range(length):
                            idx = i - j
                            if idx >= 0:
                                # Use close as approximation for open
                                open_price = close_prices[idx-1] if idx > 0 else close_prices[idx]
                                close_price = close_prices[idx]
                                high_price = high.iloc[idx]
                                low_price = low.iloc[idx]
                                
                                numerator += (close_price - open_price)
                                denominator += (high_price - low_price)
                        
                        if denominator != 0:
                            rvi_values.append(numerator / denominator)
                        else:
                            rvi_values.append(0)
                return rvi_values
            
            rvi_values = calculate_rvi(close.values, 14)
            df['rvi'] = rvi_values
            
            current_rvi = float(df['rvi'].iloc[-1])
            prev_rvi = float(df['rvi'].iloc[-2])
            current_stoch_k = float(df['stoch_k'].iloc[-1])
            current_stoch_d = float(df['stoch_d'].iloc[-1])
            
            # RVI momentum
            rvi_momentum = current_rvi - prev_rvi
            
            # Stochastic conditions
            stoch_oversold = current_stoch_k < 20 and current_stoch_d < 20
            stoch_overbought = current_stoch_k > 80 and current_stoch_d > 80
            
            # RVI conditions
            rvi_bullish = rvi_momentum > 0 and current_rvi > 0
            rvi_bearish = rvi_momentum < 0 and current_rvi < 0
            
            if rvi_bullish and stoch_oversold:
                return "BUY"
            elif rvi_bearish and stoch_overbought:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in RVI Stochastic signal calculation: {e}")
            return None

    def check_cci_bollinger_signal(self, df):
        """Check Commodity Channel Index (CCI) + Bollinger Bands signal"""
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            
            # Calculate CCI
            cci = ta.cci(high=high, low=low, close=close, length=20)
            df['cci'] = cci
            
            current_price = float(close.iloc[-1])
            current_cci = float(df['cci'].iloc[-1])
            bb_upper = float(df['bb_upper'].iloc[-1])
            bb_lower = float(df['bb_lower'].iloc[-1])
            
            # CCI extreme conditions
            cci_extreme_oversold = current_cci < -200
            cci_extreme_overbought = current_cci > 200
            
            # Bollinger Bands conditions
            price_at_upper = current_price >= bb_upper
            price_at_lower = current_price <= bb_lower
            
            if price_at_lower and cci_extreme_oversold:
                return "BUY"
            elif price_at_upper and cci_extreme_overbought:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in CCI Bollinger signal calculation: {e}")
            return None

    def check_obv_price_action_signal(self, df):
        """Check On-Balance Volume (OBV) + Price Action signal"""
        try:
            close = df['close'].astype(float)
            volume = df['volume'].astype(float)
            
            # Manual OBV calculation
            obv = [volume.iloc[0]]
            for i in range(1, len(close)):
                if close.iloc[i] > close.iloc[i-1]:
                    obv.append(obv[-1] + volume.iloc[i])
                elif close.iloc[i] < close.iloc[i-1]:
                    obv.append(obv[-1] - volume.iloc[i])
                else:
                    obv.append(obv[-1])
            df['obv'] = obv
            
            # Calculate OBV moving average
            df['obv_sma'] = pd.Series(obv).rolling(window=20).mean()
            
            current_price = float(close.iloc[-1])
            prev_price = float(close.iloc[-2])
            current_obv = float(df['obv'].iloc[-1])
            obv_sma = float(df['obv_sma'].iloc[-1])
            
            # Price action
            price_up = current_price > prev_price
            price_down = current_price < prev_price
            
            # OBV conditions
            obv_bullish = current_obv > obv_sma
            obv_bearish = current_obv < obv_sma
            
            # Volume confirmation
            current_volume = float(volume.iloc[-1])
            avg_volume = float(df['volume_sma20'].iloc[-1])
            volume_confirmation = current_volume > avg_volume
            
            if price_up and obv_bullish and volume_confirmation:
                return "BUY"
            elif price_down and obv_bearish and volume_confirmation:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in OBV Price Action signal calculation: {e}")
            return None

    def check_chaikin_money_flow_macd_signal(self, df):
        """Check Chaikin Money Flow (CMF) + MACD signal"""
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            volume = df['volume'].astype(float)
            
            # Manual CMF calculation
            def calculate_cmf(high_prices, low_prices, close_prices, volume_prices, length=20):
                cmf_values = []
                for i in range(len(close_prices)):
                    if i < length - 1:
                        cmf_values.append(0)
                    else:
                        money_flow_volume = 0
                        total_volume = 0
                        for j in range(length):
                            idx = i - j
                            if idx >= 0:
                                high_price = high_prices[idx]
                                low_price = low_prices[idx]
                                close_price = close_prices[idx]
                                vol = volume_prices[idx]
                                
                                # Money Flow Multiplier
                                if high_price != low_price:
                                    mfm = ((close_price - low_price) - (high_price - close_price)) / (high_price - low_price)
                                else:
                                    mfm = 0
                                
                                # Money Flow Volume
                                mfv = mfm * vol
                                money_flow_volume += mfv
                                total_volume += vol
                        
                        if total_volume != 0:
                            cmf_values.append(money_flow_volume / total_volume)
                        else:
                            cmf_values.append(0)
                return cmf_values
            
            cmf_values = calculate_cmf(high.values, low.values, close.values, volume.values, 20)
            df['cmf'] = cmf_values
            
            current_cmf = float(df['cmf'].iloc[-1])
            current_macd = float(df['macd'].iloc[-1])
            current_macd_signal = float(df['macd_signal'].iloc[-1])
            
            # CMF conditions
            cmf_bullish = current_cmf > 0.1
            cmf_bearish = current_cmf < -0.1
            
            # MACD conditions
            macd_bullish = current_macd > current_macd_signal
            macd_bearish = current_macd < current_macd_signal
            
            if cmf_bullish and macd_bullish:
                return "BUY"
            elif cmf_bearish and macd_bearish:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Chaikin Money Flow MACD signal calculation: {e}")
            return None

    def check_roc_moving_average_crossover_signal(self, df):
        """Check Rate of Change (ROC) + Moving Average Crossover signal"""
        try:
            close = df['close'].astype(float)
            
            # Calculate ROC
            roc = ta.roc(close=close, length=10)
            df['roc'] = roc
            
            # Calculate additional moving averages for crossover
            df['ema5'] = df.ta.ema(length=5)
            df['ema15'] = df.ta.ema(length=15)
            
            current_roc = float(df['roc'].iloc[-1])
            prev_roc = float(df['roc'].iloc[-2])
            ema5 = float(df['ema5'].iloc[-1])
            ema15 = float(df['ema15'].iloc[-1])
            prev_ema5 = float(df['ema5'].iloc[-2])
            prev_ema15 = float(df['ema15'].iloc[-2])
            
            # ROC momentum
            roc_momentum = current_roc - prev_roc
            
            # Moving average crossover
            ma_bullish_cross = prev_ema5 <= prev_ema15 and ema5 > ema15
            ma_bearish_cross = prev_ema5 >= prev_ema15 and ema5 < ema15
            
            # ROC conditions
            roc_bullish = roc_momentum > 0 and current_roc > 0
            roc_bearish = roc_momentum < 0 and current_roc < 0
            
            if roc_bullish and ma_bullish_cross:
                return "BUY"
            elif roc_bearish and ma_bearish_cross:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in ROC Moving Average Crossover signal calculation: {e}")
            return None

    def check_emergency_signal(self, df):
        """Emergency Signal - Quick entry when 2 original strategies agree"""
        try:
            # Get signals from original strategies only
            macd_signal = self.check_macd_trend_signal(df)
            bb_rsi_signal = self.check_bollinger_rsi_signal(df, float(df['close'].iloc[-1]))
            stoch_williams_signal = self.check_stochastic_williams_signal(df)
            
            # Count original signals
            original_buy_signals = sum([1 for signal in [macd_signal, bb_rsi_signal, stoch_williams_signal] if signal == "BUY"])
            original_sell_signals = sum([1 for signal in [macd_signal, bb_rsi_signal, stoch_williams_signal] if signal == "SELL"])
            
            # Emergency conditions: 2 out of 3 original strategies agree
            if original_buy_signals >= 2:
                return "BUY"
            elif original_sell_signals >= 2:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Emergency signal calculation: {e}")
            return None

    def check_strong_trend_signal(self, df):
        """Strong Trend Signal - For markets with strong momentum"""
        try:
            close = df['close'].astype(float)
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            volume = df['volume'].astype(float)
            
            # Calculate trend strength indicators
            # 1. Price momentum (last 3 periods)
            price_momentum_3 = ((close.iloc[-1] - close.iloc[-4]) / close.iloc[-4]) * 100
            
            # 2. Volume trend (last 5 periods)
            recent_volume = volume.iloc[-5:].mean()
            avg_volume = volume.iloc[-20:].mean()
            volume_trend = recent_volume / avg_volume if avg_volume > 0 else 1.0
            
            # 3. Price range expansion
            recent_range = (high.iloc[-5:].max() - low.iloc[-5:].min()) / close.iloc[-5:].mean() * 100
            avg_range = (high.iloc[-20:].max() - low.iloc[-20:].min()) / close.iloc[-20:].mean() * 100
            range_expansion = recent_range / avg_range if avg_range > 0 else 1.0
            
            # 4. RSI momentum
            current_rsi = float(df['rsi'].iloc[-1])
            prev_rsi = float(df['rsi'].iloc[-2])
            rsi_momentum = current_rsi - prev_rsi
            
            # 5. MACD momentum
            current_macd = float(df['macd'].iloc[-1])
            prev_macd = float(df['macd'].iloc[-2])
            macd_momentum = current_macd - prev_macd
            
            # Strong trend conditions
            strong_bullish_trend = (
                price_momentum_3 > 2.0 and  # Price up more than 2% in 3 periods
                volume_trend > 1.3 and      # Volume 30% above average
                range_expansion > 1.2 and   # Price range 20% above average
                rsi_momentum > 5 and        # RSI momentum positive
                macd_momentum > 0 and       # MACD momentum positive
                current_rsi > 50            # RSI above neutral
            )
            
            strong_bearish_trend = (
                price_momentum_3 < -2.0 and  # Price down more than 2% in 3 periods
                volume_trend > 1.3 and       # Volume 30% above average
                range_expansion > 1.2 and    # Price range 20% above average
                rsi_momentum < -5 and        # RSI momentum negative
                macd_momentum < 0 and        # MACD momentum negative
                current_rsi < 50             # RSI below neutral
            )
            
            if strong_bullish_trend:
                return "BUY"
            elif strong_bearish_trend:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Strong Trend signal calculation: {e}")
            return None

    def check_breakout_signal(self, df):
        """Breakout Signal - For price breakouts with volume confirmation"""
        try:
            close = df['close'].astype(float)
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            volume = df['volume'].astype(float)
            
            # Calculate recent highs and lows
            recent_high = high.iloc[-20:].max()
            recent_low = low.iloc[-20:].min()
            
            current_price = float(close.iloc[-1])
            current_volume = float(volume.iloc[-1])
            avg_volume = float(df['volume_sma20'].iloc[-1])
            
            # Breakout conditions
            breakout_up = current_price > recent_high * 1.001  # 0.1% above recent high
            breakout_down = current_price < recent_low * 0.999  # 0.1% below recent low
            
            # Volume confirmation
            volume_confirmation = current_volume > avg_volume * 1.5
            
            # RSI conditions for breakout
            current_rsi = float(df['rsi'].iloc[-1])
            rsi_bullish = current_rsi > 50
            rsi_bearish = current_rsi < 50
            
            if breakout_up and volume_confirmation and rsi_bullish:
                return "BUY"
            elif breakout_down and volume_confirmation and rsi_bearish:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Breakout signal calculation: {e}")
            return None

    def check_momentum_acceleration_signal(self, df):
        """Momentum Acceleration Signal - For accelerating price movements"""
        try:
            close = df['close'].astype(float)
            
            # Calculate price acceleration (rate of change of rate of change)
            roc_1 = ((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2]) * 100
            roc_2 = ((close.iloc[-2] - close.iloc[-3]) / close.iloc[-3]) * 100
            roc_3 = ((close.iloc[-3] - close.iloc[-4]) / close.iloc[-4]) * 100
            
            # Acceleration = current ROC - previous ROC
            acceleration_1 = roc_1 - roc_2
            acceleration_2 = roc_2 - roc_3
            
            # Volume acceleration
            volume = df['volume'].astype(float)
            vol_1 = float(volume.iloc[-1])
            vol_2 = float(volume.iloc[-2])
            vol_3 = float(volume.iloc[-3])
            vol_acceleration = (vol_1 - vol_2) / vol_2 if vol_2 > 0 else 0
            
            # RSI acceleration
            current_rsi = float(df['rsi'].iloc[-1])
            prev_rsi = float(df['rsi'].iloc[-2])
            prev_prev_rsi = float(df['rsi'].iloc[-3])
            rsi_acceleration = (current_rsi - prev_rsi) - (prev_rsi - prev_prev_rsi)
            
            # Strong acceleration conditions
            bullish_acceleration = (
                acceleration_1 > 0.5 and      # Current acceleration positive
                acceleration_2 > 0.3 and      # Previous acceleration positive
                vol_acceleration > 0.2 and    # Volume increasing
                rsi_acceleration > 2 and      # RSI accelerating up
                current_rsi > 40              # RSI not oversold
            )
            
            bearish_acceleration = (
                acceleration_1 < -0.5 and     # Current acceleration negative
                acceleration_2 < -0.3 and     # Previous acceleration negative
                vol_acceleration > 0.2 and    # Volume increasing
                rsi_acceleration < -2 and     # RSI accelerating down
                current_rsi < 60              # RSI not overbought
            )
            
            if bullish_acceleration:
                return "BUY"
            elif bearish_acceleration:
                return "SELL"
            
            return None
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in Momentum Acceleration signal calculation: {e}")
            return None

    async def check_market_conditions(self, symbol):
        try:
            # ตรวจสอบ balance ก่อน
            await self.update_account_balance()
            if self.account_balance is None:
                logger.warning(f"Cannot check market conditions for {symbol}: Account balance is None")
                return
            
            account = await self.safe_api_call(self.client.futures_account)
            available_balance = float(account['availableBalance'])
            
            if available_balance < 5:  # ขั้นต่ำ 5 USDT
                logger.warning(f"Insufficient balance for trading: {available_balance} USDT")
                return
            
            # ดึงข้อมูลราคา
            klines = await self.safe_api_call(
                self.client.futures_klines,
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1MINUTE,
                limit=100
            )
            
            if not klines:
                logger.warning(f"No kline data available for {symbol}")
                return
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            df['close'] = pd.to_numeric(df['close'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            current_price = float(df['close'].iloc[-1])
            
            # คำนวณ indicators
            indicators = self.calculate_indicators(df)
            current_rsi = indicators['rsi'].iloc[-1]
            
            # ตรวจสอบ margin ก่อนที่จะทำการเทรด
            try:
                # ดึง leverage ปัจจุบัน
                position_info = await self.safe_api_call(self.client.futures_position_information, symbol=symbol)
                current_leverage = float(position_info[0]['leverage']) if position_info else config.LEVERAGE
                
                # คำนวณ position size ที่ต้องการ
                coin_recommendations = await self.get_coin_recommendations(symbol)
                position_size_multiplier = coin_recommendations.get('recommendations', {}).get('position_size_multiplier', 0.6)
                
                # คำนวณ margin requirement
                margin_requirement = 1.0 / current_leverage
                
                # คำนวณ position size ที่ปลอดภัย
                if available_balance < config.MIN_BALANCE_THRESHOLD:
                    safe_balance = available_balance * 0.8
                else:
                    safe_balance = available_balance * config.POSITION_SIZE_BUFFER
                
                max_position_value = safe_balance * current_leverage * position_size_multiplier
                estimated_quantity = max_position_value / current_price
                estimated_notional = estimated_quantity * current_price
                required_margin = estimated_notional * margin_requirement
                
                # ตรวจสอบว่า margin พอหรือไม่
                if required_margin > available_balance:
                    logger.warning(f"Insufficient margin for {symbol}: Required={required_margin:.2f} USDT, Available={available_balance:.2f} USDT")
                    return
                
                logger.info(f"✅ Margin check passed for {symbol}: Required={required_margin:.2f} USDT, Available={available_balance:.2f} USDT")
                
            except Exception as e:
                logger.warning(f"Could not verify margin for {symbol}: {e}")
                # ดำเนินการต่อแม้จะไม่สามารถตรวจสอบ margin ได้
            
            # ตรวจสอบสัญญาณต่างๆ
            signals_dict_local = {}
            signals = []
            directions = []
            # Helper to append
            def _add_signal(res, name):
                signals_dict_local[name] = res  # Store raw result for weighted analysis
                if res == "BUY":
                    signals.append(f"{name} (BUY)")
                    directions.append("BUY")
                elif res == "SELL":
                    signals.append(f"{name} (SELL)")
                    directions.append("SELL")

            # Evaluate indicators
            _add_signal(self.check_macd_trend_signal(df), "MACD Trend")
            _add_signal(self.check_bollinger_rsi_signal(df, current_price), "Bollinger RSI")
            _add_signal(self.check_stochastic_williams_signal(df), "Stochastic Williams")
            _add_signal(self.check_momentum_signal(df), "Momentum")
            _add_signal(self.check_fibonacci_rsi_signal(df), "Fibonacci RSI")
            _add_signal(self.check_parabolic_sar_adx_signal(df), "Parabolic SAR ADX")
            _add_signal(self.check_keltner_cci_signal(df), "Keltner CCI")
            _add_signal(self.check_pivot_points_rsi_signal(df), "Pivot Points RSI")
            _add_signal(self.check_money_flow_volume_signal(df), "Money Flow Volume")
            _add_signal(self.check_atr_moving_average_signal(df), "ATR Moving Average")
            _add_signal(self.check_rvi_stochastic_signal(df), "RVI Stochastic")
            _add_signal(self.check_cci_bollinger_signal(df), "CCI Bollinger")
            _add_signal(self.check_obv_price_action_signal(df), "OBV Price Action")
            _add_signal(self.check_chaikin_money_flow_macd_signal(df), "Chaikin Money Flow MACD")
            _add_signal(self.check_roc_moving_average_crossover_signal(df), "ROC MA Crossover")
            _add_signal(self.check_emergency_signal(df), "Emergency")
            _add_signal(self.check_strong_trend_signal(df), "Strong Trend")
            _add_signal(self.check_breakout_signal(df), "Breakout")
            _add_signal(self.check_momentum_acceleration_signal(df), "Momentum Acceleration")
            
            # Advanced Strategies
            _add_signal(self.check_volume_profile_signal(df), "Volume Profile")
            _add_signal(self.check_market_structure_signal(df), "Market Structure")
            _add_signal(self.check_order_flow_signal(df), "Order Flow")

            # ส่งข้อมูล technical indicators
            await self.send_technical_indicators(symbol, current_price, current_rsi)

            # Enhanced signal analysis with weighted scoring
            signals_dict = signals_dict_local.copy()

            # Get weighted signal with confidence score
            weighted_signal, confidence_score = self.get_weighted_signal(signals_dict)
            
            # Calculate signal strength for the weighted signal
            if weighted_signal:
                signal_strength = self.calculate_signal_strength(df, weighted_signal)
                logger.info(f"🎯 Weighted Signal for {symbol}: {weighted_signal} (Confidence: {confidence_score:.2f}, Strength: {signal_strength}/100)")
            else:
                signal_strength = 0

            buy_count = directions.count("BUY")
            sell_count = directions.count("SELL")
            consensus_threshold = 3  # require 3 aligned signals
            trade_direction = None
            
            # Use weighted signal if confidence is high enough (lowered thresholds for better responsiveness)
            if weighted_signal and confidence_score > 0.25 and signal_strength > 30:
                trade_direction = weighted_signal
                logger.info(f"🚀 Using weighted signal for {symbol}: {weighted_signal} (Confidence: {confidence_score:.2f})")
            elif buy_count >= consensus_threshold and sell_count == 0:
                trade_direction = "BUY"
            elif sell_count >= consensus_threshold and buy_count == 0:
                trade_direction = "SELL"

            if trade_direction:
                logger.info(
                    f"🎯 Final signal for {symbol}: {trade_direction} | "
                    f"Signals: {', '.join(signals)} | "
                    f"Confidence: {confidence_score:.2f} | "
                    f"Strength: {signal_strength}/100")
                
                if symbol not in self.active_trades:
                    if available_balance >= 5:
                        side = SIDE_BUY if trade_direction == "BUY" else SIDE_SELL
                        await self.place_order(symbol, side, 0)
                    else:
                        logger.warning(f"Insufficient balance for {symbol}: {available_balance} USDT")
                else:
                    logger.info(f"Position already exists for {symbol}")
            else:
                logger.debug(f"No strong signal for {symbol}. Signals: {signals} | Confidence: {confidence_score:.2f}")
        except Exception as e:
            logger.error(f"Error checking market conditions for {symbol}: {str(e)}")

    async def verify_api_connection(self):
        try:
            # Test API connection
            server_time = await self.safe_api_call(self.client.get_server_time)
            logger.info(f"Successfully connected to Binance API. Server time: {server_time}")
            
            # Test futures API specifically
            try:
                # Get futures account information
                account = await self.safe_api_call(self.client.futures_account)
                logger.info("Futures Account Information:")
                logger.info(f"Total Wallet Balance: {account['totalWalletBalance']} USDT")
                logger.info(f"Available Balance: {account['availableBalance']} USDT")
                logger.info(f"Total Unrealized Profit: {account['totalUnrealizedProfit']} USDT")
                logger.info(f"Total Margin Balance: {account['totalMarginBalance']} USDT")
                
                # Check if futures trading is enabled
                if account['canTrade']:
                    logger.info("Futures trading is enabled")
                else:
                    logger.warning("Futures trading is not enabled for this account")
                    
                # Check API permissions
                api_permissions = await self.safe_api_call(self.client.get_account_api_permissions)
                logger.info("API Permissions:")
                logger.info(f"Enable Reading: {api_permissions.get('enableReading', False)}")
                logger.info(f"Enable Futures: {api_permissions.get('enableFutures', False)}")
                logger.info(f"Enable Spot & Margin Trading: {api_permissions.get('enableSpotAndMarginTrading', False)}")
                
                if not api_permissions.get('enableFutures', False):
                    raise Exception("Futures trading is not enabled in API permissions")
                    
            except Exception as e:
                logger.error(f"Futures API Error: {str(e)}")
                raise Exception(f"Failed to access Futures API: {str(e)}")
                
        except Exception as e:
            logger.error(f"Failed to verify API connection: {str(e)}")
            raise Exception("Failed to connect to Binance API. Please check your API keys and permissions.")

    async def update_account_balance(self):
        try:
            account = await self.safe_api_call(self.client.futures_account)
            self.account_balance = float(account['totalWalletBalance'])
            available_balance = float(account['availableBalance'])
            unrealized_profit = float(account['totalUnrealizedProfit'])
            margin_balance = float(account['totalMarginBalance'])
            
            # Set initial balance for risk management if not set
            if self.initial_balance is None:
                self.initial_balance = self.account_balance
                logger.info(f"💰 Initial balance set for risk management: {self.initial_balance:.2f} USDT")
            
            logger.info("Detailed Balance Information:")
            logger.info(f"Total Wallet Balance: {self.account_balance} USDT")
            logger.info(f"Available Balance: {available_balance} USDT")
            logger.info(f"Unrealized Profit: {unrealized_profit} USDT")
            logger.info(f"Margin Balance: {margin_balance} USDT")
            
            # Check risk limits
            if config.CIRCUIT_BREAKER_ENABLED:
                self.check_risk_limits()
            
            if self.account_balance <= 0:
                logger.warning("Account balance is 0 or negative. Please deposit funds to your futures account.")
                asyncio.create_task(self.notification.notify(
                    "⚠️ Warning: Account balance is 0 or negative.\n"
                    "Please follow these steps:\n"
                    "1. Log into your Binance account\n"
                    "2. Go to Futures section\n"
                    "3. Click 'Transfer' to move funds from spot to futures\n"
                    "4. Transfer at least 100 USDT\n"
                    "5. Verify the transfer is complete"
                ))
            if not account['canTrade']:
                logger.error("Futures trading is not enabled for this account")
                asyncio.create_task(self.notification.notify(
                    "❌ Error: Futures trading is not enabled.\n"
                    "Please enable futures trading in your Binance account settings."
                ))
        except Exception as e:
            logger.error(f"Failed to update account balance: {str(e)}")
            if "APIError(code=-2015)" in str(e):
                logger.error("Invalid API key or permissions. Please check your API key settings.")
                asyncio.create_task(self.notification.notify(
                    "❌ Error: Invalid API key or permissions.\n"
                    "Please check that your API key has futures trading enabled."
                ))

    def format_quantity(self, quantity, step_size):
        """Format quantity according to Binance precision requirements"""
        # Calculate precision from step_size
        precision = 0
        if step_size < 1:
            precision = len(str(step_size).split('.')[-1].rstrip('0'))
        
        # Round to the correct precision
        if precision == 0:
            return int(quantity)
        else:
            return round(quantity, precision)

    async def analyze_coins(self):
        """วิเคราะห์เหรียญทั้งหมดและอัปเดตคำแนะนำ"""
        try:
            current_time = time.time()
            if current_time - self.last_analysis_time < self.analysis_interval:
                return self.coin_analyses
            
            logger.info("🔄 เริ่มวิเคราะห์เหรียญ...")
            await self.notification.notify("🔄 กำลังวิเคราะห์เหรียญเพื่อคำนวณ order size และ leverage...")
            
            self.coin_analyses = await self.coin_analyzer.analyze_all_coins(config.TRADING_PAIRS)
            self.last_analysis_time = current_time
            
            # ส่งรายงานสรุป
            summary_report = self.coin_analyzer.get_summary_report(self.coin_analyses)
            await self.notification.notify(summary_report)
            
            logger.info("✅ วิเคราะห์เหรียญเสร็จสิ้น")
            return self.coin_analyses
            
        except Exception as e:
            logger.error(f"❌ เกิดข้อผิดพลาดในการวิเคราะห์เหรียญ: {e}")
            await self.notification.notify(f"❌ เกิดข้อผิดพลาดในการวิเคราะห์เหรียญ: {e}")
            return {}

    async def get_coin_recommendations(self, symbol: str) -> Dict:
        """ดึงคำแนะนำสำหรับเหรียญเฉพาะ"""
        if not self.coin_analyses or symbol not in self.coin_analyses:
            await self.analyze_coins()
        
        return self.coin_analyses.get(symbol, {})

    async def calculate_position_size(self, symbol, current_price):
        try:
            await self.update_account_balance()
            if self.account_balance is None:
                logger.error("Cannot calculate position size: Account balance is None")
                return None
            
            account = await self.safe_api_call(self.client.futures_account)
            available_balance = float(account['availableBalance'])
            if available_balance <= 0:
                logger.warning(f"Insufficient available balance: {available_balance} USDT")
                return None
            
            # ดึงคำแนะนำจาก coin analysis
            coin_recommendations = await self.get_coin_recommendations(symbol)
            position_size_multiplier = coin_recommendations.get('recommendations', {}).get('position_size_multiplier', config.POSITION_SIZE_MULTIPLIER)
            leverage_recommendation = coin_recommendations.get('recommendations', {}).get('leverage', {}).get('recommended', config.LEVERAGE)
            
            # จำกัด leverage ให้อยู่ในขีดจำกัดที่ปลอดภัย
            max_safe_leverage = min(leverage_recommendation, config.MAX_LEVERAGE)
            
            # Get symbol info for margin requirements
            symbol_info = await self.safe_api_call(self.client.futures_exchange_info)
            symbol_filters = next(filter(lambda x: x['symbol'] == symbol, symbol_info['symbols']))
            lot_size_filter = next(filter(lambda x: x['filterType'] == 'LOT_SIZE', symbol_filters['filters']))
            step_size = float(lot_size_filter['stepSize'])
            
            # คำนวณ safe balance
            if available_balance < config.MIN_BALANCE_THRESHOLD:
                # สำหรับบัญชีเล็ก ใช้ SMALL_ACCOUNT_POSITION_LIMIT
                max_position_percent = config.SMALL_ACCOUNT_POSITION_LIMIT
            else:
                # สำหรับบัญชีใหญ่ ใช้ MAX_POSITION_SIZE
                max_position_percent = config.MAX_POSITION_SIZE
            
            # คำนวณ maximum position value ที่อนุญาต
            max_position_value = available_balance * max_position_percent
            
            # ตั้ง leverage เป็นค่าที่เหมาะสม
            try:
                await self.safe_api_call(self.client.futures_change_leverage, symbol=symbol, leverage=max_safe_leverage)
                logger.info(f"Set leverage for {symbol} to {max_safe_leverage}x")
            except Exception as e:
                logger.warning(f"Failed to set leverage for {symbol}: {e}")
            
            # คำนวณ margin requirement
            margin_requirement = 1.0 / max_safe_leverage
            
            # คำนวณ position size ขึ้นอยู่กับ margin ที่มี
            max_notional = max_position_value
            
            # ตรวจสอบว่า margin พอหรือไม่
            required_margin = max_notional * margin_requirement
            if required_margin > available_balance:
                # ถ้า margin ไม่พอ ลด position size
                max_notional = available_balance / margin_requirement
            
            # ใช้ position size multiplier
            final_notional = max_notional * position_size_multiplier
            
            # ตรวจสอบ minimum notional
            if final_notional < config.MIN_NOTIONAL:
                logger.warning(f"Position size too small for {symbol}: {final_notional:.2f} < {config.MIN_NOTIONAL} USDT")
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Position size too small: {final_notional:.2f} USDT\n"
                    f"Minimum required: {config.MIN_NOTIONAL} USDT"
                )
                return None
            
            # คำนวณ quantity
            quantity = final_notional / current_price
            quantity = self.format_quantity(quantity, step_size)
            
            # คำนวณค่าสุดท้าย
            final_notional = quantity * current_price
            final_margin = final_notional * margin_requirement
            
            # Log การคำนวณ
            order_size_category = coin_recommendations.get('categories', {}).get('order_size', 'MEDIUM')
            leverage_category = coin_recommendations.get('categories', {}).get('leverage', 'MEDIUM')
            
            logger.info(f"Position calculation for {symbol}: Order Size={order_size_category}, Leverage={leverage_category}")
            logger.info(f"Available Balance: {available_balance:.2f} USDT")
            logger.info(f"Max Position %: {max_position_percent*100:.0f}%, Leverage: {max_safe_leverage}x")
            logger.info(f"Position Value: {final_notional:.2f} USDT, Required Margin: {final_margin:.2f} USDT")
            
            # ตรวจสอบว่าผ่านเกณฑ์ position limit หรือไม่
            if not self.check_position_size_limit(final_notional, available_balance):
                logger.warning(f"Position size limit check failed for {symbol}")
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Position size exceeds limit.\n"
                    f"Notional value: {final_notional:.2f} USDT\n"
                    f"Max allowed: {max_position_value:.2f} USDT"
                )
                return None
            
            # ส่งข้อมูลการวิเคราะห์
            analysis_notes = coin_recommendations.get('recommendations', {}).get('notes', [])
            if analysis_notes:
                await self.notification.notify(
                    f"📊 การวิเคราะห์ {symbol}:\n" + "\n".join(analysis_notes[:3])
                )
            
            logger.info(f"✅ Final position size for {symbol}: {quantity} (Price: {current_price}, Notional: {final_notional:.2f} USDT, Margin: {final_margin:.2f} USDT)")
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return None

    def log_trade_activity(self, event, symbol, side=None, price=None, pnl=None, order_id=None, reason=None):
        history_file = "trade_history.json"
        entry = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            "symbol": symbol,
            "side": side,
            "price": price,
            "pnl": pnl,
            "order_id": order_id,
            "reason": reason
        }
        # Read existing history
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    history = json.load(f)
            except Exception:
                history = []
        # Append new entry and keep only last 100
        history.append(entry)
        history = history[-100:]
        with open(history_file, "w") as f:
            json.dump(history, f)

    async def place_order(self, symbol, side, quantity):
        try:
            # Check circuit breaker first
            if config.CIRCUIT_BREAKER_ENABLED and self.circuit_breaker_triggered:
                logger.warning(f"🚨 Cannot place order for {symbol}: Circuit breaker is active")
                await self.notification.notify(f"🚨 Trading stopped: Circuit breaker is active")
                return None
            
            ticker = await self.safe_api_call(self.client.futures_symbol_ticker, symbol=symbol)
            current_price = float(ticker['price'])
            
            # ตรวจสอบ balance ก่อน
            await self.update_account_balance()
            if self.account_balance is None:
                await self.notification.notify(f"❌ Cannot place order for {symbol}: Account balance is None")
                return None
            
            account = await self.safe_api_call(self.client.futures_account)
            available_balance = float(account['availableBalance'])
            
            if available_balance <= 0:
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Insufficient available balance: {available_balance} USDT"
                )
                return None
            
            # คำนวณ position size ด้วย aggressive leverage
            calculated_quantity = await self.calculate_position_size(symbol, current_price)
            if calculated_quantity is None:
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Even with maximum leverage (125x), position size is too small.\n"
                    f"Minimum order size: 20 USDT\n"
                    f"Current price: {current_price} USDT\n"
                    f"Available balance: {available_balance:.2f} USDT"
                )
                return None
            
            # ใช้ quantity ที่คำนวณได้ (ถ้า quantity parameter เป็น 0 ให้ใช้ calculated_quantity)
            if quantity <= 0:
                quantity = calculated_quantity
            
            # ตรวจสอบ quantity อีกครั้ง
            if quantity <= 0:
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Calculated position size is too small.\n"
                    f"Minimum order size: 20 USDT\n"
                    f"Current price: {current_price} USDT"
                )
                return None
            
            # ตรวจสอบ notional value
            notional_value = quantity * current_price
            
            # Check position size limit
            if not self.check_position_size_limit(notional_value, available_balance):
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Position size exceeds limit.\n"
                    f"Notional value: {notional_value:.2f} USDT\n"
                    f"Max allowed: {available_balance * config.MAX_POSITION_SIZE:.2f} USDT"
                )
                return None
            
            if notional_value < 20.0:
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Order size too small.\n"
                    f"Current notional value: {notional_value:.2f} USDT\n"
                    f"Minimum required: 20 USDT"
                )
                return None
            
            # ตรวจสอบ margin อีกครั้งก่อนวาง order
            try:
                # ดึง leverage ปัจจุบัน
                position_info = await self.safe_api_call(self.client.futures_position_information, symbol=symbol)
                current_leverage = float(position_info[0]['leverage']) if position_info else config.LEVERAGE
                margin_requirement = 1.0 / current_leverage
                required_margin = notional_value * margin_requirement
                
                if required_margin > available_balance:
                    await self.notification.notify(
                        f"❌ Cannot place order for {symbol}:\n"
                        f"Insufficient margin for order.\n"
                        f"Available balance: {available_balance:.2f} USDT\n"
                        f"Required margin: {required_margin:.2f} USDT\n"
                        f"Notional value: {notional_value:.2f} USDT\n"
                        f"Leverage: {current_leverage}x"
                    )
                    return None
                
                logger.info(f"✅ Margin check passed for {symbol}: Required={required_margin:.2f} USDT, Available={available_balance:.2f} USDT")
                
            except Exception as e:
                logger.warning(f"Could not verify margin for {symbol}: {e}")
                # ดำเนินการต่อแม้จะไม่สามารถตรวจสอบ margin ได้
            
            # วาง order
            order = await self.safe_api_call(
                self.client.futures_create_order,
                symbol=symbol,
                side=side,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=quantity
            )
            
            # Update daily trade count
            self.daily_trades_count += 1
            logger.info(f"📊 Daily trades: {self.daily_trades_count}/{config.MAX_DAILY_TRADES}")
            
            entry_price = float(order['avgPrice'])
            position_side = "LONG" if side == SIDE_BUY else "SHORT"
            self.active_trades[symbol] = {
                'entry_price': entry_price,
                'position_side': position_side,
                'quantity': quantity,
                'pnl': 0
            }
            self.save_status()
            self.log_trade_activity(
                event="Position Opened",
                symbol=symbol,
                side=position_side,
                price=entry_price,
                order_id=order.get('orderId'),
                reason="Manual"
            )
            await self.notification.notify(
                f"✅ New {position_side} position opened for {symbol}\n"
                f"Entry Price: {entry_price}\n"
                f"Quantity: {quantity}\n"
                f"Notional Value: {notional_value:.2f} USDT\n"
                f"Daily Trades: {self.daily_trades_count}/{config.MAX_DAILY_TRADES}"
            )
            logger.info(f"Order placed successfully: {order}")
            return order
        except Exception as e:
            logger.error(f"Failed to place order: {str(e)}")
            await self.notification.notify(f"Failed to place order: {str(e)}")
            return None

    async def close_position(self, symbol):
        try:
            trade = self.active_trades[symbol]
            side = SIDE_SELL if trade['position_side'] == "LONG" else SIDE_BUY
            order = await self.safe_api_call(
                self.client.futures_create_order,
                symbol=symbol,
                side=side,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=trade['quantity']
            )
            current_price = float(order['avgPrice'])
            pnl = (current_price - trade['entry_price']) * trade['quantity']
            if trade['position_side'] == "SHORT":
                pnl = -pnl
            
            # Update daily PnL
            if self.update_daily_pnl(pnl):
                trade['pnl'] = pnl
                await self.notification.notify(
                    f"Position closed for {symbol}\n"
                    f"Exit Price: {current_price}\n"
                    f"P&L: {pnl:.2f} USDT\n"
                    f"Daily P&L: {self.daily_pnl:.2f} USDT"
                )
                self.log_trade_activity(
                    event="Position Closed",
                    symbol=symbol,
                    side=trade['position_side'],
                    price=current_price,
                    pnl=pnl,
                    order_id=order.get('orderId'),
                    reason="Manual"
                )
                del self.active_trades[symbol]
                self.save_status()
                logger.info(f"Position closed successfully: {order}")
            else:
                logger.warning(f"🚨 Position closed but trading stopped due to risk limits")
                await self.notification.notify(f"🚨 Position closed but trading stopped due to risk limits")
                
        except Exception as e:
            logger.error(f"Failed to close position: {str(e)}")
            await self.notification.notify(f"Failed to close position: {str(e)}")

    async def setup_bot(self):
        """Async setup method to be called after bot creation"""
        await self.verify_api_connection()
        await self.update_account_balance()
        # วิเคราะห์เหรียญครั้งแรก
        await self.analyze_coins()

    async def run(self):
        await self.setup_bot()
        await self.initialize()
        
        # วิเคราะห์เหรียญทุกชั่วโมง
        last_analysis = time.time()
        
        while True:
            try:
                self.send_heartbeat()
                
                # วิเคราะห์เหรียญทุกชั่วโมง
                current_time = time.time()
                if current_time - last_analysis >= self.analysis_interval:
                    await self.analyze_coins()
                    last_analysis = current_time
                
                for symbol in config.TRADING_PAIRS:
                    await self.check_market_conditions(symbol)
                    
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await self.notification.notify(f"Error in main loop: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying

    def save_status(self, running=True):
        status = {
            "running": running,
            "active_trades_count": len(self.active_trades),
            "total_pnl": self.calculate_total_pnl(),
            "last_update": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open("bot_status.json", "w") as f:
            json.dump(status, f)
        self.save_active_trades()

    def save_active_trades(self):
        trades = []
        for symbol, trade in self.active_trades.items():
            trades.append({
                "Symbol": symbol,
                "Side": trade.get("position_side"),
                "Entry": trade.get("entry_price"),
                "Quantity": trade.get("quantity"),
            })
        with open("active_trades.json", "w") as f:
            json.dump(trades, f)

    def calculate_total_pnl(self):
        # This is a placeholder. You can implement real P&L calculation if you store trade history.
        return 0.0

    def confirm_signal_across_timeframes(self, tf_signals, min_confirm=2):
        """
        Confirm signal across multiple timeframes
        Returns 'buy', 'sell', or None
        """
        if not tf_signals:
            return None
        
        buy_count = sum(1 for signal in tf_signals.values() if signal == 'buy')
        sell_count = sum(1 for signal in tf_signals.values() if signal == 'sell')
        
        # Require minimum confirmation
        if buy_count >= min_confirm and sell_count == 0:
            return 'buy'
        elif sell_count >= min_confirm and buy_count == 0:
            return 'sell'
        
        return None

    def check_risk_limits(self):
        """
        Check if trading should be stopped due to risk limits
        Returns True if trading should be stopped
        """
        try:
            # Reset daily counters if it's a new day
            current_date = datetime.now().date()
            if self.last_trade_date != current_date:
                self.daily_pnl = 0.0
                self.daily_trades_count = 0
                self.last_trade_date = current_date
                self.circuit_breaker_triggered = False
                logger.info("🔄 New trading day - resetting daily counters")
            
            # Check daily loss limit
            if self.initial_balance and self.daily_pnl < -(self.initial_balance * config.DAILY_LOSS_LIMIT):
                if not self.circuit_breaker_triggered:
                    self.circuit_breaker_triggered = True
                    logger.warning(f"🚨 CIRCUIT BREAKER: Daily loss limit exceeded! PnL: {self.daily_pnl:.2f} USDT")
                    asyncio.create_task(self.notification.notify(
                        f"🚨 CIRCUIT BREAKER ACTIVATED\n"
                        f"Daily Loss Limit: {config.DAILY_LOSS_LIMIT * 100}%\n"
                        f"Current PnL: {self.daily_pnl:.2f} USDT\n"
                        f"Trading stopped for safety"
                    ))
                return True
            
            # Check daily trade limit
            if self.daily_trades_count >= config.MAX_DAILY_TRADES:
                if not self.circuit_breaker_triggered:
                    self.circuit_breaker_triggered = True
                    logger.warning(f"🚨 CIRCUIT BREAKER: Daily trade limit exceeded! Trades: {self.daily_trades_count}")
                    asyncio.create_task(self.notification.notify(
                        f"🚨 CIRCUIT BREAKER ACTIVATED\n"
                        f"Daily Trade Limit: {config.MAX_DAILY_TRADES}\n"
                        f"Current Trades: {self.daily_trades_count}\n"
                        f"Trading stopped for safety"
                    ))
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in risk limit check: {e}")
            return True  # Stop trading if error occurs
    
    def update_daily_pnl(self, pnl_change):
        """
        Update daily PnL and check risk limits
        """
        try:
            self.daily_pnl += pnl_change
            logger.info(f"📊 Daily PnL updated: {self.daily_pnl:.2f} USDT (change: {pnl_change:.2f})")
            
            # Check if we should stop trading
            if self.check_risk_limits():
                logger.warning("🛑 Trading stopped due to risk limits")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating daily PnL: {e}")
            return False
    
    def check_position_size_limit(self, position_value, available_balance):
        """
        Check if position size exceeds limits
        Returns True if position is within limits
        """
        try:
            max_position_value = available_balance * config.MAX_POSITION_SIZE
            
            if position_value > max_position_value:
                logger.warning(f"⚠️ Position size limit exceeded: {position_value:.2f} > {max_position_value:.2f} USDT")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking position size limit: {e}")
            return False

    def calculate_signal_strength(self, df, signal_type):
        """
        Calculate signal strength score (0-100)
        Higher score = stronger signal
        """
        try:
            strength = 0
            
            if signal_type == "BUY":
                # RSI oversold
                current_rsi = float(df['rsi'].iloc[-1])
                if current_rsi < 30:
                    strength += 20
                elif current_rsi < 40:
                    strength += 10
                
                # Volume confirmation
                current_volume = float(df['volume'].iloc[-1])
                avg_volume = float(df['volume_sma20'].iloc[-1])
                if current_volume > avg_volume * 2:
                    strength += 25
                elif current_volume > avg_volume * 1.5:
                    strength += 15
                
                # MACD momentum
                current_macd = float(df['macd'].iloc[-1])
                prev_macd = float(df['macd'].iloc[-2])
                if current_macd > prev_macd and current_macd > 0:
                    strength += 20
                
                # Price above SMA
                sma20 = float(df['sma20'].iloc[-1])
                current_price = float(df['close'].iloc[-1])
                if current_price > sma20:
                    strength += 15
                
                # Stochastic oversold
                current_stoch = float(df['stoch_k'].iloc[-1])
                if current_stoch < 20:
                    strength += 20
                    
            elif signal_type == "SELL":
                # RSI overbought
                current_rsi = float(df['rsi'].iloc[-1])
                if current_rsi > 70:
                    strength += 20
                elif current_rsi > 60:
                    strength += 10
                
                # Volume confirmation
                current_volume = float(df['volume'].iloc[-1])
                avg_volume = float(df['volume_sma20'].iloc[-1])
                if current_volume > avg_volume * 2:
                    strength += 25
                elif current_volume > avg_volume * 1.5:
                    strength += 15
                
                # MACD momentum
                current_macd = float(df['macd'].iloc[-1])
                prev_macd = float(df['macd'].iloc[-2])
                if current_macd < prev_macd and current_macd < 0:
                    strength += 20
                
                # Price below SMA
                sma20 = float(df['sma20'].iloc[-1])
                current_price = float(df['close'].iloc[-1])
                if current_price < sma20:
                    strength += 15
                
                # Stochastic overbought
                current_stoch = float(df['stoch_k'].iloc[-1])
                if current_stoch > 80:
                    strength += 20
            
            return min(strength, 100)  # Cap at 100
            
        except Exception as e:
            logger.warning(f"Error calculating signal strength: {e}")
            return 0

    def check_volume_profile_signal(self, df):
        """
        Volume Profile Analysis - Advanced volume-based signal
        """
        try:
            current_volume = float(df['volume'].iloc[-1])
            avg_volume = float(df['volume_sma20'].iloc[-1])
            current_price = float(df['close'].iloc[-1])
            current_rsi = float(df['rsi'].iloc[-1])
            
            # Volume spike detection
            volume_ratio = current_volume / avg_volume
            
            # Price momentum
            prev_price = float(df['close'].iloc[-2])
            price_change = (current_price - prev_price) / prev_price * 100
            
            # Volume confirmation patterns
            if volume_ratio > 2.0:  # High volume spike
                if price_change > 1.0 and current_rsi < 70:
                    return "BUY"
                elif price_change < -1.0 and current_rsi > 30:
                    return "SELL"
            
            # Volume divergence
            if volume_ratio > 1.5:
                if price_change < 0.5 and current_rsi < 40:
                    return "BUY"  # Volume up, price down = accumulation
                elif price_change > 0.5 and current_rsi > 60:
                    return "SELL"  # Volume up, price up = distribution
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in Volume Profile signal: {e}")
            return None

    def check_market_structure_signal(self, df):
        """
        Market Structure Analysis - Support/Resistance levels
        """
        try:
            high = df['high'].astype(float)
            low = df['low'].astype(float)
            close = df['close'].astype(float)
            current_price = float(close.iloc[-1])
            
            # Find recent highs and lows
            recent_highs = high.tail(20).nlargest(3)
            recent_lows = low.tail(20).nsmallest(3)
            
            # Resistance level (average of recent highs)
            resistance = recent_highs.mean()
            
            # Support level (average of recent lows)
            support = recent_lows.mean()
            
            # Distance to levels
            distance_to_resistance = (resistance - current_price) / current_price * 100
            distance_to_support = (current_price - support) / current_price * 100
            
            # RSI for confirmation
            current_rsi = float(df['rsi'].iloc[-1])
            
            # Breakout/breakdown signals
            if distance_to_resistance < 1.0 and current_rsi > 60:
                return "SELL"  # Near resistance, overbought
            elif distance_to_support < 1.0 and current_rsi < 40:
                return "BUY"   # Near support, oversold
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in Market Structure signal: {e}")
            return None

    def check_order_flow_signal(self, df):
        """
        Order Flow Analysis - Based on price action and volume
        """
        try:
            open_prices = df['open'].astype(float)
            close_prices = df['close'].astype(float)
            high_prices = df['high'].astype(float)
            low_prices = df['low'].astype(float)
            volumes = df['volume'].astype(float)
            
            # Current candle analysis
            current_open = float(open_prices.iloc[-1])
            current_close = float(close_prices.iloc[-1])
            current_high = float(high_prices.iloc[-1])
            current_low = float(low_prices.iloc[-1])
            current_volume = float(volumes.iloc[-1])
            
            # Previous candle
            prev_open = float(open_prices.iloc[-2])
            prev_close = float(close_prices.iloc[-2])
            prev_volume = float(volumes.iloc[-2])
            
            # Candle patterns
            bullish_candle = current_close > current_open
            bearish_candle = current_close < current_open
            
            # Volume analysis
            volume_increase = current_volume > prev_volume * 1.2
            
            # Body size (strength of move)
            body_size = abs(current_close - current_open)
            avg_body = abs(close_prices - open_prices).tail(10).mean()
            strong_move = body_size > avg_body * 1.5
            
            # Order flow signals
            if bullish_candle and volume_increase and strong_move:
                return "BUY"
            elif bearish_candle and volume_increase and strong_move:
                return "SELL"
            
            return None
            
        except Exception as e:
            logger.warning(f"Error in Order Flow signal: {e}")
            return None

    def get_weighted_signal(self, signals_dict):
        """
        Get weighted signal based on signal strength and reliability
        Returns: (signal, confidence_score)
        """
        try:
            buy_signals = []
            sell_signals = []
            
            # Signal weights (higher = more reliable)
            signal_weights = {
                'MACD Trend': 0.15,
                'Bollinger RSI': 0.12,
                'Stochastic Williams': 0.10,
                'Momentum': 0.08,
                'Fibonacci RSI': 0.06,
                'Parabolic SAR ADX': 0.14,
                'Volume Profile': 0.13,
                'Market Structure': 0.11,
                'Order Flow': 0.11,
                'OBV Price Action': 0.09,
                'ROC MA Crossover': 0.08,
                'ATR Moving Average': 0.07,
                'Chaikin Money Flow MACD': 0.06,
                'Emergency': 0.20,  # High weight for emergency signals
                'Strong Trend': 0.16,
                'Breakout': 0.12,
                'Momentum Acceleration': 0.10
            }
            
            for signal_name, signal_value in signals_dict.items():
                if signal_value == "BUY":
                    weight = signal_weights.get(signal_name, 0.05)
                    buy_signals.append(weight)
                elif signal_value == "SELL":
                    weight = signal_weights.get(signal_name, 0.05)
                    sell_signals.append(weight)
            
            # Calculate weighted scores
            buy_score = sum(buy_signals)
            sell_score = sum(sell_signals)
            
            # Determine final signal with lower threshold for better responsiveness
            if buy_score > 0.2 and buy_score > sell_score * 1.2:
                return ("BUY", buy_score)
            elif sell_score > 0.2 and sell_score > buy_score * 1.2:
                return ("SELL", sell_score)
            
            return (None, 0)
            
        except Exception as e:
            logger.warning(f"Error in weighted signal calculation: {e}")
            return (None, 0)