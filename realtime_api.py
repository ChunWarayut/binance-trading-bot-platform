#!/usr/bin/env python3
"""
Real-time API with WebSocket support for live trading data
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import os
import time
import subprocess
from typing import List, Dict
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Crypto Trading Bot Real-time API", version="2.0")

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            
            # Remove disconnected clients
            for conn in disconnected:
                self.disconnect(conn)

manager = ConnectionManager()

def read_json(filename: str) -> dict:
    """Read JSON file safely"""
    try:
        filepath = os.path.join(BASE_PATH, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error reading {filename}: {e}")
        return {}

def get_log_tail(lines: int = 50) -> List[str]:
    """Get last N lines from trading bot log"""
    try:
        log_path = os.path.join(BASE_PATH, "logs", "trading_bot.log")
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                return f.readlines()[-lines:]
        return []
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        return []

def get_system_stats() -> dict:
    """Get system performance statistics"""
    try:
        # CPU and Memory info
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        python_processes = [line for line in result.stdout.split('\n') if 'python' in line and 'main.py' in line]
        
        return {
            'timestamp': datetime.now().isoformat(),
            'python_processes': len(python_processes),
            'uptime': time.time(),
            'log_size': os.path.getsize(os.path.join(BASE_PATH, "logs", "trading_bot.log")) if os.path.exists(os.path.join(BASE_PATH, "logs", "trading_bot.log")) else 0
        }
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {'error': str(e)}

async def collect_real_time_data() -> dict:
    """Collect all real-time data for broadcasting"""
    return {
        'type': 'update',
        'timestamp': datetime.now().isoformat(),
        'bot_status': read_json("bot_status.json"),
        'active_trades': read_json("active_trades.json"),
        'trade_history': read_json("trade_history.json"),
        'system_stats': get_system_stats(),
        'recent_logs': get_log_tail(10)
    }

# Background task for real-time updates
async def broadcast_updates():
    """Background task to broadcast real-time updates"""
    while True:
        try:
            data = await collect_real_time_data()
            await manager.broadcast(data)
            await asyncio.sleep(2)  # Update every 2 seconds
        except Exception as e:
            logger.error(f"Error in broadcast_updates: {e}")
            await asyncio.sleep(5)

# Start background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_updates())

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial data
        initial_data = await collect_real_time_data()
        await websocket.send_json(initial_data)
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# REST API Endpoints
@app.get("/api/status")
def get_full_status():
    """Get complete bot status"""
    return JSONResponse(content={
        'bot_status': read_json("bot_status.json"),
        'active_trades': read_json("active_trades.json"),
        'system_stats': get_system_stats(),
        'timestamp': datetime.now().isoformat()
    })

@app.get("/api/bot_status")
def get_bot_status():
    """Get bot status only"""
    return JSONResponse(content=read_json("bot_status.json"))

@app.get("/api/active_trades")
def get_active_trades():
    """Get active trades"""
    return JSONResponse(content=read_json("active_trades.json"))

@app.get("/api/trade_history")
def get_trade_history():
    """Get trade history"""
    return JSONResponse(content=read_json("trade_history.json"))

@app.get("/api/logs/{lines}")
def get_logs(lines: int = 50):
    """Get recent log lines"""
    return JSONResponse(content={
        'logs': get_log_tail(lines),
        'timestamp': datetime.now().isoformat()
    })

@app.get("/api/config")
def get_config():
    """Get bot configuration"""
    return JSONResponse(content=read_json("bot_config.json"))

@app.post("/api/config")
async def update_config(config: dict):
    """Update bot configuration"""
    try:
        with open(os.path.join(BASE_PATH, "bot_config.json"), 'w') as f:
            json.dump(config, f, indent=2)
        
        # Broadcast config update
        await manager.broadcast({
            'type': 'config_update',
            'timestamp': datetime.now().isoformat(),
            'message': 'Configuration updated successfully'
        })
        
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Bot control endpoints
def run_command(cmd: List[str]) -> dict:
    """Run system command safely"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr, 
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}

@app.post("/api/bot/start")
async def start_bot():
    """Start the trading bot"""
    result = run_command(["python3", "main.py"])
    await manager.broadcast({
        'type': 'bot_action',
        'action': 'start',
        'timestamp': datetime.now().isoformat(),
        'result': result
    })
    return {"status": "starting" if result.get("success") else "error", "details": result}

