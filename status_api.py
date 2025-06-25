from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import json
import os
import subprocess

app = FastAPI()

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def read_json(filename):
    try:
        with open(os.path.join(BASE_PATH, filename), 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def run_docker_compose_cmd(cmd):
    result = subprocess.run(
        ["docker-compose"] + cmd,
        cwd=BASE_PATH,
        capture_output=True,
        text=True
    )
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}

@app.get("/api/bot_status")
def get_bot_status():
    return JSONResponse(content=read_json("bot_status.json"))

@app.get("/api/active_trades")
def get_active_trades():
    return JSONResponse(content=read_json("active_trades.json"))

@app.get("/api/trade_history")
def get_trade_history():
    return JSONResponse(content=read_json("trade_history.json"))

@app.post("/api/start_bot")
def start_bot(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_docker_compose_cmd, ["start", "trading-bot"])
    return {"status": "starting"}

@app.post("/api/stop_bot")
def stop_bot(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_docker_compose_cmd, ["stop", "trading-bot"])
    return {"status": "stopping"}

@app.post("/api/restart_bot")
def restart_bot(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_docker_compose_cmd, ["restart", "trading-bot"])
    return {"status": "restarting"} 