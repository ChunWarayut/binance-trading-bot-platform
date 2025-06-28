# 🪙 ระบบวิเคราะห์เหรียญ (Coin Analysis System)

## 📋 ภาพรวม

ระบบวิเคราะห์เหรียญถูกออกแบบมาเพื่อคำนวณและแนะนำ:
- **ขนาด Order** (Order Size): ใหญ่, ปานกลาง, เล็ก
- **Leverage**: สูง, ปานกลาง, ต่ำ
- **การจัดการความเสี่ยง**: จำนวน position สูงสุด, ระยะห่างระหว่าง position

## 🔍 เกณฑ์การวิเคราะห์

### 1. การวิเคราะห์ความผันผวน (Volatility Analysis)
- **ความผันผวนต่ำ** (< 2%): เหมาะสำหรับ order size ใหญ่ และ leverage สูง
- **ความผันผวนปานกลาง** (2-5%): เหมาะสำหรับ order size ปานกลาง และ leverage ปานกลาง
- **ความผันผวนสูง** (5-10%): เหมาะสำหรับ order size เล็ก และ leverage ต่ำ
- **ความผันผวนสูงมาก** (> 10%): ควรระมัดระวังเป็นพิเศษ

### 2. การวิเคราะห์ปริมาณการซื้อขาย (Volume Analysis)
- **ปริมาณสูง** (> 1M): เหมาะสำหรับ order size ใหญ่
- **ปริมาณปานกลาง** (500K-1M): เหมาะสำหรับ order size ปานกลาง
- **ปริมาณต่ำ** (< 500K): เหมาะสำหรับ order size เล็ก

### 3. การวิเคราะห์สภาพคล่อง (Liquidity Analysis)
- **สภาพคล่องดี** (> 70): เหมาะสำหรับ order size ใหญ่
- **สภาพคล่องปานกลาง** (30-70): เหมาะสำหรับ order size ปานกลาง
- **สภาพคล่องต่ำ** (< 30): เหมาะสำหรับ order size เล็ก

## 📊 หมวดหมู่การแนะนำ

### 🎯 ขนาด Order (Order Size Categories)

#### 🔥 LARGE (ใหญ่)
- **Position Size Multiplier**: 1.0 (100% ของ available balance)
- **เหมาะสำหรับ**: เหรียญที่มีความผันผวนต่ำ, ปริมาณการซื้อขายสูง, สภาพคล่องดี
- **ตัวอย่าง**: BTC, ETH, BNB

#### ⚖️ MEDIUM (ปานกลาง)
- **Position Size Multiplier**: 0.6 (60% ของ available balance)
- **เหมาะสำหรับ**: เหรียญที่มีความสมดุลระหว่างความเสี่ยงและโอกาส
- **ตัวอย่าง**: SOL, XRP, ADA

#### 🔴 SMALL (เล็ก)
- **Position Size Multiplier**: 0.3 (30% ของ available balance)
- **เหมาะสำหรับ**: เหรียญที่มีความผันผวนสูง, ปริมาณการซื้อขายต่ำ, สภาพคล่องต่ำ
- **ตัวอย่าง**: DOGE, NEAR, ICP

### 🚀 Leverage Categories

#### 🚀 HIGH (สูง)
- **Recommended Leverage**: 10-50x
- **เหมาะสำหรับ**: เหรียญที่มีความผันผวนต่ำ, โมเมนตัมดี, ปริมาณการซื้อขายเสถียร

#### ⚖️ MEDIUM (ปานกลาง)
- **Recommended Leverage**: 5-20x
- **เหมาะสำหรับ**: เหรียญที่มีความสมดุลระหว่างผลตอบแทนและความเสี่ยง

#### 🛡️ LOW (ต่ำ)
- **Recommended Leverage**: 1-10x
- **เหมาะสำหรับ**: เหรียญที่มีความผันผวนสูง, ควรระมัดระวัง

## 🔧 การใช้งาน

### 1. การเรียกใช้ในระบบเทรด

```python
# วิเคราะห์เหรียญทั้งหมด
analyses = await bot.analyze_coins()

# ดึงคำแนะนำสำหรับเหรียญเฉพาะ
recommendations = await bot.get_coin_recommendations("BTCUSDT")
```

### 2. API Endpoints

#### ดึงผลการวิเคราะห์ทั้งหมด
```bash
GET /api/coin-analysis
```

#### ดึงผลการวิเคราะห์เหรียญเฉพาะ
```bash
GET /api/coin-analysis/BTCUSDT
```

