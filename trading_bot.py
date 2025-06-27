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

class TradingBot:
    def __init__(self):
        self.client = Client(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
        self.notification = NotificationSystem()
        self.active_trades = {}
        self.setup_logging()
        self.last_heartbeat = time.time()
        self.account_balance = None
        self.last_rsi = {}

    def setup_logging(self):
        logger.add(
            config.LOG_FILE,
            rotation="1 day",
            retention="7 days",
            level=config.LOG_LEVEL
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
                await self.safe_api_call(self.client.futures_change_leverage, symbol=symbol, leverage=config.LEVERAGE)
                logger.info(f"Set leverage for {symbol} to {config.LEVERAGE}x")
                ticker = await self.safe_api_call(self.client.futures_symbol_ticker, symbol=symbol)
                logger.info(f"Current price for {symbol}: {ticker['price']}")
                await self.notification.notify(
                    f"✅ Initialized {symbol}\n"
                    f"Leverage: {config.LEVERAGE}x\n"
                    f"Current Price: {ticker['price']}"
                )
            except Exception as e:
                logger.error(f"Failed to set leverage for {symbol}: {str(e)}")
                await self.notification.notify(f"❌ Failed to initialize {symbol}: {str(e)}")

    def send_heartbeat(self):
        current_time = time.time()
        if current_time - self.last_heartbeat >= 60:  # Send heartbeat every minute
            logger.info("Bot is running and monitoring markets...")
            self.last_heartbeat = current_time

    async def send_technical_indicators(self, symbol, current_price, current_rsi):
        # Send notification with RSI
        await self.notification.notify(
            f"📊 RSI Indicator for {symbol}\n"
            f"Price: {current_price:.2f}\n"
            f"RSI: {current_rsi:.2f}"
        )

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
        """Check momentum signal for additional confirmation"""
        try:
            # Price momentum (current price vs previous)
            current_price = float(df['close'].iloc[-1])
            prev_price = float(df['close'].iloc[-2])
            price_momentum = (current_price - prev_price) / prev_price * 100
            
            # Volume confirmation
            current_volume = float(df['volume'].iloc[-1])
            avg_volume = float(df['volume_sma20'].iloc[-1])
            volume_spike = current_volume > avg_volume * 1.5
            
            # RSI momentum
            current_rsi = float(df['rsi'].iloc[-1])
            prev_rsi = float(df['rsi'].iloc[-2])
            rsi_momentum = current_rsi - prev_rsi
            
            return price_momentum, volume_spike, rsi_momentum
        except (ValueError, TypeError, IndexError) as e:
            logger.warning(f"Error in momentum signal calculation: {e}")
            return 0.0, False, 0.0

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
            ticker = await self.safe_api_call(self.client.futures_symbol_ticker, symbol=symbol)
            current_price = float(ticker['price'])
            klines = await self.safe_api_call(
                self.client.futures_klines,
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_15MINUTE,
                limit=100
            )
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].astype(float)
            # Also convert volume to numeric
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
            df = self.calculate_indicators(df)
            
            # Get all signals from 16 strategies (3 original + 13 new)
            # Original strategies
            macd_signal = self.check_macd_trend_signal(df)
            bb_rsi_signal = self.check_bollinger_rsi_signal(df, current_price)
            stoch_williams_signal = self.check_stochastic_williams_signal(df)
            
            # New strategies
            fib_rsi_signal = self.check_fibonacci_rsi_signal(df)
            parabolic_sar_adx_signal = self.check_parabolic_sar_adx_signal(df)
            keltner_cci_signal = self.check_keltner_cci_signal(df)
            pivot_points_rsi_signal = self.check_pivot_points_rsi_signal(df)
            money_flow_volume_signal = self.check_money_flow_volume_signal(df)
            atr_moving_average_signal = self.check_atr_moving_average_signal(df)
            rvi_stochastic_signal = self.check_rvi_stochastic_signal(df)
            cci_bollinger_signal = self.check_cci_bollinger_signal(df)
            obv_price_action_signal = self.check_obv_price_action_signal(df)
            chaikin_money_flow_macd_signal = self.check_chaikin_money_flow_macd_signal(df)
            roc_moving_average_crossover_signal = self.check_roc_moving_average_crossover_signal(df)
            
            # Emergency and Strong Trend strategies (Priority signals)
            emergency_signal = self.check_emergency_signal(df)
            strong_trend_signal = self.check_strong_trend_signal(df)
            breakout_signal = self.check_breakout_signal(df)
            momentum_acceleration_signal = self.check_momentum_acceleration_signal(df)
            
            # Get momentum signals
            price_momentum, volume_spike, rsi_momentum = self.check_momentum_signal(df)
            
            # Log all indicators
            try:
                current_rsi = float(df['rsi'].iloc[-1])
                current_macd = float(df['macd'].iloc[-1])
                current_stoch_k = float(df['stoch_k'].iloc[-1])
                current_williams_r = float(df['williams_r'].iloc[-1])
                bb_upper = float(df['bb_upper'].iloc[-1])
                bb_lower = float(df['bb_lower'].iloc[-1])
                
                logger.info(f"Monitoring {symbol} - Price: {current_price}")
                logger.info(f"Indicators: RSI={current_rsi:.2f}, MACD={current_macd:.4f}, StochK={current_stoch_k:.2f}, WilliamsR={current_williams_r:.2f}")
                logger.info(f"Bollinger: Upper={bb_upper:.2f}, Lower={bb_lower:.2f}")
                
                # Log all signals
                all_signals = [
                    ("MACD+Trend", macd_signal),
                    ("BB+RSI", bb_rsi_signal),
                    ("Stoch+Williams", stoch_williams_signal),
                    ("Fib+RSI", fib_rsi_signal),
                    ("Parabolic+ADX", parabolic_sar_adx_signal),
                    ("Keltner+CCI", keltner_cci_signal),
                    ("Pivot+RSI", pivot_points_rsi_signal),
                    ("MFI+Volume", money_flow_volume_signal),
                    ("ATR+MA", atr_moving_average_signal),
                    ("RVI+Stoch", rvi_stochastic_signal),
                    ("CCI+BB", cci_bollinger_signal),
                    ("OBV+Price", obv_price_action_signal),
                    ("CMF+MACD", chaikin_money_flow_macd_signal),
                    ("ROC+MA", roc_moving_average_crossover_signal)
                ]
                
                priority_signals = [
                    ("Emergency", emergency_signal),
                    ("Strong Trend", strong_trend_signal),
                    ("Breakout", breakout_signal),
                    ("Momentum Accel", momentum_acceleration_signal)
                ]
                
                buy_signals_list = [name for name, signal in all_signals if signal == "BUY"]
                sell_signals_list = [name for name, signal in all_signals if signal == "SELL"]
                priority_buy_signals = [name for name, signal in priority_signals if signal == "BUY"]
                priority_sell_signals = [name for name, signal in priority_signals if signal == "SELL"]
                
                logger.info(f"Regular Buy Signals: {buy_signals_list}")
                logger.info(f"Regular Sell Signals: {sell_signals_list}")
                logger.info(f"Priority Buy Signals: {priority_buy_signals}")
                logger.info(f"Priority Sell Signals: {priority_sell_signals}")
                logger.info(f"Momentum: Price={price_momentum:.2f}%, Volume Spike={volume_spike}, RSI Momentum={rsi_momentum:.2f}")
                
                self.last_rsi[symbol] = current_rsi
            except (ValueError, TypeError, IndexError) as e:
                logger.warning(f"Error logging indicators for {symbol}: {e}")
                self.last_rsi[symbol] = 50.0  # Default neutral RSI value
            if symbol in self.active_trades:
                return
            
            # Priority signal check (Emergency and Strong Trend signals)
            if emergency_signal == "BUY" or strong_trend_signal == "BUY" or breakout_signal == "BUY" or momentum_acceleration_signal == "BUY":
                priority_reason = f"Priority signal: {[name for name, signal in priority_signals if signal == 'BUY']}"
                logger.info(f"🚨 PRIORITY BUY signal for {symbol} - {priority_reason}")
                await self.update_account_balance()
                if self.account_balance is None or self.account_balance <= 0:
                    logger.warning(f"Cannot open new position for {symbol}: Insufficient balance")
                    return
                quantity = await self.calculate_position_size(symbol, current_price)
                if quantity is None:
                    logger.warning(f"Cannot open new position for {symbol}: Invalid position size")
                    return
                await self.place_order(symbol, SIDE_BUY, quantity)
                return
            elif emergency_signal == "SELL" or strong_trend_signal == "SELL" or breakout_signal == "SELL" or momentum_acceleration_signal == "SELL":
                priority_reason = f"Priority signal: {[name for name, signal in priority_signals if signal == 'SELL']}"
                logger.info(f"🚨 PRIORITY SELL signal for {symbol} - {priority_reason}")
                await self.update_account_balance()
                if self.account_balance is None or self.account_balance <= 0:
                    logger.warning(f"Cannot open new position for {symbol}: Insufficient balance")
                    return
                quantity = await self.calculate_position_size(symbol, current_price)
                if quantity is None:
                    logger.warning(f"Cannot open new position for {symbol}: Invalid position size")
                    return
                await self.place_order(symbol, SIDE_SELL, quantity)
                return
            
            # Count signals from all 16 strategies
            all_signals = [macd_signal, bb_rsi_signal, stoch_williams_signal, 
                          fib_rsi_signal, parabolic_sar_adx_signal, keltner_cci_signal,
                          pivot_points_rsi_signal, money_flow_volume_signal, atr_moving_average_signal,
                          rvi_stochastic_signal, cci_bollinger_signal, obv_price_action_signal,
                          chaikin_money_flow_macd_signal, roc_moving_average_crossover_signal]
            
            buy_signals = sum([1 for signal in all_signals if signal == "BUY"])
            sell_signals = sum([1 for signal in all_signals if signal == "SELL"])
            
            # Enhanced decision logic with strategy weighting
            # Original strategies (more conservative) get higher weight
            original_buy_signals = sum([1 for signal in [macd_signal, bb_rsi_signal, stoch_williams_signal] if signal == "BUY"])
            original_sell_signals = sum([1 for signal in [macd_signal, bb_rsi_signal, stoch_williams_signal] if signal == "SELL"])
            
            # New strategies (more aggressive) get lower weight
            new_buy_signals = buy_signals - original_buy_signals
            new_sell_signals = sell_signals - original_sell_signals
            
            # Weighted decision: Original strategies count more
            weighted_buy_score = (original_buy_signals * 3) + new_buy_signals
            weighted_sell_score = (original_sell_signals * 3) + new_sell_signals
            
            # Strong signal conditions
            strong_buy_condition = (
                buy_signals >= 5 or  # At least 5 out of 16 signals (30% consensus)
                (original_buy_signals >= 2 and new_buy_signals >= 2) or  # 2 original + 2 new
                weighted_buy_score >= 8 or  # High weighted score
                (price_momentum > 1.5 and volume_spike and rsi_momentum > 8)  # Strong momentum
            )
            
            strong_sell_condition = (
                sell_signals >= 5 or  # At least 5 out of 16 signals (30% consensus)
                (original_sell_signals >= 2 and new_sell_signals >= 2) or  # 2 original + 2 new
                weighted_sell_score >= 8 or  # High weighted score
                (price_momentum < -1.5 and volume_spike and rsi_momentum < -8)  # Strong momentum
            )
            
            if strong_buy_condition:
                signal_reason = f"Technical signals: {buy_signals}/16 (Weighted: {weighted_buy_score})" if buy_signals >= 5 else "Strong momentum"
                logger.info(f"🟢 STRONG BUY signal for {symbol} - {signal_reason}")
                await self.update_account_balance()
                if self.account_balance is None or self.account_balance <= 0:
                    logger.warning(f"Cannot open new position for {symbol}: Insufficient balance")
                    return
                quantity = await self.calculate_position_size(symbol, current_price)
                if quantity is None:
                    logger.warning(f"Cannot open new position for {symbol}: Invalid position size")
                    return
                await self.place_order(symbol, SIDE_BUY, quantity)
            elif strong_sell_condition:
                signal_reason = f"Technical signals: {sell_signals}/16 (Weighted: {weighted_sell_score})" if sell_signals >= 5 else "Strong momentum"
                logger.info(f"🔴 STRONG SELL signal for {symbol} - {signal_reason}")
                await self.update_account_balance()
                if self.account_balance is None or self.account_balance <= 0:
                    logger.warning(f"Cannot open new position for {symbol}: Insufficient balance")
                    return
                quantity = await self.calculate_position_size(symbol, current_price)
                if quantity is None:
                    logger.warning(f"Cannot open new position for {symbol}: Invalid position size")
                    return
                await self.place_order(symbol, SIDE_SELL, quantity)
            else:
                logger.info(f"⚪ No clear signal for {symbol} (Buy: {buy_signals}/16, Sell: {sell_signals}/16, Weighted Buy: {weighted_buy_score}, Weighted Sell: {weighted_sell_score}, Momentum: {price_momentum:.2f}%)")
                
        except Exception as e:
            logger.error(f"Error checking market conditions for {symbol}: {str(e)}")
            await self.notification.notify(f"Error checking market conditions for {symbol}: {str(e)}")

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
            logger.info("Detailed Balance Information:")
            logger.info(f"Total Wallet Balance: {self.account_balance} USDT")
            logger.info(f"Available Balance: {available_balance} USDT")
            logger.info(f"Unrealized Profit: {unrealized_profit} USDT")
            logger.info(f"Margin Balance: {margin_balance} USDT")
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
            
            # Get symbol info for margin requirements
            symbol_info = await self.safe_api_call(self.client.futures_exchange_info)
            symbol_filters = next(filter(lambda x: x['symbol'] == symbol, symbol_info['symbols']))
            lot_size_filter = next(filter(lambda x: x['filterType'] == 'LOT_SIZE', symbol_filters['filters']))
            step_size = float(lot_size_filter['stepSize'])
            
            # Get margin requirements (usually 1/leverage for isolated margin)
            current_leverage = config.LEVERAGE
            margin_requirement = 1.0 / current_leverage  # 1/leverage for isolated margin
            
            if available_balance < config.MIN_BALANCE_THRESHOLD:
                # เทหมดหน้าตักสำหรับบัญชีเล็ก
                max_position_value = available_balance * current_leverage
                quantity = max_position_value / current_price
            else:
                max_position_value = (available_balance * config.POSITION_SIZE_BUFFER) * current_leverage
                quantity = max_position_value / current_price
            
            min_notional = config.MIN_NOTIONAL
            min_quantity = min_notional / current_price
            min_quantity = self.format_quantity(min_quantity, step_size)
            quantity = max(quantity, min_quantity)
            quantity = self.format_quantity(quantity, step_size)
            notional_value = quantity * current_price
            
            # Calculate required margin
            required_margin = notional_value * margin_requirement
            logger.info(f"Position calculation for {symbol}: Notional={notional_value:.2f} USDT, Required Margin={required_margin:.2f} USDT, Available={available_balance:.2f} USDT")
            
            # ถ้า notional ไม่ถึงขั้นต่ำ หรือ margin ไม่พอ ให้ลองเพิ่ม leverage อัตโนมัติ
            if notional_value < min_notional or required_margin > available_balance:
                logger.info(f"Starting leverage loop for {symbol}: Notional={notional_value:.2f} < {min_notional} OR Required Margin={required_margin:.2f} > Available={available_balance:.2f}")
                max_leverage = 125
                found = False
                for lev in range(int(current_leverage)+1, max_leverage+1):
                    logger.info(f"Testing leverage {lev}x for {symbol}")
                    margin_requirement = 1.0 / lev
                    
                    if available_balance < config.MIN_BALANCE_THRESHOLD:
                        max_position_value = available_balance * lev
                    else:
                        max_position_value = (available_balance * config.POSITION_SIZE_BUFFER) * lev
                    
                    test_quantity = max_position_value / current_price
                    test_quantity = max(test_quantity, min_quantity)
                    test_quantity = self.format_quantity(test_quantity, step_size)
                    test_notional = test_quantity * current_price
                    test_required_margin = test_notional * margin_requirement
                    
                    logger.info(f"Leverage {lev}x: Notional={test_notional:.2f} USDT, Required Margin={test_required_margin:.2f} USDT")
                    
                    if test_notional >= min_notional and test_required_margin <= available_balance:
                        # ตั้งค่า leverage ใหม่ผ่าน API
                        try:
                            await self.safe_api_call(self.client.futures_change_leverage, symbol=symbol, leverage=lev)
                            logger.info(f"✅ Auto-increased leverage for {symbol} to {lev}x to meet requirements.")
                            await self.notification.notify(f"🔄 Auto-increased leverage for {symbol} to {lev}x")
                        except Exception as e:
                            logger.error(f"Failed to set leverage: {e}")
                            await self.notification.notify(f"Failed to set leverage: {e}")
                            return None
                        quantity = test_quantity
                        notional_value = test_notional
                        found = True
                        break
                
                if not found:
                    logger.warning(f"ทุนต่ำเกินไป แม้จะใช้ leverage 125x แล้วก็ยังไม่ถึง requirements")
                    await self.notification.notify(
                        f"❌ ทุนต่ำเกินไป แม้จะใช้ leverage 125x แล้วก็ยังไม่ถึง requirements\n"
                        f"Notional: {notional_value:.2f} USDT (ขั้นต่ำ {min_notional} USDT)\n"
                        f"Required Margin: {required_margin:.2f} USDT (Available: {available_balance:.2f} USDT)"
                    )
                    return None
            
            min_buffer = min_notional + 5
            if notional_value < min_buffer:
                logger.warning(f"Position size too small for {symbol}: {notional_value:.2f} USDT")
                return None
            
            logger.info(f"✅ Final position size for {symbol}: {quantity} (Price: {current_price}, Notional: {notional_value:.2f} USDT)")
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
            ticker = await self.safe_api_call(self.client.futures_symbol_ticker, symbol=symbol)
            current_price = float(ticker['price'])
            calculated_quantity = await self.calculate_position_size(symbol, current_price)
            if calculated_quantity is None:
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Either insufficient balance or position size too small.\n"
                    f"Minimum order size: 20 USDT\n"
                    f"Current price: {current_price} USDT"
                )
                return
            quantity = min(quantity, calculated_quantity)
            if quantity <= 0:
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Calculated position size is too small.\n"
                    f"Minimum order size: 20 USDT\n"
                    f"Current price: {current_price} USDT"
                )
                return
            notional_value = quantity * current_price
            if notional_value < 20.0:
                await self.notification.notify(
                    f"❌ Cannot place order for {symbol}:\n"
                    f"Order size too small.\n"
                    f"Current notional value: {notional_value:.2f} USDT\n"
                    f"Minimum required: 20 USDT"
                )
                return
            order = await self.safe_api_call(
                self.client.futures_create_order,
                symbol=symbol,
                side=side,
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=quantity
            )
            entry_price = float(order['avgPrice'])
            position_side = "LONG" if side == SIDE_BUY else "SHORT"
            self.active_trades[symbol] = {
                'entry_price': entry_price,
                'position_side': position_side,
                'quantity': quantity,
                'trailing_stop': self.calculate_trailing_stop(
                    entry_price,
                    entry_price,
                    position_side
                ),
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
                f"New {position_side} position opened for {symbol}\n"
                f"Entry Price: {entry_price}\n"
                f"Quantity: {quantity}"
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
            trade['pnl'] = pnl
            await self.notification.notify(
                f"Position closed for {symbol}\n"
                f"Exit Price: {current_price}\n"
                f"P&L: {pnl:.2f} USDT"
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
        except Exception as e:
            logger.error(f"Failed to close position: {str(e)}")
            await self.notification.notify(f"Failed to close position: {str(e)}")

    async def setup_bot(self):
        """Async setup method to be called after bot creation"""
        await self.verify_api_connection()
        await self.update_account_balance()

    async def run(self):
        await self.setup_bot()
        await self.initialize()
        while True:
            try:
                self.send_heartbeat()
                
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
                "TrailingStop": trade.get("trailing_stop"),
            })
        with open("active_trades.json", "w") as f:
            json.dump(trades, f)

    def calculate_total_pnl(self):
        # This is a placeholder. You can implement real P&L calculation if you store trade history.
        return sum([trade.get("pnl", 0) for trade in self.active_trades.values()]) 