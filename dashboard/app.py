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
from fastapi.responses import HTMLResponse, FileResponse
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
    """Generate a single video with full production lifecycle + real-time progress."""
    import os, time
    niche = payload.get("niche", "health_fitness")
    topic = payload.get("topic") or select_topic(niche)
    job_id = f"gen_{niche}_{int(time.time())}"

    from engines.content_creator import generate_script_with_ai, save_script
    from engines.video_builder import create_text_video
    from tools.tts_engine import text_to_speech
    from tools.video_editor import add_audio_track
    from engines.safety_gate import check_safety, get_safety_status
    from engines.dedup_engine import check_duplicate, register_content
    from engines.shared_qa import run_qa
    from engines.revenue_tracker import log_video

    STEP_NAMES = ["script", "safety", "video", "tts", "merge", "qa", "register", "done"]
    async def emit_step(idx, status="active"):
        await ws_manager.broadcast({"event": "progress", "data": {
            "tracker": "progress-tracker", "job": job_id,
            "step": idx, "status": status,
            "step_name": STEP_NAMES[idx] if idx < len(STEP_NAMES) else "",
            "total_steps": len(STEP_NAMES),
        }})

    # Step 0 — Script
    await emit_step(0, "active")
    script = generate_script_with_ai(topic, niche, duration=45)
    save_script(script, f"manual_{niche}")
    full_text = f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}"
    await emit_step(0, "done")

    # Step 1 — Safety
    await emit_step(1, "active")
    safety = check_safety(full_text)
    safety_status = get_safety_status(safety)
    await emit_step(1, "done")
    if safety_status == "BLOCKED":
        await emit_step(1, "error")
        return {"success": False, "error": f"Content blocked by safety gate (risk={safety.get('overall_risk', 0):.3f})"}

    # Step 2 — Video
    await emit_step(2, "active")
    timestamp = datetime.now().strftime("%H%M%S")
    base_dir = Path(__file__).parent.parent / "data" / "videos" / "processed"
    base_dir.mkdir(parents=True, exist_ok=True)
    base = str(base_dir / f"manual_{niche}_{timestamp}")
    video_path = f"{base}.mp4"
    create_text_video(script, video_path)
    await emit_step(2, "done")

    # Step 3 — TTS
    await emit_step(3, "active")
    audio_path = f"{base}_audio.wav"
    text_to_speech(full_text, audio_path, rate=150)
    await emit_step(3, "done")

    # Step 4 — Merge
    await emit_step(4, "active")
    final_path = f"{base}_final.mp4"
    add_audio_track(video_path, audio_path, final_path, volume=0.8)
    await emit_step(4, "done")

    # Step 5 — QA
    await emit_step(5, "active")
    qa = run_qa(final_path)
    await emit_step(5, "done")

    # Dedup check
    dup = check_duplicate(source_url=f"manual_{niche}_{topic}")
    if dup.get("is_duplicate"):
        return {"success": False, "error": "Duplicate content detected"}

    # Step 6 — Register
    await emit_step(6, "active")
    video_id = log_video(
        title=script.get("hook", topic)[:60],
        niche=niche,
        agent_type="manual",
        video_path=final_path
    )
    register_content(
        video_path=final_path,
        source_url=f"manual_{niche}_{topic}",
        agent_type="manual",
    )
    await emit_step(6, "done")

    abs_path = os.path.abspath(final_path)
    file_size = os.path.getsize(final_path) if os.path.exists(final_path) else 0

    # Step 7 — Done
    await emit_step(7, "done")

    await ws_manager.broadcast({"event": "video:created", "data": {
        "niche": niche, "topic": topic, "hook": script.get("hook", ""),
        "path": abs_path, "video_id": video_id,
    }})

    return {
        "success": True,
        "video_id": video_id,
        "hook": script.get("hook", ""),
        "path": abs_path,
        "filename": os.path.basename(final_path),
        "size_kb": file_size // 1024,
        "safety": safety_status,
        "qa": qa["overall"],
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
    import time
    job_id = f"pod_{int(time.time())}"

    await ws_manager.broadcast({"event": "progress", "data": {
        "tracker": "pod-progress-tracker", "job": job_id,
        "step": 0, "status": "active",
        "step_name": "download", "total_steps": 6,
    }})

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

    # Mark all steps done
    for i in range(6):
        await ws_manager.broadcast({"event": "progress", "data": {
            "tracker": "pod-progress-tracker", "job": job_id,
            "step": i, "status": "done",
        }})
    await ws_manager.broadcast({"event": "progress", "data": {
        "tracker": "pod-progress-tracker", "job": job_id,
        "step": 6, "status": "done", "done": True,
        "success": result.get("status") != "error",
    }})

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

# ─── Agent Runner Endpoints ────────────────────────────────────────────────────
@app.get("/api/agents")
async def get_agents():
    """Get list of all 12 agents."""
    from engines.agent_runner import get_available_agents
    return {"agents": get_available_agents()}

@app.post("/api/agents/run")
async def run_agent_endpoint(payload: dict):
    """Run any agent through production lifecycle."""
    from engines.agent_runner import run_agent
    agent_type = payload.get("agent_type", "")
    kwargs = {k: v for k, v in payload.items() if k != "agent_type" and k != "auto_publish"}
    auto_publish = payload.get("auto_publish", False)

    result = run_agent(agent_type, auto_publish=auto_publish, **kwargs)

    await ws_manager.broadcast({"event": "agent:done", "data": {
        "agent_type": agent_type,
        "success": result.get("success", False),
        "job_id": result.get("job_id", ""),
    }})

    return result

# ─── Job Management Endpoints ──────────────────────────────────────────────────
@app.get("/api/jobs")
async def get_jobs(agent_type: str = None, status: str = None):
    """Get jobs with optional filters."""
    from engines.job_manager import get_jobs
    return {"jobs": get_jobs(agent_type=agent_type, status=status)}

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job details."""
    from engines.job_manager import get_job, get_job_stages
    job = get_job(job_id)
    stages = get_job_stages(job_id)
    return {"job": job, "stages": stages}

@app.get("/api/jobs/stats")
async def get_job_stats():
    """Get job queue statistics."""
    from engines.job_manager import get_queue_stats
    return get_queue_stats()

@app.post("/api/jobs/{job_id}/cancel")
async def cancel_job_endpoint(job_id: str):
    """Cancel a job."""
    from engines.job_manager import cancel_job
    cancel_job(job_id)
    return {"success": True}

# ─── Publish Queue Endpoints ───────────────────────────────────────────────────
@app.get("/api/production-queue")
async def get_publish_queue():
    """Get items pending approval."""
    from engines.scheduler import get_pending_approvals
    return {"queue": get_pending_approvals()}

@app.get("/api/production-queue/approved")
async def get_approved_queue():
    """Get approved items ready for publishing."""
    from engines.scheduler import get_approved_items
    return {"queue": get_approved_items()}

@app.post("/api/production-queue/{queue_id}/approve")
async def approve_queue_item(queue_id: int):
    """Approve an item for publishing."""
    from engines.scheduler import approve_item
    approve_item(queue_id)
    return {"success": True}

@app.post("/api/production-queue/{queue_id}/reject")
async def reject_queue_item(queue_id: int):
    """Reject a queued item."""
    from engines.scheduler import reject_item
    reject_item(queue_id)
    return {"success": True}

@app.post("/api/production-queue/publish")
async def publish_queue_endpoint():
    """Process the publish queue."""
    from main import publish_queue
    results = publish_queue()
    return {"results": results}

@app.get("/api/production-queue/stats")
async def get_queue_stats_endpoint():
    """Get publish queue statistics."""
    from engines.scheduler import get_queue_stats
    return get_queue_stats()

# ─── Dedup Endpoints ──────────────────────────────────────────────────────────
# ─── Video Serving ────────────────────────────────────────────────────────────
@app.get("/api/videos")
async def list_videos():
    """List all generated videos with metadata."""
    import os
    processed_dir = Path(__file__).parent.parent / "data" / "videos" / "processed"
    videos = []
    if processed_dir.exists():
        for f in sorted(processed_dir.glob("*.mp4"), key=os.path.getmtime, reverse=True):
            stat = os.stat(f)
            videos.append({
                "filename": f.name,
                "path": str(f.resolve()),
                "size_kb": stat.st_size // 1024,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "play_url": f"/api/serve-video/{f.name}",
            })
    return {"videos": videos, "total": len(videos)}

@app.get("/api/serve-video/{filename}")
async def serve_video(filename: str):
    """Serve a video file for browser playback."""
    import os
    video_path = Path(__file__).parent.parent / "data" / "videos" / "processed" / filename
    if not video_path.exists() or not video_path.is_file():
        return {"error": "Video not found"}
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=filename,
    )

@app.get("/api/dedup/history")
async def get_dedup_history(agent_type: str = None):
    """Get content hash history."""
    from engines.dedup_engine import get_content_history
    return {"history": get_content_history(agent_type=agent_type)}

@app.get("/api/dedup/check")
async def check_dedup(source_url: str, start: float = None, end: float = None):
    """Check if content is a duplicate."""
    from engines.dedup_engine import check_duplicate
    return check_duplicate(source_url, start, end)

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
