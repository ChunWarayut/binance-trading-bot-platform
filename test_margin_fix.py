#!/usr/bin/env python3
"""
Test script for aggressive leverage calculation
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_bot import TradingBot
from config import *

async def test_aggressive_leverage():
    """Test aggressive leverage calculation"""
    print("🚀 Testing Aggressive Leverage Calculation")
    print("=" * 50)
    
    bot = TradingBot()
    
    try:
        # Initialize bot
        await bot.initialize()
        print("✅ Bot initialized successfully")
        
        # Test symbols
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
        for symbol in test_symbols:
            print(f"\n📊 Testing {symbol}")
            print("-" * 30)
            
            try:
                # Get current price
                ticker = await bot.safe_api_call(bot.client.futures_symbol_ticker, symbol=symbol)
                current_price = float(ticker['price'])
                print(f"Current price: {current_price} USDT")
                
                # Get account balance
                await bot.update_account_balance()
                account = await bot.safe_api_call(bot.client.futures_account)
                available_balance = float(account['availableBalance'])
                print(f"Available balance: {available_balance:.2f} USDT")
                
                # Get coin recommendations
                coin_recommendations = await bot.get_coin_recommendations(symbol)
                position_size_multiplier = coin_recommendations.get('recommendations', {}).get('position_size_multiplier', 0.6)
                leverage_recommendation = coin_recommendations.get('recommendations', {}).get('leverage', {}).get('recommended', config.LEVERAGE)
                
                print(f"Position size multiplier: {position_size_multiplier}")
                print(f"Recommended leverage: {leverage_recommendation}x")
                
                # Test aggressive position size calculation
                print(f"🔄 Testing aggressive leverage loop...")
                quantity = await bot.calculate_position_size(symbol, current_price)
                
                if quantity is not None:
                    notional_value = quantity * current_price
                    
                    # Get final leverage
                    position_info = await bot.safe_api_call(bot.client.futures_position_information, symbol=symbol)
                    final_leverage = float(position_info[0]['leverage']) if position_info else leverage_recommendation
                    margin_requirement = 1.0 / final_leverage
                    required_margin = notional_value * margin_requirement
                    
                    print(f"✅ Position size calculated successfully")
                    print(f"Final leverage used: {final_leverage}x")
                    print(f"Quantity: {quantity}")
                    print(f"Notional value: {notional_value:.2f} USDT")
                    print(f"Required margin: {required_margin:.2f} USDT")
                    print(f"Margin ratio: {required_margin/available_balance*100:.1f}%")
                    
                    # Check if margin is sufficient
                    if required_margin <= available_balance:
                        print("✅ Margin is sufficient")
                    else:
                        print("❌ Margin is insufficient")
                        
                else:
                    print("❌ Could not calculate position size")
                    
            except Exception as e:
                print(f"❌ Error testing {symbol}: {e}")
                
    except Exception as e:
        print(f"❌ Error initializing bot: {e}")
    finally:
        # Cleanup
        if hasattr(bot, 'client') and bot.client:
            try:
                await bot.client.close_connection()
            except:
                pass

async def test_leverage_steps():
    """Test different leverage steps"""
    print("\n⚡ Testing Leverage Steps")
    print("=" * 30)
    
    bot = TradingBot()
    
    try:
        await bot.initialize()
        
        test_symbol = 'BTCUSDT'
        max_leverage = 125
        leverage_step = 5
        
        print(f"Testing leverage steps: {leverage_step}x increments up to {max_leverage}x")
        
        # Test leverage range
        for leverage in range(5, max_leverage + 1, leverage_step):
            try:
                await bot.safe_api_call(bot.client.futures_change_leverage, symbol=test_symbol, leverage=leverage)
                print(f"✅ Set leverage to {leverage}x successfully")
                
                # Verify leverage
                position_info = await bot.safe_api_call(bot.client.futures_position_information, symbol=test_symbol)
                current_leverage = float(position_info[0]['leverage'])
                print(f"Verified leverage: {current_leverage}x")
                
            except Exception as e:
                print(f"❌ Failed to set leverage {leverage}x: {e}")
                break
                
    except Exception as e:
        print(f"❌ Error testing leverage steps: {e}")
    finally:
        if hasattr(bot, 'client') and bot.client:
            try:
                await bot.client.close_connection()
            except:
                pass

async def test_balance_check():
    """Test balance checking functionality"""
    print("\n💰 Testing Balance Check")
    print("=" * 30)
    
    bot = TradingBot()
    
    try:
        await bot.initialize()
        
        # Test balance update
        await bot.update_account_balance()
        print(f"Account balance: {bot.account_balance}")
        
        # Test account info
        account = await bot.safe_api_call(bot.client.futures_account)
        available_balance = float(account['availableBalance'])
        total_balance = float(account['totalWalletBalance'])
        
        print(f"Available balance: {available_balance:.2f} USDT")
        print(f"Total balance: {total_balance:.2f} USDT")
        print(f"Used balance: {total_balance - available_balance:.2f} USDT")
        
        # Check if balance is sufficient for trading
        if available_balance >= 5:
            print("✅ Sufficient balance for trading")
        else:
            print("❌ Insufficient balance for trading")
            
    except Exception as e:
        print(f"❌ Error testing balance: {e}")
    finally:
        if hasattr(bot, 'client') and bot.client:
            try:
                await bot.client.close_connection()
            except:
                pass

async def main():
    """Run all tests"""
    print("🚀 Starting Aggressive Leverage Tests")
    print("=" * 50)
    
    await test_balance_check()
    await test_leverage_steps()
    await test_aggressive_leverage()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 