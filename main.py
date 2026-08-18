"""
Flipped Factory — Main Orchestrator
Coordinates all 12 agents, engines, and platforms.
"""
import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime

# Setup logging
Path(__file__).parent.mkdir(exist_ok=True, parents=True)
Path(__file__).parent / "logs"
(Path(__file__).parent / "logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "logs" / "factory.log"),
    ]
)
logger = logging.getLogger("orchestrator")

sys.path.insert(0, str(Path(__file__).parent))


# ─── Agent Dispatcher ─────────────────────────────────────────────────────────

def run_agent(agent_type: str, auto_publish: bool = False, **kwargs) -> dict:
    """
    Run any agent through the production lifecycle.

    Commands:
        python main.py agent youtube_clipper youtube_url="..." niche="tech"
        python main.py agent podcast_clipper source="..." max_clips=3
        python main.py agent blog_to_video blog_url="..." niche="health"
        python main.py agent remix_flip video_path="..." niche="finance"
        python main.py agent dub_flip video_path="..." languages="en,es,hi"
        python main.py agent data_to_video niche="tech"
        python main.py agent product_compilation niche="health"
        python main.py agent bts_educational bts_video_path="..." niche="education"
        python main.py agent trending_niche niche="tech"
        python main.py agent course_teaser course_module="..." niche="education"
        python main.py agent live_highlights live_video_path="..." niche="tech"
        python main.py agent screenshot_tutorial screenshots_dir="..." niche="tech"
    """
    from engines.agent_runner import run_agent as _run
    return _run(agent_type, auto_publish=auto_publish, **kwargs)


# ─── Daily Pipeline ───────────────────────────────────────────────────────────

def run_daily_pipeline(videos_per_day: int = 3, languages: list = None):
    """
    Main daily pipeline:
    1. Check trends
    2. Select niches
    3. Create videos using agent_runner (with QA + dedup)
    4. Queue for publishing
    """
    from engines.trend_engine import refresh_trends
    from engines.niche_selector import select_niche, select_topic, get_hashtags
    from engines.content_creator import generate_script_with_ai, save_script
    from engines.video_builder import create_text_video
    from engines.revenue_tracker import init_db, update_daily_log, log_video
    from engines.agent_runner import run_agent as _run
    from config import TREND_KEYWORDS

    if languages is None:
        languages = ["en"]

    init_db()
    logger.info("=== FLIPPED FACTORY — Daily Pipeline ===")

    # 1. Trends
    logger.info("Step 1: Checking trends...")
    trend_data = refresh_trends(TREND_KEYWORDS)
    ranked = trend_data.get("ranked", [])

    # 2. Select niches
    logger.info("Step 2: Selecting niches...")
    selected_niches = []
    for _ in range(min(videos_per_day, len(ranked) or 10)):
        niche = select_niche(ranked)
        if niche not in selected_niches:
            selected_niches.append(niche)

    # 3. Create videos
    logger.info("Step 3: Creating videos via agent_runner...")
    videos_created = []

    for i, niche in enumerate(selected_niches):
        logger.info(f"  Video {i+1}/{len(selected_niches)}: {niche}")
        topic = select_topic(niche)

        try:
            result = _run(
                "blog_to_video",
                auto_publish=False,
                blog_url_or_text=topic,
                niche=niche,
                language=languages[0] if languages else "en",
            )

            if result.get("success"):
                videos_created.append({
                    "niche": niche,
                    "topic": topic,
                    "hook": result.get("metadata", {}).get("hook", topic),
                    "path": result.get("video_path", ""),
                    "video_id": result.get("video_id"),
                    "job_id": result.get("job_id"),
                    "hashtags": get_hashtags(niche),
                })
                logger.info(f"  Created: {topic[:40]}...")
            else:
                logger.warning(f"  Failed: {result.get('error', 'unknown')}")
        except Exception as e:
            logger.error(f"  Exception: {e}")

    update_daily_log(
        videos_created=len(videos_created),
        top_niche=selected_niches[0] if selected_niches else "",
    )

    logger.info(f"=== Pipeline Complete: {len(videos_created)} videos ===")
    return {
        "success": True,
        "videos_created": videos_created,
        "niches_used": selected_niches,
        "trend_ranking": ranked[:5],
    }


# ─── Instagram Publishing ─────────────────────────────────────────────────────

def post_to_instagram(video_path: str, caption: str, hashtags: list) -> dict:
    """Post a single video to Instagram."""
    from platforms.instagram_uploader import post_with_retry
    logger.info(f"Posting to Instagram: {video_path}")
    result = post_with_retry(video_path, caption, hashtags)
    if result["success"]:
        logger.info(f"Posted: {result.get('post_url')}")
    else:
        logger.error(f"Post failed: {result.get('error')}")
    return result


def publish_queue():
    """Process the publish queue — post approved items."""
    from engines.scheduler import get_ready_to_publish, mark_published, mark_failed
    from platforms.instagram_uploader import post_with_retry

    items = get_ready_to_publish(limit=5)
    if not items:
        logger.info("No items ready to publish")
        return []

    results = []
    for item in items:
        logger.info(f"Publishing: {item['video_path']}")
        hashtags = json.loads(item.get("hashtags", "[]"))
        result = post_with_retry(item["video_path"], item["caption"], hashtags)

        if result["success"]:
            mark_published(item["id"], result["post_id"], result["post_url"])
            results.append({"queue_id": item["id"], "success": True, "post_url": result["post_url"]})
        else:
            mark_failed(item["id"], result.get("error", "unknown"))
            results.append({"queue_id": item["id"], "success": False, "error": result.get("error")})

    return results


