# Crypto Trading Bot - 20 Advanced Strategies + Coin Analysis System

A sophisticated cryptocurrency trading bot that uses **20 advanced technical analysis strategies** combined with an **intelligent coin analysis system** to make optimal trading decisions on Binance Futures.

## 🆕 New Feature: Coin Analysis System

The bot now includes an advanced **Coin Analysis System** that automatically determines:
- **Optimal Order Sizes** (Large, Medium, Small) for each coin
- **Recommended Leverage** (High, Medium, Low) based on market conditions
- **Dynamic Risk Management** with position limits and spacing
- **🆕 Multi-Timeframe Analysis** using 6 different timeframes in parallel

### 🪙 How Coin Analysis Works

The system analyzes each coin based on:
- **Volatility Analysis**: Price fluctuation patterns across multiple timeframes
- **Volume Analysis**: Trading volume and stability from 1m to 1d
- **Liquidity Analysis**: Market depth and spread analysis
- **Trend Strength Analysis**: Multi-timeframe trend confirmation
- **🆕 Parallel Processing**: Analyzes 6 timeframes simultaneously for faster results

### 📊 Coin Categories

#### 🔥 LARGE Orders (100% position size)
- **Criteria**: Low volatility (<2%), high volume (>1M), high liquidity (>70)
- **Examples**: BTC, ETH, BNB
- **Risk Level**: Low

#### ⚖️ MEDIUM Orders (60% position size)
- **Criteria**: Medium volatility (2-5%), balanced metrics
- **Examples**: SOL, XRP, ADA
- **Risk Level**: Medium

#### 🔴 SMALL Orders (30% position size)
- **Criteria**: High volatility (>5%), low volume, low liquidity
- **Examples**: DOGE, NEAR, ICP
- **Risk Level**: High

### 🚀 Leverage Recommendations

- **HIGH Leverage** (10-50x): Low volatility, strong momentum
- **MEDIUM Leverage** (5-20x): Balanced risk/reward
- **LOW Leverage** (1-10x): High volatility, conservative approach

### 🆕 Multi-Timeframe Analysis

The system now analyzes coins using **6 different timeframes** in parallel:

#### ⏰ Timeframes Used
- **1m**: Ultra-short term volatility and micro-trends
- **5m**: Short-term price movements and momentum
- **15m**: Medium-short term patterns and reversals
- **1h**: Primary analysis timeframe for daily trading
- **4h**: Medium-term trends and swing trading signals
- **1d**: Long-term trend confirmation and position sizing

#### 📊 Weighted Analysis
The system uses weighted averages with emphasis on longer timeframes:
- **1m**: 5% weight
- **5m**: 10% weight
- **15m**: 15% weight
- **1h**: 25% weight (Primary)
- **4h**: 25% weight (Primary)
- **1d**: 20% weight

#### ⚡ Parallel Processing
- **Concurrent API calls** to fetch data from all timeframes simultaneously
- **Parallel analysis** of multiple coins for faster results
- **Real-time updates** with comprehensive market insights

## Features

- **20 Advanced Trading Strategies** combining multiple technical indicators
- **🆕 Intelligent Coin Analysis System** for optimal position sizing
- **Priority Signals** for quick entry during strong market conditions
- **Real-time market monitoring** with 3-minute intervals
- **Automated position management** with trailing stops
- **Multi-channel notifications** (Telegram, Email, Discord)
- **Risk management** with configurable position sizing
- **Comprehensive logging** and trade history tracking
- **Weighted decision system** for optimal signal accuracy
- **🆕 Coin Analysis API** for external monitoring

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

## 🆕 Coin Analysis Usage

### Run Coin Analysis
```bash
# วิเคราะห์ครั้งเดียว
python run_coin_analysis.py

# วิเคราะห์ต่อเนื่อง (ทุกชั่วโมง)
python run_coin_analysis.py --continuous
```

### Test Coin Analysis
```bash
python test_coin_analysis.py
```

### 🆕 Test Multi-Timeframe Analysis
```bash
python test_multi_tf_analysis.py
```

### API Endpoints
```bash
# ดึงผลการวิเคราะห์ทั้งหมด
curl http://localhost:5001/api/coin-analysis

# ดึงผลการวิเคราะห์เหรียญเฉพาะ
curl http://localhost:5001/api/coin-analysis/BTCUSDT

# ดึงรายงานสรุป
curl http://localhost:5001/api/coin-analysis/summary

# ดึงคำแนะนำเฉพาะ
curl http://localhost:5001/api/coin-analysis/recommendations
```

### Docker Setup
```bash
# รันระบบทั้งหมดรวม coin analysis API
docker-compose up -d

# ดู logs ของ coin analysis API
docker-compose logs coin-analysis-api
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
- **🆕 Coin analysis accuracy and recommendations**

## 📚 Documentation

- [Coin Analysis System Documentation](COIN_ANALYSIS_README.md)
- [Strategy Examples](strategy_examples.md)
