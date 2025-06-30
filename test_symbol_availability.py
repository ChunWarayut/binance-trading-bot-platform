#!/usr/bin/env python3
"""
Test script to verify which trading pairs from bot_config.json are available for futures trading
"""

import asyncio
import json
import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_symbol_availability():
    """Test which symbols are available for futures trading"""
    
    # Load config
    with open('bot_config.json', 'r') as f:
        config = json.load(f)
    
    trading_pairs = config.get('TRADING_PAIRS', [])
    logger.info(f"Testing {len(trading_pairs)} trading pairs for futures availability")
    
    # Initialize client (no API keys needed for public endpoints)
    client = Client("", "")
    
    try:
        # Get all available futures symbols
        exchange_info = client.futures_exchange_info()
        available_symbols = {s['symbol']: s for s in exchange_info['symbols'] if s['status'] == 'TRADING'}
        
        logger.info(f"Found {len(available_symbols)} symbols available for futures trading")
        
        # Test each trading pair
        available_pairs = []
        unavailable_pairs = []
        
        for symbol in trading_pairs:
            if symbol in available_symbols:
                available_pairs.append(symbol)
                logger.info(f"✅ {symbol} - Available")
            else:
                unavailable_pairs.append(symbol)
                logger.warning(f"❌ {symbol} - Not available for futures trading")
        
        # Summary
        logger.info(f"\n=== SUMMARY ===")
        logger.info(f"Available pairs: {len(available_pairs)}/{len(trading_pairs)}")
        logger.info(f"Unavailable pairs: {len(unavailable_pairs)}")
        
        if unavailable_pairs:
            logger.info(f"\nUnavailable pairs:")
            for pair in unavailable_pairs:
                logger.info(f"  - {pair}")
        
        # Test leverage setting for a few available pairs
        logger.info(f"\n=== TESTING LEVERAGE SETTING ===")
        test_pairs = available_pairs[:5]  # Test first 5 available pairs
        
        for symbol in test_pairs:
            try:
                # Try to get current leverage
                leverage_info = client.futures_leverage_bracket(symbol=symbol)
                current_leverage = leverage_info[0]['brackets'][0]['initialLeverage']
                logger.info(f"✅ {symbol} - Current leverage: {current_leverage}x")
            except BinanceAPIException as e:
                logger.error(f"❌ {symbol} - Leverage error: {e}")
            except Exception as e:
                logger.error(f"❌ {symbol} - Unexpected error: {e}")
        
        return available_pairs, unavailable_pairs
        
    except Exception as e:
        logger.error(f"Error testing symbol availability: {e}")
        return [], []

if __name__ == "__main__":
    asyncio.run(test_symbol_availability()) 