# 16 Trading Strategy Examples

This document provides detailed examples of how each of the 16 trading strategies works in practice.

**Timeframe**: All strategies operate on 3-minute candlesticks for high-frequency trading and quick signal generation.

## Conservative Strategies (3x Weight)

### 1. MACD + Trend Signal

**Bullish Signal Example:**
```
Current MACD: 0.0025
Previous MACD: 0.0018
Current Signal: 0.0020
Previous Signal: 0.0022
SMA20: 45,250
SMA50: 44,800

Analysis:
- MACD crossed above signal line (0.0025 > 0.0020, 0.0018 < 0.0022)
- SMA20 > SMA50 (45,250 > 44,800)
- Result: BUY signal (Weight: 3x)
```

### 2. Bollinger Bands + RSI

**Bullish Signal Example:**
```
Current Price: 44,500
Bollinger Upper: 46,200
Bollinger Lower: 43,800
Current RSI: 28

Analysis:
- Price at lower band (44,500 ≈ 43,800)
- RSI oversold (28 < 30)
- Result: BUY signal (Weight: 3x)
```

### 3. Stochastic + Williams %R

**Bullish Signal Example:**
```
Stochastic %K: 18
Williams %R: -85

Analysis:
- Stochastic oversold (18 < 20)
- Williams %R oversold (-85 < -80)
- Result: BUY signal (Weight: 3x)
```

## Aggressive Strategies (1x Weight)

### 4. Fibonacci + RSI

**Bullish Signal Example:**
```
Current RSI: 25

Analysis:
- RSI oversold (25 < 30)
- Result: BUY signal (Weight: 1x)
```

### 5. Parabolic SAR + ADX

**Bullish Signal Example:**
```
Current Price: 45,500
Parabolic SAR: 44,800
ADX: 28
DI+: 25
DI-: 15

Analysis:
- Price above SAR (45,500 > 44,800)
- DI+ > DI- (25 > 15)
- ADX > 25 (28 > 25)
- Result: BUY signal (Weight: 1x)
```

### 6. Keltner Channel + CCI

**Bullish Signal Example:**
```
Current Price: 44,200
Keltner Upper: 45,800
Keltner Lower: 44,000
CCI: -120

Analysis:
- Price at lower channel (44,200 ≈ 44,000)
- CCI oversold (-120 < -100)
- Result: BUY signal (Weight: 1x)
```

### 7. Pivot Points + RSI

**Bullish Signal Example:**
```
Current Price: 44,500
Support Level (S1): 44,400
Current RSI: 28

Analysis:
- Price near support (44,500 ≈ 44,400)
- RSI oversold (28 < 30)
- Result: BUY signal (Weight: 1x)
```

### 8. Money Flow Index + Volume

**Bullish Signal Example:**
```
MFI: 18
Current Volume: 1,500,000
Average Volume: 800,000

Analysis:
- MFI oversold (18 < 20)
- High volume (1,500,000 > 1,200,000)
- Result: BUY signal (Weight: 1x)
```

### 9. ATR + Moving Average

**Bullish Signal Example:**
```
Current ATR: 850
Average ATR: 600
SMA10: 45,200
SMA30: 44,800
Current Price: 45,300

Analysis:
- High volatility (850 > 600)
- SMA10 > SMA30 (45,200 > 44,800)
- Price > SMA10 (45,300 > 45,200)
- Result: BUY signal (Weight: 1x)
```

### 10. RVI + Stochastic

**Bullish Signal Example:**
```
Current RVI: 0.15
Previous RVI: 0.10
Stochastic %K: 18
Stochastic %D: 20

Analysis:
- RVI momentum > 0 (0.15 - 0.10 = 0.05 > 0)
- Stochastic oversold (18 < 20, 20 < 20)
- Result: BUY signal (Weight: 1x)
```

### 11. CCI + Bollinger Bands

**Bullish Signal Example:**
```
Current Price: 44,000
Bollinger Lower: 44,100
CCI: -220

Analysis:
- Price at lower band (44,000 ≈ 44,100)
- CCI extreme oversold (-220 < -200)
- Result: BUY signal (Weight: 1x)
```

### 12. OBV + Price Action

**Bullish Signal Example:**
```
Current Price: 45,500
Previous Price: 45,200
Current OBV: 1,250,000
OBV SMA: 1,200,000
Current Volume: 900,000
Average Volume: 800,000

Analysis:
- Price up (45,500 > 45,200)
- OBV > OBV SMA (1,250,000 > 1,200,000)
- Volume confirmation (900,000 > 800,000)
- Result: BUY signal (Weight: 1x)
```

### 13. Chaikin Money Flow + MACD

**Bullish Signal Example:**
```
CMF: 0.15
MACD: 0.0025
MACD Signal: 0.0020

Analysis:
- CMF bullish (0.15 > 0.1)
- MACD > Signal (0.0025 > 0.0020)
- Result: BUY signal (Weight: 1x)
```

