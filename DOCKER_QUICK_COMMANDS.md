# 🐳 Docker Quick Commands - Copy & Paste

## 🚀 แก้ไข Error (ทีละคำสั่ง)

### 1. ตรวจสอบ Error
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python error_checker.py"
```

### 2. แก้ไข Error อัตโนมัติ
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python fix_errors.py"
```

### 3. Debug Trading Bot
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python debug_bot.py"
```

### 4. Quick Start Test
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python quick_start.py"
```

---

## 🧪 ทดสอบระบบ (ทีละคำสั่ง)

### 1. ทดสอบ Win Rate (5-10 นาที)
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && timeout 600 python quick_winrate_test.py"
```

### 2. ปรับปรุง Win Rate
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python win_rate_optimizer.py"
```

### 3. ทดสอบ Backtest พื้นฐาน
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python manual_test_backtest.py"
```

### 4. Full Backtest (10-30 นาที)
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && timeout 1800 python backtest.py"
```

### 5. วิเคราะห์ผลลัพธ์
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python performance_analyzer.py"
```

---

## ⚡ คำสั่งรวม (All-in-One)

### แก้ไข Error ทั้งหมด
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
echo '🔍 Checking errors...' && python error_checker.py && 
echo '🔧 Fixing errors...' && python fix_errors.py && 
echo '🤖 Debugging bot...' && python debug_bot.py && 
echo '🚀 Quick start test...' && python quick_start.py && 
echo '✅ All error fixing completed!'
"
```

### ทดสอบระบบทั้งหมด
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
echo '🧪 Testing Win Rate...' && timeout 600 python quick_winrate_test.py && 
echo '📊 Testing Backtest...' && python manual_test_backtest.py && 
echo '📈 Analyzing Performance...' && python performance_analyzer.py && 
echo '✅ All tests completed!'
"
```

---

## 🏗️ Docker Compose Commands

### Start Services
```bash
docker-compose build && docker-compose up -d
```

### Check Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs -f trading-bot
```

### Execute in Running Container
```bash
docker-compose exec trading-bot python error_checker.py
```

### Stop Services
```bash
docker-compose down
```

---

## 🚨 Emergency Commands

### หาก Docker มีปัญหา
```bash
docker system prune -a -f
```

### หาก Container ไม่ทำงาน
```bash
docker-compose down && docker-compose up -d --build
```

### ทดสอบ Docker ว่าทำงานได้หรือไม่
```bash
docker run --rm python:3.11-slim python -c "print('🐳 Docker is working!')"
```

---

## 📋 Recommended Sequence

### ครั้งแรก (Setup)
```bash
# 1. แก้ไข error
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python fix_errors.py"

# 2. ตรวจสอบระบบ
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python debug_bot.py"

# 3. ทดสอบเบื้องต้น
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python quick_start.py"
```

### การทดสอบ
```bash
# 1. ทดสอบ Win Rate
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && timeout 600 python quick_winrate_test.py"

# 2. หาก Win Rate < 55% ให้ปรับปรุง
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python win_rate_optimizer.py"

# 3. ทดสอบ Backtest
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "pip install -r requirements.txt > /dev/null 2>&1 && python manual_test_backtest.py"
```

### Deploy
```bash
# หากทดสอบผ่านแล้ว
docker-compose up -d
```

---

## 💡 Tips

- ใช้ `Ctrl+C` เพื่อหยุดคำสั่งที่ทำงานอยู่
- ใช้ `timeout` เพื่อจำกัดเวลาการทำงาน
- คำสั่งจะลบ container อัตโนมัติหลังใช้งาน (`--rm`)
- ไฟล์จะถูก sync กับ host machine ผ่าน volume mount
- หาก memory ไม่พอ ให้เพิ่ม `--memory="512m"` ในคำสั่ง docker run

---

## 🎯 Success Indicators

หลังจากรันคำสั่งแล้ว ควรเห็น:
- ✅ All imports successful
- ✅ JSON files valid  
- ✅ Trading bot imports OK
- ✅ Win Rate > 55%
- ✅ Backtest working

หากเห็น ❌ ให้รันคำสั่งแก้ไข error อีกครั้ง 