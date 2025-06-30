#!/usr/bin/env python3
"""
Test script to verify backtest engine works with enhanced strategies
"""

import asyncio
import sys
import logging
from datetime import datetime
from backtest import BacktestEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_backtest():
    """Test the backtest engine with a short period"""
    try:
        print("🧪 Testing Enhanced Backtest Engine...")
        print("=" * 50)
        
        # Create backtest engine
        engine = BacktestEngine('2024-01-01', '2024-01-15', 1000)
        
        # Run backtest on BTC with 1-hour intervals
        print("📊 Running backtest on BTCUSDT (1h intervals)...")
        result = await engine.run_backtest('BTCUSDT', '1h')
        
        if result:
            print("\n✅ Backtest completed successfully!")
            print(f"📈 Total trades: {result.get('total_trades', 0)}")
            print(f"💰 Final balance: ${result.get('final_balance', 0):,.2f}")
            print(f"📊 Return: {result.get('total_return_pct', 0):.2f}%")
            print(f"🎯 Win rate: {result.get('win_rate_pct', 0):.2f}%")
            print(f"📉 Max drawdown: {result.get('max_drawdown_pct', 0):.2f}%")
            
            # Show strategy performance
            strategy_perf = result.get('strategy_performance', {})
            if strategy_perf:
                print("\n📋 Strategy Performance:")
                for strategy, perf in strategy_perf.items():
                    print(f"  • {strategy}: {perf['signals']} signals, {perf['win_rate']:.1f}% win rate")
            
            print("\n🎉 Test completed successfully!")
            return True
        else:
            print("❌ Backtest failed - no results returned")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        logger.error(f"Backtest test error: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_backtest())
    sys.exit(0 if success else 1) 