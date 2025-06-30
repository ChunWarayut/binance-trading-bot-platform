#!/bin/bash

echo "🐳 DOCKER TESTING SCRIPT"
echo "========================"

# ตัวแปร
PYTHON_IMAGE="python:3.11-slim"
WORKSPACE="/workspace"

echo "📋 การทดสอบที่จะรัน:"
echo "1. quick_winrate_test.py - ทดสอบ Win Rate"
echo "2. win_rate_optimizer.py - ปรับปรุง Win Rate"
echo "3. manual_test_backtest.py - ทดสอบ Backtest"
echo "4. performance_analyzer.py - วิเคราะห์ผลลัพธ์"
echo ""

# Function สำหรับรันคำสั่งใน Docker
run_test_in_docker() {
    local script_name=$1
    local description=$2
    local timeout=${3:-300}  # default 5 minutes
    
    echo "🚀 รัน: $script_name - $description"
    echo "⏱️ Timeout: ${timeout} seconds"
    echo "================================"
    
    docker run -it --rm \
        -v "$(pwd):$WORKSPACE" \
        -w $WORKSPACE \
        $PYTHON_IMAGE \
        timeout $timeout bash -c "
            echo '📦 Installing requirements...'
            pip install --no-cache-dir -r requirements.txt > /dev/null 2>&1
            echo '✅ Requirements installed'
            echo ''
            echo '🔧 Running $script_name...'
            python $script_name
        "
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "✅ สำเร็จ: $script_name"
    elif [ $exit_code -eq 124 ]; then
        echo "⏰ Timeout: $script_name (เกิน ${timeout} วินาที)"
    else
        echo "❌ ล้มเหลว: $script_name (exit code: $exit_code)"
    fi
    echo "================================"
    echo ""
}

# Function สำหรับรัน backtest แบบเร็ว
run_quick_backtest() {
    echo "🚀 รัน: Quick Backtest (7 วัน)"
    echo "================================"
    
    docker run -it --rm \
        -v "$(pwd):$WORKSPACE" \
        -w $WORKSPACE \
        $PYTHON_IMAGE \
        timeout 600 bash -c "
            echo '📦 Installing requirements...'
            pip install --no-cache-dir -r requirements.txt > /dev/null 2>&1
            echo '✅ Requirements installed'
            echo ''
            echo '🔧 Running Quick Backtest...'
            python -c \"
import sys
sys.path.append('.')
from backtest import run_backtest
from datetime import datetime, timedelta
import pandas as pd

# Quick backtest - 7 days only
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f'📅 Testing period: {start_date.strftime(\"%Y-%m-%d\")} to {end_date.strftime(\"%Y-%m-%d\")}')
print('💰 Initial balance: \$1000')
print('🎯 Target: Win Rate > 55%')
print('')

try:
    result = run_backtest(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        initial_balance=1000,
        symbols=['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
        interval='1h'
    )
    
    if result:
        print('✅ Quick Backtest completed successfully')
    else:
        print('❌ Quick Backtest failed')
        
except Exception as e:
    print(f'❌ Error in Quick Backtest: {e}')
\"
        "
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "✅ สำเร็จ: Quick Backtest"
    elif [ $exit_code -eq 124 ]; then
        echo "⏰ Timeout: Quick Backtest (เกิน 10 นาที)"
    else
        echo "❌ ล้มเหลว: Quick Backtest (exit code: $exit_code)"
    fi
    echo "================================"
    echo ""
}

# เริ่มการทดสอบ
echo "🎯 เริ่มต้นการทดสอบ..."
echo ""

# 1. ทดสอบ Win Rate (ใช้เวลา 5-10 นาที)
run_test_in_docker "quick_winrate_test.py" "ทดสอบ Win Rate" 600

# 2. ปรับปรุง Win Rate (หาก Win Rate < 55%)
echo "🤔 ต้องการปรับปรุง Win Rate หรือไม่? (y/n)"
echo "หาก Win Rate < 55% ควรรัน win_rate_optimizer.py"
run_test_in_docker "win_rate_optimizer.py" "ปรับปรุง Win Rate" 300

# 3. ทดสอบ Backtest พื้นฐาน
run_test_in_docker "manual_test_backtest.py" "ทดสอบ Backtest พื้นฐาน" 300

# 4. Quick Backtest
run_quick_backtest

# 5. วิเคราะห์ผลลัพธ์
run_test_in_docker "performance_analyzer.py" "วิเคราะห์ผลลัพธ์" 180

echo "🎉 เสร็จสิ้นการทดสอบทั้งหมด!"
echo ""
echo "📊 สรุปผลลัพธ์:"
echo "- หาก Win Rate > 55% = ✅ พร้อมใช้งาน"
echo "- หาก Win Rate < 55% = ⚠️ ต้องปรับปรุงเพิ่มเติม"
echo ""
echo "🚀 ขั้นตอนต่อไป:"
echo "1. หากผลลัพธ์ดี ให้รัน full backtest:"
echo "   docker run --rm -v \$(pwd):/workspace -w /workspace python:3.11-slim bash -c 'pip install -r requirements.txt && python backtest.py'"
echo ""
echo "2. หากต้องการ deploy:"
echo "   docker-compose up -d"
echo ""
echo "3. หากต้องการ monitor:"
echo "   docker-compose logs -f trading-bot" 