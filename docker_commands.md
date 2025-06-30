# 🐳 Docker Commands Reference

## 🚀 Quick Start Commands

### 1. แก้ไข Error
```bash
# ให้ permission ไฟล์ script
chmod +x docker_fix_errors.sh

# รันการแก้ไข error
./docker_fix_errors.sh
```

### 2. ทดสอบระบบ
```bash
# ให้ permission ไฟล์ script
chmod +x docker_test.sh

# รันการทดสอบ
./docker_test.sh
```

## 🔧 Manual Docker Commands

### แก้ไข Error ทีละขั้นตอน

#### 1. ตรวจสอบ Error
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
python error_checker.py"
```

#### 2. แก้ไข Error อัตโนมัติ
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
python fix_errors.py"
```

#### 3. Debug Trading Bot
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
python debug_bot.py"
```

#### 4. Quick Start
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
python quick_start.py"
```

### ทดสอบระบบ

#### 1. ทดสอบ Win Rate (5-10 นาที)
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
timeout 600 python quick_winrate_test.py"
```

#### 2. ปรับปรุง Win Rate
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
python win_rate_optimizer.py"
```

#### 3. ทดสอบ Backtest พื้นฐาน
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
python manual_test_backtest.py"
```

#### 4. Full Backtest (10-30 นาที)
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
timeout 1800 python backtest.py"
```

#### 5. วิเคราะห์ผลลัพธ์
```bash
docker run --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
python performance_analyzer.py"
```

## 🏗️ Docker Compose Commands

### Build และ Start Services
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Start เฉพาะ trading bot
docker-compose up -d trading-bot

# Check status
docker-compose ps

# View logs
docker-compose logs -f trading-bot
```

### Execute Commands in Running Container
```bash
# เข้า shell ของ container
docker-compose exec trading-bot bash

# รันคำสั่งโดยตรง
docker-compose exec trading-bot python error_checker.py
docker-compose exec trading-bot python quick_winrate_test.py
docker-compose exec trading-bot python backtest.py
```

### Stop และ Clean Up
```bash
# Stop services
docker-compose down

# Remove containers และ networks
docker-compose down --remove-orphans

# Remove images
docker-compose down --rmi all
```

## 📊 Monitoring Commands

### ดู Logs
```bash
# ดู logs ทั้งหมด
docker-compose logs

# ดู logs แบบ real-time
docker-compose logs -f

# ดู logs เฉพาะ service
docker-compose logs -f trading-bot
docker-compose logs -f web-ui
docker-compose logs -f status-api
```

### ตรวจสอบ Resources
```bash
# ดู container stats
docker stats

# ดู disk usage
docker system df

# ดู images
docker images

# ดู containers
docker ps -a
```

## 🚨 Emergency Commands

### หาก Container ไม่ทำงาน
```bash
# Restart service
docker-compose restart trading-bot

# Rebuild และ restart
docker-compose up -d --build trading-bot

# Force recreate
docker-compose up -d --force-recreate trading-bot
```

### หาก Docker มีปัญหา
```bash
# Clean up everything
docker system prune -a

# Remove all stopped containers
docker container prune

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune
```

### หาก Memory เต็ม
```bash
# ดู memory usage
docker stats --no-stream

# Limit memory สำหรับ container
docker run --memory="512m" --rm -v $(pwd):/workspace -w /workspace python:3.11-slim bash -c "
pip install -r requirements.txt > /dev/null 2>&1 && 
python quick_winrate_test.py"
```

## 🎯 Recommended Workflow

### 1. เริ่มต้น (ครั้งแรก)
```bash
chmod +x docker_fix_errors.sh docker_test.sh
./docker_fix_errors.sh
```

### 2. ทดสอบ
```bash
./docker_test.sh
```

### 3. Deploy (หากทดสอบผ่าน)
```bash
docker-compose up -d
```

### 4. Monitor
```bash
docker-compose logs -f trading-bot
```

### 5. Update และ Restart
```bash
docker-compose down
docker-compose up -d --build
```

## 📝 Notes

- ใช้ `--rm` เพื่อลบ container หลังใช้งาน
- ใช้ `timeout` เพื่อจำกัดเวลาการทำงาน
- ใช้ `-v $(pwd):/workspace` เพื่อ mount current directory
- ใช้ `> /dev/null 2>&1` เพื่อซ่อน pip install output
- ใช้ `python:3.11-slim` เพื่อประหยัด space และเวลา download 