# ─── Status ───────────────────────────────────────────────────────────────────

def show_status():
    """Show factory status."""
    from engines.revenue_tracker import get_dashboard_stats
    from engines.job_manager import get_queue_stats
    from engines.scheduler import get_queue_stats as get_publish_stats

    stats = get_dashboard_stats()
    job_stats = get_queue_stats()
    pub_stats = get_publish_stats()

    print("\n╔══════════════════════════════════════════════╗")
    print("║       FLIPPED FACTORY — STATUS               ║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  Total Videos:      {stats['total_videos']:>6}                   ║")
    print(f"║  Total Posts:       {stats['total_posts']:>6}                   ║")
    print(f"║  Today Videos:      {stats['today_videos']:>6}                   ║")
    print(f"║  Total Revenue:     ${stats['total_revenue']:>8.2f}               ║")
    print("╠══════════════════════════════════════════════╣")
    print("║  Job Queue:                                 ║")
    print(f"║    Queued:          {job_stats.get('queued', 0):>6}                   ║")
    print(f"║    Running:         {job_stats.get('running', 0):>6}                   ║")
    print(f"║    Completed:       {job_stats.get('completed', 0):>6}                   ║")
    print(f"║    Failed:          {job_stats.get('failed', 0):>6}                   ║")
    print("╠══════════════════════════════════════════════╣")
    print("║  Publish Queue:                             ║")
    print(f"║    Pending Approval:{pub_stats.get('pending_approval', 0):>6}                   ║")
    print(f"║    Approved:        {pub_stats.get('approved', 0):>6}                   ║")
    print(f"║    Published:       {pub_stats.get('published', 0):>6}                   ║")
    print("╠══════════════════════════════════════════════╣")

    if stats.get("niche_stats"):
        print("║  Niche Breakdown:                           ║")
        for ns in stats["niche_stats"][:5]:
            print(f"║    {ns['niche']:<20} {ns['count']:>4} videos      ║")

    print("╚══════════════════════════════════════════════╝")


# ─── CLI Entry Point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "run":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        result = run_daily_pipeline(videos_per_day=count)
        print(f"\nDone: {len(result['videos_created'])} videos created")
        for v in result["videos_created"]:
            print(f"  {v['hook'][:50]}... [{v['niche']}]")

    elif cmd == "agent":
        if len(sys.argv) < 3:
            print("Usage: python main.py agent <type> [key=value ...]")
            print("Types: " + ", ".join([
                "youtube_clipper", "podcast_clipper", "blog_to_video",
                "remix_flip", "dub_flip", "data_to_video",
                "product_compilation", "bts_educational", "trending_niche",
                "course_teaser", "live_highlights", "screenshot_tutorial",
            ]))
            sys.exit(1)

        agent_type = sys.argv[2]
        kwargs = {}
        for arg in sys.argv[3:]:
            if "=" in arg:
                key, val = arg.split("=", 1)
                # Auto-parse types
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                elif val.isdigit():
                    val = int(val)
                elif val.replace(".", "").isdigit():
                    val = float(val)
                elif "," in val:
                    val = val.split(",")
                kwargs[key] = val

        result = run_agent(agent_type, **kwargs)
        status = "SUCCESS" if result.get("success") else "FAILED"
        print(f"\n[{status}] {agent_type}")
        if result.get("success"):
            print(f"  Video: {result.get('video_path', 'N/A')}")
            print(f"  Job ID: {result.get('job_id', 'N/A')}")
        else:
            print(f"  Error: {result.get('error', 'unknown')}")

    elif cmd == "publish":
        results = publish_queue()
        if not results:
            print("Nothing to publish")
        for r in results:
            status = "OK" if r["success"] else "FAIL"
            print(f"  [{status}] Queue #{r['queue_id']}: {r.get('post_url', r.get('error', ''))}")

    elif cmd == "post":
        if len(sys.argv) < 4:
            print("Usage: python main.py post <video_path> <caption>")
            sys.exit(1)
        video = sys.argv[2]
        caption = sys.argv[3]
        result = post_to_instagram(video, caption, ["reels", "viral"])
        print(f"{'OK' if result['success'] else 'FAIL'} {result}")

    elif cmd == "status":
        show_status()

    elif cmd == "setup":
        from platforms.instagram_uploader import login
        username = input("Instagram username: ")
        password = input("Instagram password: ")
        success = login(username, password)
        print(f"{'Login successful' if success else 'Login failed'}")

    elif cmd == "help":
        print("""
Flipped Factory — AI Content Factory (12 Agents)

Commands:
  python main.py run [count]              Create N videos (default: 3)
  python main.py agent <type> [k=v ...]  Run specific agent
  python main.py publish                  Publish approved queue items
  python main.py post <vid> <cap>         Post video to Instagram
  python main.py status                   Show factory status
  python main.py setup                    Setup Instagram credentials

Agent Types:
  youtube_clipper      YouTube video → Reels
  podcast_clipper      Podcast → Clips with TTS
  blog_to_video        Blog post → Video
  remix_flip           Re-edit with new hook
  dub_flip             Multi-language versions
  data_to_video        Stats → Infographic
  product_compilation  Top products showcase
  bts_educational      BTS → Tutorial
  trending_niche       Trending audio + topic
  course_teaser        Course preview clip
  live_highlights      Live stream → Clips
  screenshot_tutorial  Screenshots → Video
        """)

    else:
        print(f"Unknown command: {cmd}. Use 'python main.py help'")