#### ดึงรายงานสรุป
```bash
GET /api/coin-analysis/summary
```

#### ดึงคำแนะนำเฉพาะ
```bash
GET /api/coin-analysis/recommendations
```

## 📈 ตัวอย่างผลลัพธ์

### ผลการวิเคราะห์เหรียญ
```json
{
  "BTCUSDT": {
    "symbol": "BTCUSDT",
    "current_price": 45000.0,
    "order_size_category": "LARGE",
    "leverage_category": "HIGH",
    "position_size_multiplier": 1.0,
    "recommended_leverage": 20,
    "notes": [
      "✅ เหมาะสำหรับ order size ใหญ่ - ความผันผวนต่ำ, สภาพคล่องดี",
      "🚀 เหมาะสำหรับ leverage สูง - ความผันผวนต่ำ, โมเมนตัมดี"
    ],
    "metrics": {
      "volatility": 1.8,
      "liquidity_score": 85.5,
      "avg_volume": 1500000
    }
  }
}
```

### รายงานสรุป
```
📊 รายงานการวิเคราะห์เหรียญ

🎯 ขนาด Order:
   🔥 ใหญ่ (3): BTCUSDT, ETHUSDT, BNBUSDT
   ⚖️ ปานกลาง (8): SOLUSDT, XRPUSDT, ADAUSDT, DOTUSDT, LTCUSDT, LINKUSDT, BCHUSDT, AVAXUSDT
   🔴 เล็ก (3): DOGEUSDT, NEARUSDT, ICPUSDT

🚀 Leverage:
   🚀 สูง (4): BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT
   ⚖️ ปานกลาง (7): XRPUSDT, ADAUSDT, DOTUSDT, LTCUSDT, LINKUSDT, BCHUSDT, AVAXUSDT
   🛡️ ต่ำ (3): DOGEUSDT, NEARUSDT, ICPUSDT

💡 คำแนะนำ:
   • ใช้ order size ใหญ่กับ: BTCUSDT, ETHUSDT, BNBUSDT
   • ใช้ leverage สูงกับ: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT
   • ระมัดระวังกับ: DOGEUSDT, NEARUSDT, ICPUSDT
```

## ⚙️ การตั้งค่า

### การปรับแต่งเกณฑ์การวิเคราะห์
สามารถปรับแต่งเกณฑ์ต่างๆ ในไฟล์ `coin_analysis.py`:

```python
# ปรับเกณฑ์ความผันผวน
VOLATILITY_THRESHOLDS = {
    'LOW': 2.0,
    'MEDIUM': 5.0,
    'HIGH': 10.0
}

# ปรับเกณฑ์ปริมาณการซื้อขาย
VOLUME_THRESHOLDS = {
    'HIGH': 1000000,
    'MEDIUM': 500000,
    'LOW': 100000
}

# ปรับเกณฑ์สภาพคล่อง
LIQUIDITY_THRESHOLDS = {
    'HIGH': 70,
    'MEDIUM': 30,
    'LOW': 0
}
```

### การปรับแต่ง Leverage
```python
LEVERAGE_RECOMMENDATIONS = {
    "HIGH": {"min": 10, "max": 50, "recommended": 20},
    "MEDIUM": {"min": 5, "max": 20, "recommended": 10},
    "LOW": {"min": 1, "max": 10, "recommended": 5}
}
```

## 🔄 การอัปเดต

ระบบจะวิเคราะห์เหรียญใหม่ทุกชั่วโมงโดยอัตโนมัติ และสามารถเรียกใช้การวิเคราะห์ใหม่ได้ทันทีผ่าน API

## 📝 หมายเหตุสำคัญ

1. **การวิเคราะห์นี้เป็นเพียงคำแนะนำ** ไม่ใช่การรับประกันผลกำไร
2. **ควรพิจารณาปัจจัยอื่นๆ** เช่น ข่าวสาร, เหตุการณ์สำคัญ, การเปลี่ยนแปลงของตลาด
3. **ควรปรับการตั้งค่า** ตามความเสี่ยงที่ยอมรับได้และขนาดบัญชี
4. **ควรทดสอบ** ในบัญชีทดลองก่อนใช้งานจริง

## 🚨 คำเตือน

- การเทรดมีความเสี่ยงสูง
- อย่าเทรดด้วยเงินที่สูญเสียไม่ได้
- ควรศึกษาหาความรู้เพิ่มเติมก่อนเริ่มเทรด
- ระบบนี้เป็นเพียงเครื่องมือช่วยในการตัดสินใจ ไม่ใช่การรับประกันผลกำไร 