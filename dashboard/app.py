"""
Flipped Factory — Dashboard Server
Full UI for managing the AI content factory.
Port: 8003
"""
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from engines.revenue_tracker import init_db, get_dashboard_stats, log_video, update_daily_log
from engines.niche_selector import NICHES, select_topic, get_hashtags
from engines.trend_engine import refresh_trends
from config import TREND_KEYWORDS, DASHBOARD_PORT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("dashboard")

app = FastAPI(title="Flipped Factory Dashboard")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ─── WebSocket Manager ────────────────────────────────────────────────────────
class WsManager:
    def __init__(self):
        self.connections: list[WebSocket] = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
    
    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)
    
    async def broadcast(self, data: dict):
        dead = []
        for ws in list(self.connections):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

ws_manager = WsManager()

# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Dashboard started")

# ─── HTTP Endpoints ───────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = Path(__file__).parent / "index.html"
    return HTMLResponse(html_path.read_text())

@app.get("/api/stats")
async def get_stats():
    return get_dashboard_stats()

@app.get("/api/niches")
async def get_niches():
    return {"niches": NICHES}

@app.get("/api/topics/{niche}")
async def get_topics(niche: str):
    topics = [select_topic(niche) for _ in range(10)]
    return {"niche": niche, "topics": topics}

@app.get("/api/hashtags/{niche}")
async def get_hashtags_endpoint(niche: str):
    tags = get_hashtags(niche)
    return {"niche": niche, "hashtags": tags}

@app.post("/api/generate")
async def generate_video(payload: dict):
    """Generate a single video."""
    niche = payload.get("niche", "health_fitness")
    topic = payload.get("topic") or select_topic(niche)
    
    from engines.content_creator import generate_script_with_ai, save_script
    from engines.video_builder import create_text_video
    from tools.tts_engine import text_to_speech
    from tools.video_editor import add_audio_track
    
    script = generate_script_with_ai(topic, niche, duration=45)
    save_script(script, f"manual_{niche}")
    
    timestamp = datetime.now().strftime("%H%M%S")
    base = f"data/videos/processed/manual_{niche}_{timestamp}"
    
    video_path = f"{base}.mp4"
    create_text_video(script, video_path)
    
    audio_path = f"{base}_audio.wav"
    text_to_speech(f"{script['hook']} {script['body']} {script['cta']}", audio_path, rate=150)
    
    final_path = f"{base}_final.mp4"
    add_audio_track(video_path, audio_path, final_path, volume=0.8)
    
    video_id = log_video(
        title=script.get("hook", topic)[:60],
        niche=niche,
        agent_type="manual",
        video_path=final_path
    )
    
    await ws_manager.broadcast({"event": "video:created", "data": {
        "niche": niche, "topic": topic, "hook": script.get("hook", ""),
        "path": final_path, "video_id": video_id,
    }})
    
    return {
        "success": True,
        "video_id": video_id,
        "hook": script.get("hook", ""),
        "path": final_path,
    }

@app.post("/api/trends/refresh")
async def refresh_trends_endpoint():
    """Refresh Google Trends."""
    result = refresh_trends(TREND_KEYWORDS)
    return {"success": True, "ranked": result.get("ranked", [])}

@app.get("/api/trends")
async def get_trends():
    from engines.trend_engine import load_trends, rank_niches
    data = load_trends()
    ranked = rank_niches(data) if data else []
    return {"ranked": ranked}

@app.post("/api/pipeline/run")
async def run_pipeline(payload: dict = {}):
    """Run the daily pipeline."""
    count = payload.get("count", 3)
    
    from main import run_daily_pipeline
    
    result = run_daily_pipeline(videos_per_day=count)
    
    await ws_manager.broadcast({"event": "pipeline:done", "data": {
        "videos_created": len(result.get("videos_created", [])),
    }})
    
    return result

# ─── WebSocket ────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        stats = get_dashboard_stats()
        await ws.send_json({"event": "init", "data": stats})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)

# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=DASHBOARD_PORT)
