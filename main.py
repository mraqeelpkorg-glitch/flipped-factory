"""
Flipped Factory — Main Orchestrator
Coordinates all agents, engines, and platforms.
"""
import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "logs" / "factory.log"),
    ]
)
logger = logging.getLogger("orchestrator")

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent))


def run_daily_pipeline(videos_per_day: int = 3, languages: list = None):
    """
    Main daily pipeline:
    1. Check trends
    2. Select niches
    3. Generate scripts
    4. Create videos (one per agent type)
    5. Post to Instagram
    """
    from engines.trend_engine import refresh_trends, rank_niches
    from engines.niche_selector import select_niche, select_topic, get_hashtags, get_niche_info
    from engines.content_creator import generate_script_with_ai, get_template_script, save_script
    from engines.video_builder import create_text_video
    from engines.revenue_tracker import init_db, update_daily_log, log_video
    from config import TREND_KEYWORDS, VIDEOS_PER_DAY
    
    if languages is None:
        languages = ["en"]
    
    init_db()
    logger.info("=== FLIPPED FACTORY — Daily Pipeline ===")
    
    # 1. Trends
    logger.info("Step 1: Checking trends...")
    trend_data = refresh_trends(TREND_KEYWORDS)
    ranked = trend_data.get("ranked", [])
    
    # 2. Select niches for today
    logger.info("Step 2: Selecting niches...")
    selected_niches = []
    for i in range(min(videos_per_day, len(ranked) or 10)):
        niche = select_niche(ranked)
        if niche not in selected_niches:
            selected_niches.append(niche)
    
    # 3. Create videos
    logger.info("Step 3: Creating videos...")
    videos_created = []
    
    for i, niche in enumerate(selected_niches):
        logger.info(f"  Video {i+1}/{len(selected_niches)}: {niche}")
        
        # Select topic
        topic = select_topic(niche)
        
        # Generate script
        script = generate_script_with_ai(topic, niche, duration=45)
        script["niche"] = niche
        script["topic"] = topic
        save_script(script, f"daily_{i+1}")
        
        # Create video
        timestamp = datetime.now().strftime("%H%M%S")
        video_path = f"data/videos/processed/daily_{niche}_{timestamp}.mp4"
        
        success = create_text_video(script, video_path)
        
        if success:
            # Add TTS
            from tools.tts_engine import text_to_speech
            from tools.video_editor import add_audio_track
            
            audio_path = f"data/videos/processed/daily_audio_{niche}_{timestamp}.wav"
            text_to_speech(
                f"{script['hook']} {script['body']} {script['cta']}",
                audio_path,
                rate=150
            )
            
            final_path = f"data/videos/processed/daily_final_{niche}_{timestamp}.mp4"
            add_audio_track(video_path, audio_path, final_path, volume=0.8)
            
            # Log to database
            video_id = log_video(
                title=script.get("hook", topic)[:60],
                niche=niche,
                agent_type="daily_pipeline",
                video_path=final_path
            )
            
            videos_created.append({
                "niche": niche,
                "topic": topic,
                "hook": script.get("hook", ""),
                "path": final_path,
                "video_id": video_id,
                "hashtags": get_hashtags(niche),
            })
            
            logger.info(f"  ✅ Created: {script.get('hook', '')[:40]}...")
        else:
            logger.warning(f"  ❌ Failed to create video for {niche}")
    
    # 4. Update daily log
    update_daily_log(videos_created=len(videos_created), top_niche=selected_niches[0] if selected_niches else "")
    
    logger.info(f"=== Pipeline Complete: {len(videos_created)} videos created ===")
    
    return {
        "success": True,
        "videos_created": videos_created,
        "niches_used": selected_niches,
        "trend_ranking": ranked[:5],
    }


def post_to_instagram(video_path: str, caption: str, hashtags: list) -> dict:
    """Post a single video to Instagram."""
    from platforms.instagram_uploader import post_with_retry
    
    logger.info(f"Posting to Instagram: {video_path}")
    result = post_with_retry(video_path, caption, hashtags)
    
    if result["success"]:
        from engines.revenue_tracker import log_post, update_video_status
        logger.info(f"Posted: {result.get('post_url')}")
    else:
        logger.error(f"Post failed: {result.get('error')}")
    
    return result


def show_status():
    """Show current factory status."""
    from engines.revenue_tracker import get_dashboard_stats
    
    stats = get_dashboard_stats()
    
    print("\n╔══════════════════════════════════════════╗")
    print("║       FLIPPED FACTORY — STATUS           ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  Total Videos:    {stats['total_videos']:>6}                ║")
    print(f"║  Total Posts:     {stats['total_posts']:>6}                ║")
    print(f"║  Today Videos:    {stats['today_videos']:>6}                ║")
    print(f"║  Today Posts:     {stats['today_posts']:>6}                ║")
    print(f"║  Total Revenue:   ${stats['total_revenue']:>8.2f}            ║")
    print("╠══════════════════════════════════════════╣")
    
    if stats["niche_stats"]:
        print("║  Niche Breakdown:                       ║")
        for ns in stats["niche_stats"][:5]:
            print(f"║    {ns['niche']:<20} {ns['count']:>4} videos  ║")
    
    print("╚══════════════════════════════════════════╝")


# ─── CLI Entry Point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if cmd == "run":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        result = run_daily_pipeline(videos_per_day=count)
        print(f"\n✅ Done: {len(result['videos_created'])} videos created")
        for v in result["videos_created"]:
            print(f"  📹 {v['hook'][:50]}... [{v['niche']}]")
    
    elif cmd == "post":
        if len(sys.argv) < 4:
            print("Usage: python main.py post <video_path> <caption>")
            sys.exit(1)
        video = sys.argv[2]
        caption = sys.argv[3]
        result = post_to_instagram(video, caption, ["reels", "viral"])
        print(f"{'✅' if result['success'] else '❌'} {result}")
    
    elif cmd == "status":
        show_status()
    
    elif cmd == "setup":
        from platforms.instagram_uploader import login
        username = input("Instagram username: ")
        password = input("Instagram password: ")
        success = login(username, password)
        print(f"{'✅ Login successful' if success else '❌ Login failed'}")
    
    else:
        print("""
Flipped Factory — AI Content Factory

Commands:
  python main.py run [count]    — Create N videos (default: 3)
  python main.py post <vid> <cap> — Post video to Instagram
  python main.py status         — Show factory status
  python main.py setup          — Setup Instagram credentials
        """)
