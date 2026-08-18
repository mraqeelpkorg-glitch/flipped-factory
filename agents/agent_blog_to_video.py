"""
Agent 3: Blog to Video — Blog post → Instagram Reel
Scrapes blog content, generates TTS voiceover, creates video.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_blog_to_video")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(blog_url_or_text: str, niche: str = "tech_ai", language: str = "en") -> dict:
    """
    Convert blog content to Instagram video.
    
    Steps:
    1. Get blog content (URL scrape or text)
    2. Extract key points (AI or template)
    3. Generate TTS voiceover
    4. Create video with text overlays
    """
    from engines.content_creator import generate_script_with_ai, get_template_script
    from tools.tts_engine import text_to_speech
    from engines.video_builder import create_text_video
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Blog to Video | Source: {blog_url_or_text[:50]}")
    
    # 1. Get content
    if blog_url_or_text.startswith("http"):
        # Scrape URL
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
    
    # 2. Generate script
    if blog_text:
        script = generate_script_with_ai(blog_text[:500], niche, duration=45, language=language)
    else:
        script = get_template_script(niche)
    
    # 3. Generate TTS
    output_dir = str(PROCESSED_DIR)
    timestamp = datetime.now().strftime("%H%M%S")
    audio_path = f"{output_dir}/blog_voiceover_{timestamp}.wav"
    
    text_to_speech(
        f"{script['hook']} {script['body']} {script['cta']}",
        audio_path,
        rate=150
    )
    
    # 4. Create video
    video_path = f"{output_dir}/blog_video_{timestamp}.mp4"
    create_text_video(script, video_path)
    
    # 5. Add audio
    from tools.video_editor import add_audio_track
    final_path = f"{output_dir}/blog_final_{timestamp}.mp4"
    add_audio_track(video_path, audio_path, final_path, volume=0.8)
    
    # 6. Log
    video_id = log_video(
        title=script.get("hook", "Blog Video")[:60],
        niche=niche,
        agent_type="blog_to_video",
        video_path=final_path,
        language=language
    )
    
    return {
        "success": True,
        "title": script.get("hook", ""),
        "video_path": final_path,
        "audio_path": audio_path,
        "duration": script.get("duration", 45),
        "video_id": video_id,
    }
