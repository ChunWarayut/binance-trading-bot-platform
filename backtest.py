import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from loguru import logger
import config
from trading_bot import TradingBot
import asyncio
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class BacktestEngine:
    def __init__(self, start_date: str, end_date: str, initial_balance: float = 1000):
        """
        Initialize backtest engine
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            initial_balance: Initial balance in USDT
        """
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.trading_bot = TradingBot()
        self.trades = []
        self.daily_returns = []
        self.strategy_performance = {}
        self.signal_counts = {}
        
        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.max_drawdown = 0
        self.peak_balance = initial_balance
        
        # Strategy tracking
        self.strategy_signals = {
            'emergency': 0,
            'strong_trend': 0,
            'breakout': 0,
            'momentum_acceleration': 0,
            'regular_consensus': 0,
            'momentum_based': 0
        }
        
        self.strategy_wins = {
            'emergency': 0,
            'strong_trend': 0,
            'breakout': 0,
            'momentum_acceleration': 0,
            'regular_consensus': 0,
            'momentum_based': 0
        }

    async def get_historical_data(self, symbol: str, interval: str = '15m') -> pd.DataFrame:
        """Get historical data from Binance"""
        try:
            # Convert interval to Binance format
            interval_map = {
                '3m': '3m',
                '15m': '15m',
                '1h': '1h',
                '4h': '4h',
                '1d': '1d'
            }
            binance_interval = interval_map.get(interval, '3m')
            
            # Calculate total days needed
            days_diff = (self.end_date - self.start_date).days
            
            # Binance limit is 1000 candles per request
            max_candles_per_request = 1000
            
            # Calculate candles per day based on interval
            if interval == '3m':
                candles_per_day = 480
            elif interval == '15m':
                candles_per_day = 96
            elif interval == '1h':
                candles_per_day = 24
            elif interval == '4h':
                candles_per_day = 6
            else:  # 1d
                candles_per_day = 1
            
            # Calculate total candles needed
            total_candles_needed = days_diff * candles_per_day
            
            # Initialize empty DataFrame
            all_data = []
            
            # Calculate number of requests needed
            num_requests = (total_candles_needed + max_candles_per_request - 1) // max_candles_per_request
            
            logger.info(f"Fetching {total_candles_needed} candles in {num_requests} requests")
            
            # Fetch data in batches
            for i in range(num_requests):
                try:
                    # Calculate start time for this batch
                    if i == 0:
                        start_time = self.start_date
                    else:
                        # Calculate start time based on previous batch
                        candles_processed = i * max_candles_per_request
                        days_processed = candles_processed / candles_per_day
                        start_time = self.start_date + timedelta(days=days_processed)
                    
                    # Calculate end time for this batch
                    if i == num_requests - 1:
                        end_time = self.end_date
                    else:
                        # Calculate end time based on this batch
                        candles_in_batch = min(max_candles_per_request, total_candles_needed - (i * max_candles_per_request))
                        days_in_batch = candles_in_batch / candles_per_day
                        end_time = start_time + timedelta(days=days_in_batch)
                    
                    # Get historical data for this batch
                    klines = await self.trading_bot.safe_api_call(
                        self.trading_bot.client.futures_historical_klines,
                        symbol=symbol,
                        interval=binance_interval,
                        start_str=start_time.strftime('%Y-%m-%d'),
                        end_str=end_time.strftime('%Y-%m-%d'),
                        limit=max_candles_per_request
                    )
                    
                    if klines:
                        all_data.extend(klines)
                        logger.info(f"Batch {i+1}/{num_requests}: Got {len(klines)} candles")
                    else:
                        logger.warning(f"Batch {i+1}/{num_requests}: No data received")
                    
                    # Add small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error in batch {i+1}: {e}")
                    continue
            
            if not all_data:
                logger.error("No historical data received from any batch")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert data types
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].astype(float)
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Remove duplicates and sort by timestamp
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
            
            logger.info(f"Successfully loaded {len(df)} candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return pd.DataFrame()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        try:
            # Use the same indicator calculation as the trading bot
            return self.trading_bot.calculate_indicators(df)
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df

    def get_all_signals(self, df: pd.DataFrame, current_price: float) -> Dict:
        """Get all trading signals from the bot"""
        try:
            signals = {}
            
            # Original strategies
            signals['macd_trend'] = self.trading_bot.check_macd_trend_signal(df)
            signals['bb_rsi'] = self.trading_bot.check_bollinger_rsi_signal(df, current_price)
            signals['stoch_williams'] = self.trading_bot.check_stochastic_williams_signal(df)
            
            # Handle momentum signal which returns tuple
            try:
                momentum_result = self.trading_bot.check_momentum_signal(df)
                if isinstance(momentum_result, tuple) and len(momentum_result) == 3:
                    price_momentum, volume_spike, rsi_momentum = momentum_result
                    # Simplified momentum decision
                    if price_momentum and price_momentum > 1.5 and volume_spike and rsi_momentum and rsi_momentum > 8:
                        signals['momentum'] = "BUY"
                    elif price_momentum and price_momentum < -1.5 and volume_spike and rsi_momentum and rsi_momentum < -8:
                        signals['momentum'] = "SELL"
                    else:
                        signals['momentum'] = None
                else:
                    signals['momentum'] = None
            except:
                signals['momentum'] = None
            
            # Enhanced strategies (if they exist)
            try:
                signals['fibonacci_rsi'] = self.trading_bot.check_fibonacci_rsi_signal(df)
            except AttributeError:
                signals['fibonacci_rsi'] = None
                
            try:
                signals['parabolic_sar_adx'] = self.trading_bot.check_parabolic_sar_adx_signal(df)
            except AttributeError:
                signals['parabolic_sar_adx'] = None
                
            try:
                signals['volume_profile'] = self.trading_bot.check_volume_profile_signal(df)
            except AttributeError:
                signals['volume_profile'] = None
                
            try:
                signals['market_structure'] = self.trading_bot.check_market_structure_signal(df)
            except AttributeError:
                signals['market_structure'] = None
                
            try:
                signals['order_flow'] = self.trading_bot.check_order_flow_signal(df)
            except AttributeError:
                signals['order_flow'] = None
                
            try:
                signals['chaikin_money_flow_macd'] = self.trading_bot.check_chaikin_money_flow_macd_signal(df)
            except AttributeError:
                signals['chaikin_money_flow_macd'] = None
            
            # Priority signals
            try:
                signals['emergency'] = self.trading_bot.check_emergency_signal(df)
            except AttributeError:
                signals['emergency'] = None
                
            try:
                signals['strong_trend'] = self.trading_bot.check_strong_trend_signal(df)
            except AttributeError:
                signals['strong_trend'] = None
                
            try:
                signals['breakout'] = self.trading_bot.check_breakout_signal(df)
            except AttributeError:
                signals['breakout'] = None
                
            try:
                signals['momentum_acceleration'] = self.trading_bot.check_momentum_acceleration_signal(df)
            except AttributeError:
                signals['momentum_acceleration'] = None
            
            return signals
            
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return {}

    def determine_trade_signal(self, signals: Dict) -> Tuple[str, str]:
        """Determine final trade signal and strategy used"""
        try:
            # Check priority signals first
            priority_signals = ['emergency', 'strong_trend', 'breakout', 'momentum_acceleration']
            
            for strategy in priority_signals:
                if signals.get(strategy) == "BUY":
                    return "BUY", strategy
                elif signals.get(strategy) == "SELL":
                    return "SELL", strategy
            
            # Check regular consensus signals
            regular_signals = [
                'macd_trend', 'bb_rsi', 'stoch_williams', 'fibonacci_rsi', 'parabolic_sar_adx',
                'volume_profile', 'market_structure', 'order_flow', 'chaikin_money_flow_macd'
            ]
            
            buy_signals = sum([1 for signal in regular_signals if signals.get(signal) == "BUY"])
            sell_signals = sum([1 for signal in regular_signals if signals.get(signal) == "SELL"])
            
            # Original strategies (3x weight)
            original_signals = ['macd_trend', 'bb_rsi', 'stoch_williams']
            original_buy = sum([1 for signal in original_signals if signals.get(signal) == "BUY"])
            original_sell = sum([1 for signal in original_signals if signals.get(signal) == "SELL"])
            
            # New strategies (1x weight)
            new_buy = buy_signals - original_buy
            new_sell = sell_signals - original_sell
            
            # Weighted scores
            weighted_buy = (original_buy * 3) + new_buy
            weighted_sell = (original_sell * 3) + new_sell
            
            # Check momentum conditions
            momentum = signals.get('momentum', None)
            strong_buy_momentum = (
                momentum == "BUY"
            )
            strong_sell_momentum = (
                momentum == "SELL"
            )
            
            # Decision logic
            if (buy_signals >= 5 or 
                (original_buy >= 2 and new_buy >= 2) or 
                weighted_buy >= 8 or 
                strong_buy_momentum):
                return "BUY", "regular_consensus"
            elif (sell_signals >= 5 or 
                  (original_sell >= 2 and new_sell >= 2) or 
                  weighted_sell >= 8 or 
                  strong_sell_momentum):
                return "SELL", "regular_consensus"
            elif strong_buy_momentum:
                return "BUY", "momentum_based"
            elif strong_sell_momentum:
                return "SELL", "momentum_based"
            
            return "NONE", "no_signal"
            
        except Exception as e:
            logger.error(f"Error determining trade signal: {e}")
            return "NONE", "error"

    def execute_trade(self, signal: str, entry_price: float, timestamp: datetime, strategy: str) -> Dict:
        """Execute a trade and return trade details"""
        try:
            # Calculate position size (simplified for backtest)
            position_size = (self.current_balance * 0.1) / entry_price  # 10% of balance
            
            trade = {
                'timestamp': timestamp,
                'signal': signal,
                'entry_price': entry_price,
                'position_size': position_size,
                'strategy': strategy,
                'balance_before': self.current_balance
            }
            
            return trade
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return {}

    def close_trade(self, trade: Dict, exit_price: float, timestamp: datetime) -> float:
        """Close a trade and calculate P&L"""
        try:
            if trade['signal'] == "BUY":
                pnl = (exit_price - trade['entry_price']) * trade['position_size']
            else:  # SELL
                pnl = (trade['entry_price'] - exit_price) * trade['position_size']
            
            # Update balance
            self.current_balance += pnl
            
            # Update trade record
            trade['exit_price'] = exit_price
            trade['exit_timestamp'] = timestamp
            trade['pnl'] = pnl
            trade['balance_after'] = self.current_balance
            
            # Update statistics
            self.total_trades += 1
            if pnl > 0:
                self.winning_trades += 1
                self.strategy_wins[trade['strategy']] += 1
            else:
                self.losing_trades += 1
            
            # Update peak balance and drawdown
            if self.current_balance > self.peak_balance:
                self.peak_balance = self.current_balance
            else:
                drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
                if drawdown > self.max_drawdown:
                    self.max_drawdown = drawdown
            
            return pnl
            
        except Exception as e:
            logger.error(f"Error closing trade: {e}")
            return 0

    async def run_backtest(self, symbol: str, interval: str = '3m') -> Dict:
        """Run complete backtest"""
        try:
            logger.info(f"Starting backtest for {symbol} from {self.start_date} to {self.end_date}")
            
            # Get historical data
            df = await self.get_historical_data(symbol, interval)
            if df.empty:
                logger.error("No historical data available")
                return {}
            
            logger.info(f"Loaded {len(df)} candles for backtest")
            
            # Initialize variables
            current_position = None
            current_trade = None
            
            # Process each candle
            for i in range(100, len(df)):  # Start from 100 to have enough data for indicators
                try:
                    # Get current data window
                    current_df = df.iloc[:i+1].copy()
                    current_price = float(current_df['close'].iloc[-1])
                    current_timestamp = current_df['timestamp'].iloc[-1]
                    
                    # Calculate indicators
                    current_df = self.calculate_indicators(current_df)
                    
                    # Get all signals
                    signals = self.get_all_signals(current_df, current_price)
                    
                    # Determine trade signal
                    signal, strategy = self.determine_trade_signal(signals)
                    
                    # Track signal counts
                    if signal and signal != "NONE":
                        self.strategy_signals[strategy] += 1
                    
                    # Execute trades
                    if signal and signal != "NONE" and current_position is None:
                        # Open new position
                        current_trade = self.execute_trade(signal, current_price, current_timestamp, strategy)
                        current_position = signal
                        self.trades.append(current_trade)
                        logger.info(f"Opened {signal} position at {current_price} using {strategy}")
                        
                    elif current_position and current_trade:
                        # Check exit conditions (simplified - exit after 10 candles or on opposite signal)
                        candles_held = i - len([t for t in self.trades if t == current_trade])
                        exit_condition = (
                            (signal and signal != "NONE" and signal != current_position) or  # Opposite signal
                            candles_held >= 10  # Time-based exit
                        )
                        
                        if exit_condition:
                            # Close position
                            pnl = self.close_trade(current_trade, current_price, current_timestamp)
                            logger.info(f"Closed {current_position} position at {current_price}, P&L: {pnl:.2f}")
                            
                            # Reset position
                            current_position = None
                            current_trade = None
                    
                    # Track daily returns
                    if i % 96 == 0:  # Daily (96 candles for 15m)
                        daily_return = (self.current_balance - self.initial_balance) / self.initial_balance
                        self.daily_returns.append({
                            'date': current_timestamp.date(),
                            'balance': self.current_balance,
                            'return': daily_return
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing candle {i}: {e}")
                    continue
            
            # Close any remaining position
            if current_position and current_trade:
                final_price = float(df['close'].iloc[-1])
                final_timestamp = df['timestamp'].iloc[-1]
                pnl = self.close_trade(current_trade, final_price, final_timestamp)
                logger.info(f"Closed final position, P&L: {pnl:.2f}")
            
            # Calculate final statistics
            return self.calculate_statistics()
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {}

    def calculate_statistics(self) -> Dict:
        """Calculate comprehensive backtest statistics"""
        try:
            # Basic statistics
            total_return = (self.current_balance - self.initial_balance) / self.initial_balance * 100
            win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            
            # Calculate average trade metrics
            if self.trades:
                avg_win = np.mean([t['pnl'] for t in self.trades if t['pnl'] > 0]) if any(t['pnl'] > 0 for t in self.trades) else 0
                avg_loss = np.mean([t['pnl'] for t in self.trades if t['pnl'] < 0]) if any(t['pnl'] < 0 for t in self.trades) else 0
                profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            else:
                avg_win = avg_loss = profit_factor = 0
            
            # Strategy performance
            strategy_performance = {}
            for strategy, signals in self.strategy_signals.items():
                if signals > 0:
                    win_rate_strategy = (self.strategy_wins[strategy] / signals * 100)
                    strategy_performance[strategy] = {
                        'signals': signals,
                        'wins': self.strategy_wins[strategy],
                        'win_rate': win_rate_strategy
                    }
            
            # Calculate Sharpe ratio (simplified)
            if self.daily_returns:
                returns = [d['return'] for d in self.daily_returns]
                sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
            else:
                sharpe_ratio = 0
            
            return {
                'initial_balance': self.initial_balance,
                'final_balance': self.current_balance,
                'total_return_pct': total_return,
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate_pct': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'max_drawdown_pct': self.max_drawdown * 100,
                'sharpe_ratio': sharpe_ratio,
                'strategy_performance': strategy_performance,
                'strategy_signals': self.strategy_signals,
                'trades': self.trades,
                'daily_returns': self.daily_returns
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}

    def generate_report(self, results: Dict, output_file: str = 'backtest_report.json'):
        """Generate comprehensive backtest report"""
        try:
            # Save detailed results
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            # Generate summary report
            summary = f"""
=== BACKTEST REPORT ===
Period: {self.start_date.date()} to {self.end_date.date()}
Symbol: {results.get('symbol', 'Unknown')}

PERFORMANCE METRICS:
- Initial Balance: ${results.get('initial_balance', 0):,.2f}
- Final Balance: ${results.get('final_balance', 0):,.2f}
- Total Return: {results.get('total_return_pct', 0):.2f}%
- Total Trades: {results.get('total_trades', 0)}
- Win Rate: {results.get('win_rate_pct', 0):.2f}%
- Profit Factor: {results.get('profit_factor', 0):.2f}
- Max Drawdown: {results.get('max_drawdown_pct', 0):.2f}%
- Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}

STRATEGY PERFORMANCE:
"""
            
            for strategy, perf in results.get('strategy_performance', {}).items():
                summary += f"- {strategy}: {perf['signals']} signals, {perf['win_rate']:.2f}% win rate\n"
            
            # Save summary
            with open('backtest_summary.txt', 'w') as f:
                f.write(summary)
            
            logger.info(f"Backtest report saved to {output_file}")
            logger.info(f"Summary saved to backtest_summary.txt")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return ""

    def plot_results(self, results: Dict):
        """Generate performance charts"""
        try:
            # Create figure with subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 1. Balance over time
            if results.get('daily_returns'):
                dates = [d['date'] for d in results['daily_returns']]
                balances = [d['balance'] for d in results['daily_returns']]
                ax1.plot(dates, balances)
                ax1.set_title('Account Balance Over Time')
                ax1.set_xlabel('Date')
                ax1.set_ylabel('Balance (USDT)')
                ax1.grid(True)
            
            # 2. Strategy performance
            strategies = list(results.get('strategy_performance', {}).keys())
            win_rates = [results['strategy_performance'][s]['win_rate'] for s in strategies]
            ax2.bar(strategies, win_rates)
            ax2.set_title('Strategy Win Rates')
            ax2.set_xlabel('Strategy')
            ax2.set_ylabel('Win Rate (%)')
            ax2.tick_params(axis='x', rotation=45)
            
            # 3. Trade P&L distribution
            if results.get('trades'):
                pnls = [t['pnl'] for t in results['trades']]
                ax3.hist(pnls, bins=20, alpha=0.7)
                ax3.set_title('Trade P&L Distribution')
                ax3.set_xlabel('P&L (USDT)')
                ax3.set_ylabel('Frequency')
                ax3.axvline(0, color='red', linestyle='--')
            
            # 4. Strategy signal counts
            signal_counts = results.get('strategy_signals', {})
            ax4.bar(signal_counts.keys(), signal_counts.values())
            ax4.set_title('Strategy Signal Counts')
            ax4.set_xlabel('Strategy')
            ax4.set_ylabel('Number of Signals')
            ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.savefig('backtest_results.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            logger.info("Performance charts saved to backtest_results.png")
            
        except Exception as e:
            logger.error(f"Error plotting results: {e}")

async def main():
    """Main function to run backtest"""
    try:
        # Initialize backtest engine
        backtest = BacktestEngine(
            start_date='2024-01-01',
            end_date='2025-06-30',
            initial_balance=1000
        )
        
        # Run backtest for multiple symbols
        symbols = [
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "SOLUSDT",
            "XRPUSDT",
            "ADAUSDT",
            "DOGEUSDT",
            "AVAXUSDT",
            "DOTUSDT",
            "LTCUSDT",
            "LINKUSDT",
            "BCHUSDT",
            "NEARUSDT",
            "ICPUSDT"
        ]
        
        for symbol in symbols:
            logger.info(f"Running backtest for {symbol}")
            results = await backtest.run_backtest(symbol, interval='1h')
            
            if results:
                # Generate report
                summary = backtest.generate_report(results, f'backtest_report_{symbol}.json')
                print(summary)
                
                # Generate plots
                backtest.plot_results(results)
                
                # Reset for next symbol
                backtest.current_balance = backtest.initial_balance
                backtest.trades = []
                backtest.daily_returns = []
                backtest.strategy_signals = {k: 0 for k in backtest.strategy_signals}
                backtest.strategy_wins = {k: 0 for k in backtest.strategy_wins}
                backtest.total_trades = 0
                backtest.winning_trades = 0
                backtest.losing_trades = 0
                backtest.max_drawdown = 0
                backtest.peak_balance = backtest.initial_balance
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 