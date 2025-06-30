# 🧪 คู่มือทดสอบ Enhanced Backtest Engine

## 📋 การแก้ไขที่ทำแล้ว

### ✅ ปัญหาที่แก้ไข:
1. **Signal Functions ไม่ตรงกัน** - เพิ่ม error handling สำหรับ functions ใหม่
2. **Momentum Signal Format** - แปลง tuple เป็น BUY/SELL/None
3. **Return Type Issues** - คืนค่า "NONE" แทน None
4. **Trade Execution Logic** - จัดการ signal types ใหม่

### 🔧 ไฟล์ที่แก้ไข:
- `backtest.py` - หลัก backtest engine
- `test_backtest_fix.py` - สคริปต์ทดสอบ async
- `simple_backtest_test.py` - สคริปต์ทดสอบแบบละเอียด
- `manual_test_backtest.py` - สคริปต์ทดสอบแบบ manual

---

## 🚀 วิธีทดสอบ

### 1. ทดสอบพื้นฐาน (แนะนำเริ่มที่นี่)
```bash
python manual_test_backtest.py
```
**ผลลัพธ์ที่ควรได้:**
- ✅ Import modules สำเร็จ
- ✅ สร้าง BacktestEngine สำเร็จ  
- ✅ Signal functions ทำงานได้
- 🎯 แสดง active signals และ final signal

### 2. ทดสอบ Async Functions
```bash
python simple_backtest_test.py
```
**ทดสอบ:**
- Import และ creation
- Signal functions กับข้อมูลจำลอง
- Mini backtest กับข้อมูลจริง

### 3. ทดสอบ Full Backtest (ใช้เวลานาน)
```bash
python backtest.py
```
**การตั้งค่า:**
- Period: 2024-01-01 to 2025-06-30
- Symbols: BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, LTC, LINK, BCH, NEAR, ICP
- Initial balance: $1000

### 4. ทดสอบใน Docker
```bash
# เริ่ม containers
docker-compose up -d

# รันทดสอบใน container
docker-compose exec trading-bot python manual_test_backtest.py

# รัน full backtest
docker-compose exec trading-bot python backtest.py
```

---

## 📊 ผลลัพธ์ที่คาดหวัง

### การทดสอบพื้นฐาน:
```
🧪 เริ่มทดสอบ Enhanced Backtest Engine
==================================================
📦 ทดสอบการ import modules...
✅ Import modules สำเร็จ

🏗️ ทดสอบการสร้าง BacktestEngine...
✅ สร้าง BacktestEngine สำเร็จ
📅 Period: 2024-01-01 to 2024-01-03
💰 Initial balance: $1,000.00

📊 ทดสอบ Signal Functions...
📈 สร้างข้อมูลทดสอบ 100 candles
💹 Price range: $40,000 - $50,000
✅ คำนวณ indicators สำเร็จ
✅ Signal functions ทำงานได้
📊 Total signals: 15
🟢 BUY signals: 2
🔴 SELL signals: 1
⚪ None signals: 12
🎯 Active signals:
  • macd_trend: BUY
  • volume_profile: SELL
🎯 Final signal: NONE (no_signal)

🎉 การทดสอบพื้นฐานสำเร็จทั้งหมด!
✅ Backtest engine พร้อมใช้งาน
```

### Full Backtest Results:
```json
{
  "initial_balance": 1000.0,
  "final_balance": 1250.45,
  "total_return_pct": 25.05,
  "total_trades": 45,
  "winning_trades": 28,
  "losing_trades": 17,
  "win_rate_pct": 62.22,
  "profit_factor": 1.85,
  "max_drawdown_pct": 12.5,
  "strategy_performance": {
    "regular_consensus": {
      "signals": 32,
      "wins": 20,
      "win_rate": 62.5
    },
    "momentum_based": {
      "signals": 13,
      "wins": 8,
      "win_rate": 61.5
    }
  }
}
```

---

## 🔍 การแก้ไขปัญหา (Troubleshooting)

### ❌ Import Error
```bash
# ตรวจสอบ dependencies
pip install -r requirements.txt

# ตรวจสอบ Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### ❌ API Connection Error
```bash
# ตรวจสอบ config
cat bot_config.json | grep -A 5 "binance"

# ตรวจสอบ network
ping api.binance.com
```

### ❌ Signal Function Error
- ตรวจสอบ DataFrame columns
- ตรวจสอบ indicator calculations
- ดู error logs ใน console

### ❌ Memory Error (สำหรับ full backtest)
```bash
# ลด data period
# แก้ไขใน backtest.py line 635:
# start_date = '2024-06-01'  # แทน '2024-01-01'

# หรือลด symbols
# แก้ไข symbols list ให้เหลือแค่ 3-5 symbols
```

---

## 📈 การปรับแต่งเพิ่มเติม

### 1. ปรับ Strategy Weights
แก้ไขใน `strategy_config.json`:
```json
{
  "strategy_weights": {
    "MACD Trend": 0.20,
    "Volume Profile": 0.15,
    "Market Structure": 0.12
  }
}
```

### 2. ปรับ Backtest Parameters
แก้ไขใน `backtest.py`:
```python
# เปลี่ยน initial balance
initial_balance = 5000

# เปลี่ยน position size
position_size = (self.current_balance * 0.05) / entry_price  # 5% แทน 10%

# เปลี่ยน exit condition
candles_held >= 5  # 5 candles แทน 10
```

### 3. เพิ่ม Risk Management
```python
# Stop loss
if pnl < -50:  # หยุดขาดทุนที่ $50
    self.close_trade(current_trade, current_price, current_timestamp)

# Take profit
if pnl > 100:  # ปิดกำไรที่ $100
    self.close_trade(current_trade, current_price, current_timestamp)
```

---

## 🎯 ขั้นตอนต่อไป

1. **ทดสอบเสร็จแล้ว** → ปรับแต่ง parameters
2. **ผลลัพธ์ดี** → รัน paper trading
3. **Paper trading ดี** → รัน bot จริงด้วยเงินน้อย
4. **Bot ทำงานดี** → เพิ่มเงินลงทุนค่อยๆ

---

## 📞 การติดต่อและรายงานปัญหา

หากพบปัญหาในการทดสอบ:
1. เก็บ error message และ stack trace
2. ตรวจสอบ log files ใน `logs/` directory
3. ลองรัน `manual_test_backtest.py` ก่อนเสมอ
4. ตรวจสอบ network connection และ API keys

**Happy Testing! 🚀** 