### 14. ROC + Moving Average Crossover

**Bullish Signal Example:**
```
Current ROC: 2.5
Previous ROC: 1.8
Current EMA5: 45,300
Current EMA15: 45,100
Previous EMA5: 45,000
Previous EMA15: 45,200

Analysis:
- ROC momentum > 0 (2.5 - 1.8 = 0.7 > 0)
- EMA5 crosses above EMA15 (45,300 > 45,100, 45,000 < 45,200)
- Result: BUY signal (Weight: 1x)
```

## Decision Making Examples

### Example 1: Strong Buy Signal (Multiple Strategies)

```
Signals:
- MACD + Trend: BUY (3x weight)
- Bollinger + RSI: BUY (3x weight)
- Stochastic + Williams: None
- Fibonacci + RSI: BUY (1x weight)
- Parabolic + ADX: BUY (1x weight)
- Keltner + CCI: None
- Pivot + RSI: BUY (1x weight)
- MFI + Volume: None
- ATR + MA: None
- RVI + Stoch: None
- CCI + BB: None
- OBV + Price: None
- CMF + MACD: None
- ROC + MA: None

Analysis:
- Buy signals: 5/16
- Original buy signals: 2/3
- New buy signals: 3/13
- Weighted score: (2×3) + 3 = 9

Result: STRONG BUY (5 out of 16 signals + high weighted score)
```

### Example 2: Conservative Signal (Original Strategies Only)

```
Signals:
- MACD + Trend: BUY (3x weight)
- Bollinger + RSI: BUY (3x weight)
- Stochastic + Williams: BUY (3x weight)
- All other strategies: None

Analysis:
- Buy signals: 3/16
- Original buy signals: 3/3
- New buy signals: 0/13
- Weighted score: (3×3) + 0 = 9

Result: STRONG BUY (3 original signals = high weighted score)
```

### Example 3: No Clear Signal

```
Signals:
- MACD + Trend: None
- Bollinger + RSI: BUY (3x weight)
- Stochastic + Williams: None
- Fibonacci + RSI: None
- Parabolic + ADX: None
- Keltner + CCI: SELL (1x weight)
- All other strategies: None

Analysis:
- Buy signals: 1/16
- Sell signals: 1/16
- Original buy signals: 1/3
- New sell signals: 1/13
- Weighted buy score: (1×3) + 0 = 3
- Weighted sell score: (0×3) + 1 = 1

Result: NO CLEAR SIGNAL (insufficient consensus)
```

### Example 4: Strong Momentum Signal

```
Signals:
- All technical signals: None
- Price momentum: +2.5%
- Volume spike: True
- RSI momentum: +10

Analysis:
- No technical signals
- Strong buy momentum (+2.5% > 1.5% + volume spike + RSI momentum > 8)

Result: STRONG BUY (momentum-based)
```

## Weighted Scoring System

### Conservative Strategies (3x Weight)
- **MACD + Trend**: 3 points per BUY signal
- **Bollinger + RSI**: 3 points per BUY signal
- **Stochastic + Williams**: 3 points per BUY signal

### Aggressive Strategies (1x Weight)
- **Fibonacci + RSI**: 1 point per BUY signal
- **Parabolic + ADX**: 1 point per BUY signal
- **Keltner + CCI**: 1 point per BUY signal
- **Pivot + RSI**: 1 point per BUY signal
- **MFI + Volume**: 1 point per BUY signal
- **ATR + MA**: 1 point per BUY signal
- **RVI + Stoch**: 1 point per BUY signal
- **CCI + BB**: 1 point per BUY signal
- **OBV + Price**: 1 point per BUY signal
- **CMF + MACD**: 1 point per BUY signal
- **ROC + MA**: 1 point per BUY signal

### Signal Thresholds
- **Minimum signals**: 5 out of 16 (30% consensus)
- **Minimum weighted score**: 8 points
- **Conservative combination**: 2 original + 2 new signals
- **Strong momentum**: Price change > 1.5% + volume spike + RSI momentum > 8

## Risk Management

Each strategy includes built-in risk management:

1. **Position Sizing**: Automatic calculation based on account balance
2. **Trailing Stops**: Dynamic stop-loss adjustment
3. **Leverage Management**: Auto-adjustment for small accounts
4. **Signal Confirmation**: Multiple indicators required
5. **Volume Validation**: Volume confirmation for momentum signals
6. **Weighted Decisions**: Conservative strategies have higher influence

## Performance Monitoring

The bot tracks:
- Signal accuracy per strategy
- Win/loss ratios per strategy category
- Average profit per trade
- Maximum drawdown
- Sharpe ratio
- Strategy correlation analysis
- Weighted score performance
- Conservative vs aggressive strategy performance 