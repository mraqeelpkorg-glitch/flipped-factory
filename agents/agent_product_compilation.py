"""
Agent 7: Product Compilation — Products → "Top 10" video
Creates product showcase compilation videos.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_product_compilation")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(products: list = None, niche: str = "health_fitness", affiliate_code: str = "") -> dict:
    """
    Create product compilation video.
    
    products = [
        {"name": "Vitamin D3", "benefit": "Boosts immunity", "price": "$12"},
        ...
    ]
    
    Steps:
    1. Get product list
    2. Generate comparison script
    3. Create showcase slides
    4. Generate voiceover
    5. Combine into compilation
    """
    from engines.content_creator import get_template_script
    from engines.video_builder import create_text_video
    from tools.tts_engine import text_to_speech
    from tools.video_editor import add_audio_track
    from engines.revenue_tracker import log_video
    
    logger.info(f"Agent: Product Compilation | Niche: {niche}")
    
    # Default products
    if not products:
        products = [
            {"name": "Vitamin D3 + K2", "benefit": "Immune boost & bone health", "price": "$15"},
            {"name": "Omega-3 Fish Oil", "benefit": "Heart & brain health", "price": "$18"},
            {"name": "Magnesium Glycinate", "benefit": "Better sleep & recovery", "price": "$14"},
            {"name": "Probiotics", "benefit": "Gut health & digestion", "price": "$20"},
            {"name": "Zinc Supplement", "benefit": "Skin & immune support", "price": "$10"},
        ]
    
    # Generate script
    product_list = ", ".join([p["name"] for p in products[:5]])
    hook = f"Top {len(products)} supplements you need in 2026"
    body = " ".join([f"Number {i+1}: {p['name']} — {p['benefit']}." for i, p in enumerate(products[:5])])
    cta = "Links in bio! Follow for more health tips!"
    
    script = {"hook": hook, "body": body, "cta": cta, "duration": 60}
    
    # TTS
    timestamp = datetime.now().strftime("%H%M%S")
    audio_path = f"{PROCESSED_DIR}/product_voiceover_{timestamp}.wav"
    text_to_speech(f"{hook} {body} {cta}", audio_path, rate=145)
    
    # Video
    video_path = f"{PROCESSED_DIR}/product_video_{timestamp}.mp4"
    create_text_video(script, video_path)
    
    # Final
    final_path = f"{PROCESSED_DIR}/product_final_{timestamp}.mp4"
    add_audio_track(video_path, audio_path, final_path, volume=0.8)
    
    video_id = log_video(
        title=hook[:60],
        niche=niche,
        agent_type="product_compilation",
        video_path=final_path
    )
    
    return {
        "success": True,
        "products_count": len(products),
        "video_path": final_path,
        "video_id": video_id,
    }
