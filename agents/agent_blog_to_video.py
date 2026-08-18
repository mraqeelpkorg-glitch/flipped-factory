"""
Agent 3: Blog to Video — Blog post → Instagram Reel
Scrapes blog content, generates TTS voiceover, creates video.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_blog_to_video")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(blog_url_or_text: str, niche: str = "tech_ai", language: str = "en") -> dict:
    """
    Convert blog content to Instagram video.

    Steps:
    1. Input validation + rights gate (store source URL)
    2. Get blog content (URL scrape or text)
    3. Safety gate
    4. Generate script + create video
    5. Dedup check → QA check → analytics
    """
    try:
        from engines.content_creator import generate_script_with_ai, get_template_script
        from tools.tts_engine import text_to_speech
        from engines.video_builder import create_text_video
        from tools.video_editor import add_audio_track
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: Blog to Video | Source: {blog_url_or_text[:50] if blog_url_or_text else 'empty'}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Input validation ──────────────────────────────────────────────
        if not blog_url_or_text or not blog_url_or_text.strip():
            return {"success": False, "error": "blog_url_or_text must not be empty"}

        # ── 2. Get blog content ───────────────────────────────────────────────
        blog_text = ""
        source_url = blog_url_or_text if blog_url_or_text.startswith("http") else ""

        if blog_url_or_text.startswith("http"):
            try:
                import httpx
                resp = httpx.get(blog_url_or_text, follow_redirects=True, timeout=10)
                from html.parser import HTMLParser

                class TextExtractor(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.text = []
                        self.skip = False
                    def handle_starttag(self, tag, attrs):
                        if tag in ["script", "style"]:
                            self.skip = True
                    def handle_endtag(self, tag):
                        if tag in ["script", "style"]:
                            self.skip = False
                    def handle_data(self, data):
                        if not self.skip:
                            self.text.append(data.strip())

                extractor = TextExtractor()
                extractor.feed(resp.text)
                blog_text = " ".join([t for t in extractor.text if t])[:2000]
            except Exception as e:
                logger.warning(f"Scrape failed: {e}, using template")
                blog_text = ""
        else:
            blog_text = blog_url_or_text

        # ── 3. Rights gate ────────────────────────────────────────────────────
        rights = check_copyright(
            title=f"Blog to Video: {source_url or blog_text[:60]}",
            description=blog_text[:200] if blog_text else "",
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 4. Safety gate ────────────────────────────────────────────────────
        safety_text = blog_text or blog_url_or_text
        safety = check_safety(safety_text)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 5. Generate script ────────────────────────────────────────────────
        if blog_text:
            script = generate_script_with_ai(blog_text[:500], niche, duration=45, language=language)
        else:
            script = get_template_script(niche)

        full_text = f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}"

        # ── 6. Create video ───────────────────────────────────────────────────
        audio_path = str(PROCESSED_DIR / f"blog_voiceover_{timestamp}.wav")
        text_to_speech(full_text, audio_path, rate=150)

        video_path = str(PROCESSED_DIR / f"blog_video_{timestamp}.mp4")
        create_text_video(script, video_path)

        final_path = str(PROCESSED_DIR / f"blog_final_{timestamp}.mp4")
        add_audio_track(video_path, audio_path, final_path, volume=0.8)

        # ── 7. Dedup check ────────────────────────────────────────────────────
        dup = check_duplicate(source_url=source_url or blog_text[:100])
        if dup.get("is_duplicate"):
            return {
                "success": False,
                "error": f"Duplicate detected: {dup.get('reason')}",
            }

        # ── 8. QA check ───────────────────────────────────────────────────────
        qa = run_qa(final_path)
        if qa["overall"] == "FAILED":
            return {
                "success": False,
                "error": f"QA failed: {qa['errors']}",
            }

        # ── 9. Analytics ──────────────────────────────────────────────────────
        video_id = log_video(
            title=script.get("hook", "Blog Video")[:60],
            niche=niche,
            agent_type="blog_to_video",
            video_path=final_path,
            language=language,
        )

        register_content(
            video_path=final_path,
            source_url=source_url,
            agent_type="blog_to_video",
        )

        return {
            "success": True,
            "title": script.get("hook", ""),
            "video_path": final_path,
            "audio_path": audio_path,
            "duration": script.get("duration", 45),
            "video_id": video_id,
            "source_url": source_url,
            "safety_status": safety_status,
            "qa_status": qa["overall"],
        }

    except Exception as e:
        logger.error(f"Agent Blog to Video failed: {e}")
        return {"success": False, "error": str(e)}
