#!/bin/bash

echo "🐳 CRYPTO TRADING BOT - DOCKER PRODUCTION STARTUP"
echo "================================================="
echo ""

# Set Docker environment
export DOCKER_HOST=unix:///var/run/docker.sock

# Stop existing processes
echo "🛑 Stopping existing processes..."
pkill -9 -f "python.*main.py" 2>/dev/null || true
pkill -9 -f "streamlit" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true

# Clean up existing containers
echo "🗑️ Cleaning up existing containers..."
docker stop crypto-trading-bot 2>/dev/null || true
docker rm crypto-trading-bot 2>/dev/null || true

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t crypto-trading-bot . --no-cache

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
else
    echo "❌ Docker build failed!"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Start container with all services
echo "🚀 Starting Docker container..."
docker run -d \
  --name crypto-trading-bot \
  --restart unless-stopped \
  -p 8501:8501 \
  -p 8080:8080 \
  -p 5001:5001 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/active_trades.json:/app/active_trades.json \
  -v $(pwd)/bot_status.json:/app/bot_status.json \
  -v $(pwd)/bot_config.json:/app/bot_config.json \
  -v $(pwd)/trade_history.json:/app/trade_history.json \
  -e TZ=Asia/Bangkok \
  crypto-trading-bot

if [ $? -eq 0 ]; then
    echo "✅ Docker container started successfully!"
else
    echo "❌ Docker container failed to start!"
    exit 1
fi

# Wait for services to initialize
echo "⏳ Waiting for services to initialize..."
sleep 15

# Test services
echo "🧪 Testing services..."
if curl -s http://localhost:8080/api/bot_status >/dev/null 2>&1; then
    echo "✅ API service is running on port 8080"
else
    echo "⚠️ API service not responding on port 8080"
fi

if curl -s http://localhost:8501 >/dev/null 2>&1; then
    echo "✅ Streamlit dashboard is running on port 8501"
else
    echo "⚠️ Streamlit dashboard not responding on port 8501"
fi

# Show container status
echo ""
echo "🐳 Container Status:"
docker ps | head -1
docker ps | grep crypto-trading-bot || echo "Container not found"

echo ""
echo "📊 Recent container logs:"
docker logs crypto-trading-bot 2>&1 | tail -10

echo ""
echo "🎉 DOCKER PRODUCTION STARTUP COMPLETE!"
echo "======================================"
echo "📱 Streamlit Dashboard: http://localhost:8501"
echo "⚡ API Endpoints: http://localhost:8080"
echo "🔧 API Documentation: http://localhost:8080/docs"
echo "🐳 Container Name: crypto-trading-bot"
echo ""
echo "📝 Quick Commands:"
echo "   Check status: docker ps | grep crypto-trading-bot"
echo "   View logs: docker logs crypto-trading-bot"
echo "   Stop: docker stop crypto-trading-bot"
echo "   Restart: docker restart crypto-trading-bot"
echo ""
echo "🎯 Production environment is ready!" 