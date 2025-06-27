# Crypto Trading Bot - 20 Advanced Strategies

A sophisticated cryptocurrency trading bot that uses **20 advanced technical analysis strategies** to make trading decisions on Binance Futures.

## Features

- **20 Advanced Trading Strategies** combining multiple technical indicators
- **Priority Signals** for quick entry during strong market conditions
- **Real-time market monitoring** with 15-minute intervals
- **Automated position management** with trailing stops
- **Multi-channel notifications** (Telegram, Email, Discord)
- **Risk management** with configurable position sizing
- **Comprehensive logging** and trade history tracking
- **Weighted decision system** for optimal signal accuracy

## Trading Strategies

### Priority Strategies (Immediate Execution)

1. **Emergency Signal** 🚨
   - Quick entry when 2 out of 3 original strategies agree
   - Executes immediately without waiting for consensus
   - Perfect for catching fast-moving opportunities

2. **Strong Trend Signal** 📈
   - Detects markets with strong momentum
   - Requires: Price momentum > 2%, Volume > 130%, Range expansion > 120%
   - RSI and MACD momentum confirmation

3. **Breakout Signal** 🚀
   - Identifies price breakouts with volume confirmation
   - Triggers when price breaks above/below recent highs/lows
   - Volume must be 150% above average

4. **Momentum Acceleration Signal** ⚡
   - Detects accelerating price movements
   - Measures rate of change of rate of change
   - Volume and RSI acceleration confirmation

### Original Strategies (Conservative - 3x Weight)

5. **MACD + Trend Signal**
   - Uses MACD crossover with SMA trend confirmation
   - Bullish: MACD crosses above signal line + SMA20 > SMA50
   - Bearish: MACD crosses below signal line + SMA20 < SMA50

6. **Bollinger Bands + RSI**
   - Combines Bollinger Bands with RSI for entry/exit signals
   - Bullish: Price at lower band + RSI oversold (< 30)
   - Bearish: Price at upper band + RSI overbought (> 70)

7. **Stochastic + Williams %R**
   - Uses Stochastic Oscillator with Williams %R confirmation
   - Bullish: Stochastic oversold (< 20) + Williams %R oversold (< -80)
   - Bearish: Stochastic overbought (> 80) + Williams %R overbought (> -20)

### Aggressive Strategies (1x Weight)

8. **Fibonacci + RSI**
9. **Parabolic SAR + ADX**
10. **Keltner Channel + CCI**
11. **Pivot Points + RSI**
12. **Money Flow Index + Volume**
13. **ATR + Moving Average**
14. **RVI + Stochastic**
15. **CCI + Bollinger Bands**
16. **OBV + Price Action**
17. **Chaikin Money Flow + MACD**
18. **ROC + Moving Average Crossover**

## Decision Logic

### Priority Execution (Immediate)
- **Emergency Signal**: 2 out of 3 original strategies agree
- **Strong Trend Signal**: Multiple momentum indicators align
- **Breakout Signal**: Price breaks key levels with volume
- **Momentum Acceleration**: Price acceleration with confirmation

### Regular Execution (Consensus)
- **Original strategies** get 3x weight (more conservative and proven)
- **New strategies** get 1x weight (more aggressive and experimental)
- **Strong signal conditions**:
  - At least 5 out of 16 signals agree (30% consensus)
  - OR 2 original + 2 new signals
  - OR High weighted score (≥8)
  - OR Strong momentum with volume confirmation

### Signal Priority Order
1. **Priority Signals** (Emergency, Strong Trend, Breakout, Momentum Acceleration)
2. **Regular Consensus Signals** (16 strategies with weighted scoring)
3. **Momentum-based Signals** (Strong price/volume/RSI momentum)

## Configuration

Edit `bot_config.json` to customize:

```json
{
  "TRADING_PAIRS": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
  "LEVERAGE": 3,
  "TRAILING_STOP_PERCENTAGE": 1.0,
  "TAKE_PROFIT_PERCENTAGE": 2.0,
  "MIN_NOTIONAL": 20.0,
  "MIN_BALANCE_THRESHOLD": 100.0,
  "POSITION_SIZE_BUFFER": 0.9
}
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"
export TELEGRAM_BOT_TOKEN="your_telegram_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

3. Run the bot:
```bash
python main.py
```

## Risk Warning

This bot is for educational purposes. Cryptocurrency trading involves significant risk. Only trade with funds you can afford to lose.

## Technical Indicators Used

- **Moving Averages**: SMA 10, 25, 30, 60, EMA 5, 15
- **RSI**: 28-period with oversold/overbought levels
- **MACD**: 14,30,12 parameters
- **Bollinger Bands**: 20-period, 2 standard deviations
- **Stochastic**: 14-period with %K and %D
- **Williams %R**: 14-period
- **Volume SMA**: 35-period
- **Parabolic SAR**: 0.02 acceleration factor
- **ADX**: 14-period with DI+ and DI-
- **Keltner Channels**: 20-period, 2 ATR multiplier
- **CCI**: 20-period
- **Pivot Points**: Daily calculation
- **MFI**: 14-period
- **ATR**: 14-period
- **RVI**: 14-period
- **OBV**: On-Balance Volume
- **CMF**: 20-period
- **ROC**: 10-period
- **Fibonacci**: 23.6%, 38.2%, 50%, 61.8%, 78.6% levels

## Performance Monitoring

The bot tracks:
- Signal accuracy per strategy category
- Priority vs regular signal performance
- Win/loss ratios per strategy
- Average profit per trade
- Maximum drawdown
- Sharpe ratio
- Strategy correlation analysis
- Weighted score performance
