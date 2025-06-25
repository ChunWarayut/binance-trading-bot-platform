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
        
        # Calculate Volume SMA with longer period
        df['volume_sma20'] = df.ta.sma(length=35, close='volume')  # Changed from 30 to 35
        
        return df

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
            df = self.calculate_indicators(df)
            current_rsi = df['rsi'].iloc[-1]
            logger.info(f"Monitoring {symbol} - Price: {current_price}, RSI: {current_rsi:.2f}")
            # await self.send_technical_indicators(symbol, current_price, current_rsi)
            if symbol in self.active_trades:
                await self.check_trailing_stop(symbol)
                return
            if current_rsi < 30:
                await self.update_account_balance()
                if self.account_balance is None or self.account_balance <= 0:
                    logger.warning(f"Cannot open new position for {symbol}: Insufficient balance")
                    return
                quantity = await self.calculate_position_size(symbol, current_price)
                if quantity is None:
                    logger.warning(f"Cannot open new position for {symbol}: Invalid position size")
                    return
                await self.place_order(symbol, SIDE_BUY, quantity)
            elif current_rsi > 70:
                await self.update_account_balance()
                if self.account_balance is None or self.account_balance <= 0:
                    logger.warning(f"Cannot open new position for {symbol}: Insufficient balance")
                    return
                quantity = await self.calculate_position_size(symbol, current_price)
                if quantity is None:
                    logger.warning(f"Cannot open new position for {symbol}: Invalid position size")
                    return
                await self.place_order(symbol, SIDE_SELL, quantity)
        except Exception as e:
            logger.error(f"Error checking market conditions for {symbol}: {str(e)}")
            await self.notification.notify(f"Error checking market conditions for {symbol}: {str(e)}")

    def calculate_trailing_stop(self, entry_price, current_price, position_side):
        if position_side == "LONG":
            return current_price * (1 - config.TRAILING_STOP_PERCENTAGE / 100)
        else:
            return current_price * (1 + config.TRAILING_STOP_PERCENTAGE / 100)

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
            max_position_value = (available_balance * config.POSITION_SIZE_BUFFER) * config.LEVERAGE
            quantity = max_position_value / current_price
            symbol_info = await self.safe_api_call(self.client.futures_exchange_info)
            symbol_filters = next(filter(lambda x: x['symbol'] == symbol, symbol_info['symbols']))
            lot_size_filter = next(filter(lambda x: x['filterType'] == 'LOT_SIZE', symbol_filters['filters']))
            step_size = float(lot_size_filter['stepSize'])
            min_notional = config.MIN_NOTIONAL
            min_quantity = min_notional / current_price
            min_quantity = float(int(min_quantity / step_size + 1) * step_size)
            if available_balance < config.MIN_BALANCE_THRESHOLD:
                max_quantity = (available_balance * config.SMALL_ACCOUNT_POSITION_LIMIT) / current_price
                quantity = min(quantity, max_quantity)
            quantity = max(quantity, min_quantity)
            quantity = float(int(quantity / step_size) * step_size)
            notional_value = quantity * current_price
            if notional_value < min_notional:
                logger.warning(f"Calculated position size {quantity} for {symbol} results in notional value {notional_value} USDT, which is below minimum {min_notional} USDT")
                return None
            min_buffer = min_notional + 5
            if notional_value < min_buffer:
                logger.warning(f"Position size too small for {symbol}: {notional_value:.2f} USDT")
                return None
            logger.info(f"Calculated position size for {symbol}: {quantity} (Price: {current_price}, Notional: {notional_value:.2f} USDT)")
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

    async def check_trailing_stop(self, symbol):
        if symbol not in self.active_trades:
            return
        trade = self.active_trades[symbol]
        ticker = await self.safe_api_call(self.client.futures_symbol_ticker, symbol=symbol)
        current_price = float(ticker['price'])
        new_trailing_stop = self.calculate_trailing_stop(
            trade['entry_price'],
            current_price,
            trade['position_side']
        )
        if trade['position_side'] == "LONG" and new_trailing_stop > trade['trailing_stop']:
            trade['trailing_stop'] = new_trailing_stop
        elif trade['position_side'] == "SHORT" and new_trailing_stop < trade['trailing_stop']:
            trade['trailing_stop'] = new_trailing_stop
        if (trade['position_side'] == "LONG" and current_price <= trade['trailing_stop']) or \
           (trade['position_side'] == "SHORT" and current_price >= trade['trailing_stop']):
            self.log_trade_activity(
                event="Trailing Stop Hit",
                symbol=symbol,
                side=trade['position_side'],
                price=current_price,
                reason="Trailing Stop"
            )
            await self.close_position(symbol)

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