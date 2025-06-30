#!/usr/bin/env python3
import json
import time
import os
from datetime import datetime

def show_bot_dashboard():
    os.system('clear')
    print('=' * 60)
    print('🚀 CRYPTO TRADING BOT - LIVE DASHBOARD')
    print('=' * 60)
    print(f'⏰ Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('-' * 60)
    
    # Bot Status
    try:
        with open('bot_status.json', 'r') as f:
            status = json.load(f)
        running = status.get('running', False)
        print(f'📊 Status: {"🟢 RUNNING" if running else "🔴 STOPPED"}')
        print(f'📈 Active Trades: {status.get("active_trades_count", 0)}')
        print(f'💰 Total P&L: ${status.get("total_pnl", 0):.2f}')
        print(f'🕒 Last Update: {status.get("last_update", "N/A")}')
    except Exception as e:
        print(f'❌ Unable to read bot status: {e}')
    
    print('-' * 60)
    
    # Active Trades
    try:
        with open('active_trades.json', 'r') as f:
            trades = json.load(f)
        if trades:
            print('📋 ACTIVE TRADES:')
            for i, trade in enumerate(trades, 1):
                symbol = trade.get('Symbol', 'N/A')
                side = trade.get('Side', 'N/A')
                entry = trade.get('Entry', 0)
                qty = trade.get('Quantity', 0)
                print(f'  {i}. {symbol}: {side} | Entry: ${entry} | Qty: {qty}')
        else:
            print('📋 No active trades')
    except Exception as e:
        print(f'❌ Unable to read active trades: {e}')
    
    print('-' * 60)
    
    # Trading Pairs Count
    try:
        import config
        print(f'🎯 Trading Pairs: {len(config.TRADING_PAIRS)} pairs')
        print(f'🔥 Top 5: {", ".join(config.TRADING_PAIRS[:5])}')
    except:
        print('⚠️ Config not available')
    
    print('-' * 60)
    print('🔗 Access Points:')
    print('   💻 Web Dashboard: http://localhost:8501')
    print('   🌐 API Status: http://localhost:8080')
    print('   📊 Logs: tail -f logs/trading_bot.log')
    print('=' * 60)
    print('Press Ctrl+C to exit')

if __name__ == "__main__":
    try:
        while True:
            show_bot_dashboard()
            time.sleep(5)  # Update every 5 seconds
    except KeyboardInterrupt:
        print('\n👋 Dashboard closed. Bot continues running!') 