@app.post("/api/bot/stop")
async def stop_bot():
    """Stop the trading bot"""
    result = run_command(["pkill", "-f", "python3 main.py"])
    await manager.broadcast({
        'type': 'bot_action',
        'action': 'stop',
        'timestamp': datetime.now().isoformat(),
        'result': result
    })
    return {"status": "stopping", "details": result}

@app.post("/api/bot/restart")
async def restart_bot():
    """Restart the trading bot"""
    # Stop first
    stop_result = run_command(["pkill", "-f", "python3 main.py"])
    await asyncio.sleep(2)
    # Start again
    start_result = run_command(["python3", "main.py"])
    
    await manager.broadcast({
        'type': 'bot_action',
        'action': 'restart',
        'timestamp': datetime.now().isoformat(),
        'result': {'stop': stop_result, 'start': start_result}
    })
    return {"status": "restarting", "details": {"stop": stop_result, "start": start_result}}

# Health check
@app.get("/health")
def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "connections": len(manager.active_connections)
    }

# HTML Dashboard (simple)
@app.get("/dashboard")
def dashboard():
    """Simple HTML dashboard"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Crypto Trading Bot Real-time Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: #2d2d2d; border-radius: 8px; padding: 20px; margin: 10px 0; border-left: 4px solid #00ff88; }
        .metric { display: inline-block; margin: 10px 20px; }
        .status { font-size: 1.2em; font-weight: bold; }
        .running { color: #00ff88; }
        .stopped { color: #ff4444; }
        .logs { background: #000; padding: 15px; border-radius: 5px; max-height: 300px; overflow-y: scroll; font-family: monospace; font-size: 12px; }
        button { background: #00ff88; border: none; color: black; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #00cc66; }
        .error { color: #ff4444; }
        .success { color: #00ff88; }
        h1, h2 { color: #00ff88; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Crypto Trading Bot Dashboard</h1>
        
        <div class="card">
            <h2>📊 Bot Status</h2>
            <div id="status"></div>
        </div>
        
        <div class="card">
            <h2>🎮 Controls</h2>
            <button onclick="controlBot('start')">▶️ Start</button>
            <button onclick="controlBot('stop')">⏹️ Stop</button>
            <button onclick="controlBot('restart')">🔄 Restart</button>
        </div>
        
        <div class="card">
            <h2>📈 Active Trades</h2>
            <div id="trades"></div>
        </div>
        
        <div class="card">
            <h2>📋 Recent Logs</h2>
            <div id="logs" class="logs"></div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://localhost:8080/ws');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };
        
        function updateDashboard(data) {
            // Update status
            const status = data.bot_status || {};
            const running = status.running ? 'running' : 'stopped';
            document.getElementById('status').innerHTML = `
                <div class="metric">Status: <span class="status ${running}">${running.toUpperCase()}</span></div>
                <div class="metric">Active Trades: ${status.active_trades_count || 0}</div>
                <div class="metric">Total P&L: $${(status.total_pnl || 0).toFixed(2)}</div>
                <div class="metric">Last Update: ${status.last_update || 'N/A'}</div>
            `;
            
            // Update trades
            const trades = data.active_trades || [];
            if (trades.length > 0) {
                let tradesHtml = '<table border="1" style="width:100%; border-collapse: collapse;">';
                tradesHtml += '<tr><th>Symbol</th><th>Side</th><th>Entry</th><th>Quantity</th><th>Trailing Stop</th></tr>';
                trades.forEach(trade => {
                    tradesHtml += `<tr>
                        <td>${trade.Symbol || 'N/A'}</td>
                        <td>${trade.Side || 'N/A'}</td>
                        <td>$${trade.Entry || 0}</td>
                        <td>${trade.Quantity || 0}</td>
                        <td>$${trade.TrailingStop || 'N/A'}</td>
                    </tr>`;
                });
                tradesHtml += '</table>';
                document.getElementById('trades').innerHTML = tradesHtml;
            } else {
                document.getElementById('trades').innerHTML = '<p>No active trades</p>';
            }
            
            // Update logs
            const logs = data.recent_logs || [];
            document.getElementById('logs').innerHTML = logs.slice(-10).join('');
        }
        
        async function controlBot(action) {
            try {
                const response = await fetch(`/api/bot/${action}`, { method: 'POST' });
                const result = await response.json();
                alert(`Bot ${action}: ${result.status}`);
            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        }
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = function(event) {
            console.log('WebSocket connection closed');
            setTimeout(() => location.reload(), 5000); // Reconnect after 5 seconds
        };
    </script>
</body>
</html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 