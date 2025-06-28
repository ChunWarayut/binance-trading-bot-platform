#!/usr/bin/env python3
"""
Test script specifically for BTCUSDT aggressive leverage
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_bot import TradingBot

async def test_btc_aggressive_leverage():
    """Test aggressive leverage specifically for BTCUSDT"""
    print("🚀 Testing BTCUSDT Aggressive Leverage")
    print("=" * 50)
    
    bot = TradingBot()
    
    try:
        # Initialize bot
        await bot.initialize()
        print("✅ Bot initialized successfully")
        
        symbol = 'BTCUSDT'
        
        # Get current price
        ticker = await bot.safe_api_call(bot.client.futures_symbol_ticker, symbol=symbol)
        current_price = float(ticker['price'])
        print(f"Current BTC price: {current_price} USDT")
        
        # Get account balance
        await bot.update_account_balance()
        account = await bot.safe_api_call(bot.client.futures_account)
        available_balance = float(account['availableBalance'])
        print(f"Available balance: {available_balance:.2f} USDT")
        
        # Test aggressive position size calculation
        print(f"🔄 Testing aggressive leverage loop for BTCUSDT...")
        quantity = await bot.calculate_position_size(symbol, current_price)
        
        if quantity is not None:
            notional_value = quantity * current_price
            
            # Get final leverage
            position_info = await bot.safe_api_call(bot.client.futures_position_information, symbol=symbol)
            final_leverage = float(position_info[0]['leverage']) if position_info else 3
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
                
                # Test placing order
                print(f"🔄 Testing order placement...")
                order_result = await bot.place_order(symbol, 'BUY', 0)  # Use 0 to let calculate_position_size handle it
                
                if order_result:
                    print("✅ Order placed successfully!")
                else:
                    print("❌ Order placement failed")
            else:
                print("❌ Margin is insufficient")
                
        else:
            print("❌ Could not calculate position size")
            
    except Exception as e:
        print(f"❌ Error testing BTCUSDT: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if hasattr(bot, 'client') and bot.client:
            try:
                await bot.client.close_connection()
            except:
                pass

async def main():
    """Run BTCUSDT test"""
    await test_btc_aggressive_leverage()
    print("\n✅ BTCUSDT test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 