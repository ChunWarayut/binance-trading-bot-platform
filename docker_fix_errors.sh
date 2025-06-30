#!/bin/bash

echo "🐳 DOCKER ERROR FIXING SCRIPT"
echo "================================"

# ตัวแปร
PYTHON_IMAGE="python:3.11-slim"
WORKSPACE="/workspace"

echo "📋 เครื่องมือที่จะรัน:"
echo "1. error_checker.py - ตรวจสอบ error"
echo "2. fix_errors.py - แก้ไข error อัตโนมัติ"
echo "3. debug_bot.py - debug trading bot"
echo "4. quick_start.py - ทดสอบการทำงาน"
echo ""

# Function สำหรับรันคำสั่งใน Docker
run_in_docker() {
    local script_name=$1
    local description=$2
    
    echo "🚀 รัน: $script_name - $description"
    echo "================================"
    
    docker run -it --rm \
        -v "$(pwd):$WORKSPACE" \
        -w $WORKSPACE \
        $PYTHON_IMAGE \
        bash -c "
            echo '📦 Installing requirements...'
            pip install --no-cache-dir -r requirements.txt > /dev/null 2>&1
            echo '✅ Requirements installed'
            echo ''
            echo '🔧 Running $script_name...'
            python $script_name
        "
    
    echo ""
    echo "✅ เสร็จสิ้น: $script_name"
    echo "================================"
    echo ""
}

# รันเครื่องมือทีละตัว
echo "🎯 เริ่มต้นการแก้ไข error..."
echo ""

# 1. ตรวจสอบ error
run_in_docker "error_checker.py" "ตรวจสอบ error ทั่วไป"

# 2. แก้ไข error อัตโนมัติ
run_in_docker "fix_errors.py" "แก้ไข error อัตโนมัติ"

# 3. Debug trading bot
run_in_docker "debug_bot.py" "debug trading bot"

# 4. ทดสอบการทำงาน
run_in_docker "quick_start.py" "ทดสอบการทำงาน"

echo "🎉 เสร็จสิ้นการแก้ไข error ทั้งหมด!"
echo ""
echo "🚀 ขั้นตอนต่อไป:"
echo "1. หากทุกอย่างเป็น ✅ ให้รัน:"
echo "   ./docker_test.sh"
echo ""
echo "2. หากยังมี ❌ ให้ตรวจสอบ log และแก้ไขเพิ่มเติม"
echo ""
echo "3. รัน backtest ใน Docker:"
echo "   docker run --rm -v \$(pwd):/workspace -w /workspace python:3.11-slim bash -c 'pip install -r requirements.txt && python quick_winrate_test.py'" 