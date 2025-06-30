#!/bin/bash
echo "🐳 Starting Docker Trading Bot..."
export DOCKER_HOST=unix:///var/run/docker.sock

# Stop any existing containers
docker stop crypto-trading-bot 2>/dev/null || true
docker rm crypto-trading-bot 2>/dev/null || true

# Build fresh image
docker build -t crypto-trading-bot .

# Start with manual Docker run command
docker run -d \
  --name crypto-trading-bot \
  --restart unless-stopped \
  -p 8501:8501 \
  -p 8080:8080 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd):/app \
  crypto-trading-bot

echo "✅ Docker container started!"
echo "📱 Dashboard: http://localhost:8501"
echo "⚡ API: http://localhost:8080"
