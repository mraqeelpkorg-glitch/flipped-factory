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
from engines.podcast_db import ensure_tables, get_podcast_dashboard_stats, get_queue, get_clips_by_status
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
    ensure_tables()
    logger.info("Dashboard started with podcast tables")

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

# ─── Podcast Clipper Endpoints ────────────────────────────────────────────────
@app.get("/api/podcast/stats")
async def get_podcast_stats():
    """Get podcast clipper dashboard stats."""
    return get_podcast_dashboard_stats()

@app.post("/api/podcast/run")
async def run_podcast_pipeline(payload: dict):
    """
    Run the podcast clipper pipeline.
    Payload: {source, niche, max_clips, template, brand_name, rights_status}
    """
    from engines.podcast_pipeline import run_pipeline
    
    result = run_pipeline(
        source=payload.get("source"),
        niche=payload.get("niche", "education"),
        max_clips=payload.get("max_clips", 3),
        template=payload.get("template", "SPEAKER_FOCUS"),
        caption_style=payload.get("caption_style", "default"),
        brand_name=payload.get("brand_name", ""),
        rights_status=payload.get("rights_status", "UNKNOWN"),
    )
    
    await ws_manager.broadcast({"event": "podcast:done", "data": {
        "clips_created": result.get("clips_created", 0),
        "status": result.get("status", ""),
    }})
    
    return result

@app.get("/api/podcast/queue")
async def get_podcast_queue():
    """Get items in the publish queue."""
    return {"queue": get_queue("queued")}

@app.get("/api/podcast/clips")
async def get_podcast_clips():
    """Get all clips with their status."""
    from engines.podcast_db import get_db
    conn = get_db()
    rows = conn.execute(
        "SELECT c.*, ps.title as source_title, ps.channel "
        "FROM clips c LEFT JOIN podcast_sources ps ON c.source_id = ps.id "
        "ORDER BY c.created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return {"clips": [dict(r) for r in rows]}

@app.get("/api/podcast/clips/{status}")
async def get_clips_by_status_endpoint(status: str):
    """Get clips filtered by status."""
    return {"clips": get_clips_by_status(status)}

@app.post("/api/podcast/clip/{clip_id}/approve")
async def approve_clip(clip_id: int):
    """Approve a clip for publishing."""
    from engines.podcast_db import update_clip_status, enqueue_clip
    update_clip_status(clip_id, "approved")
    queue_id = enqueue_clip(clip_id)
    return {"success": True, "queue_id": queue_id}

@app.post("/api/podcast/clip/{clip_id}/reject")
async def reject_clip(clip_id: int):
    """Reject a clip."""
    from engines.podcast_db import update_clip_status
    update_clip_status(clip_id, "rejected")
    return {"success": True}

@app.post("/api/podcast/clip/{clip_id}/publish")
async def publish_clip(clip_id: int):
    """Publish a clip to Instagram."""
    from engines.podcast_db import get_clip, update_clip_status
    from platforms.instagram_uploader import post_with_retry
    
    clip = get_clip(clip_id)
    if not clip:
        return {"success": False, "error": "Clip not found"}
    
    result = post_with_retry(
        clip["video_path"],
        clip.get("caption", ""),
        json.loads(clip.get("hashtags", "[]")) if clip.get("hashtags") else [],
    )
    
    if result["success"]:
        update_clip_status(clip_id, "published")
        await ws_manager.broadcast({"event": "podcast:published", "data": {
            "clip_id": clip_id,
            "post_id": result.get("post_id", ""),
        }})
    
    return result

@app.get("/api/podcast/templates")
async def get_templates():
    """Get available video templates."""
    from engines.podcast_renderer import get_available_templates, get_available_caption_styles
    return {
        "templates": get_available_templates(),
        "caption_styles": get_available_caption_styles(),
    }

@app.get("/api/podcast/qa/{clip_id}")
async def get_qa_result(clip_id: int):
    """Get QA result for a clip."""
    from engines.podcast_db import get_qa_result
    return get_qa_result(clip_id)

@app.get("/api/podcast/settings")
async def get_podcast_settings():
    """Get podcast clipper settings."""
    return {
        "default_niche": "education",
        "max_clips": 3,
        "template": "SPEAKER_FOCUS",
        "caption_style": "default",
        "auto_publish": False,
        "timezone": "Asia/Karachi",
        "rights_status": "UNKNOWN",
    }

@app.post("/api/podcast/settings")
async def update_podcast_settings(payload: dict):
    """Update podcast clipper settings."""
    # Store settings in a JSON file
    settings_path = Path(__file__).parent.parent / "data" / "podcast_settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(settings_path, "w") as f:
        json.dump(payload, f, indent=2)
    
    return {"success": True, "settings": payload}

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
