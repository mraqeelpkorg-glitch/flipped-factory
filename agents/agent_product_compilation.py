"""
Agent 7: Product Compilation — Products → "Top 10" video
Creates product showcase compilation videos.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_product_compilation")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(products = None, niche: str = "health_fitness", affiliate_code: str = "") -> dict:
    """
    Create product compilation video.

    products = [
        {"name": "Vitamin D3", "benefit": "Boosts immunity", "price": "$12"},
        ...
    ]

    Steps:
    1. Input validation + rights gate (verify product/brand/price)
    2. Safety gate
    3. Create video
    4. Dedup check → QA check → analytics
    """
    try:
        from engines.video_builder import create_text_video
        from tools.tts_engine import text_to_speech
        from tools.video_editor import add_audio_track
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: Product Compilation | Niche: {niche}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Default products ───────────────────────────────────────────────
        if not products:
            products = [
                {"name": "Vitamin D3 + K2", "benefit": "Immune boost & bone health", "price": "$15"},
                {"name": "Omega-3 Fish Oil", "benefit": "Heart & brain health", "price": "$18"},
                {"name": "Magnesium Glycinate", "benefit": "Better sleep & recovery", "price": "$14"},
                {"name": "Probiotics", "benefit": "Gut health & digestion", "price": "$20"},
                {"name": "Zinc Supplement", "benefit": "Skin & immune support", "price": "$10"},
            ]

        if not isinstance(products, list) or len(products) < 2:
            return {"success": False, "error": "products must be a list with at least 2 items"}

        # Validate each product has required fields
        for i, p in enumerate(products):
            if not isinstance(p, dict):
                return {"success": False, "error": f"Product {i} must be a dict"}
            if not p.get("name"):
                return {"success": False, "error": f"Product {i} missing 'name'"}

        # ── 2. Rights gate ────────────────────────────────────────────────────
        product_names = ", ".join([p["name"] for p in products[:5]])
        rights = check_copyright(
            title=f"Product Compilation: {product_names}",
            description=f"Affiliate code: {affiliate_code}" if affiliate_code else "",
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 3. Safety gate ────────────────────────────────────────────────────
        full_text = " ".join([f"{p['name']} {p.get('benefit', '')}" for p in products])
        safety = check_safety(full_text)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Safety gate BLOCKED: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 4. Create script ──────────────────────────────────────────────────
        hook = f"Top {len(products)} supplements you need in 2026"
        body = " ".join([f"Number {i+1}: {p['name']} — {p.get('benefit', '')}." for i, p in enumerate(products[:5])])
        cta = "Links in bio! Follow for more health tips!"

        script = {"hook": hook, "body": body, "cta": cta, "duration": 60}

        # ── 5. Create video ───────────────────────────────────────────────────
        audio_path = str(PROCESSED_DIR / f"product_voiceover_{timestamp}.wav")
        text_to_speech(f"{hook} {body} {cta}", audio_path, rate=145)

        video_path = str(PROCESSED_DIR / f"product_video_{timestamp}.mp4")
        create_text_video(script, video_path)

        final_path = str(PROCESSED_DIR / f"product_final_{timestamp}.mp4")
        add_audio_track(video_path, audio_path, final_path, volume=0.8)

        # ── 6. Dedup check ────────────────────────────────────────────────────
        dup = check_duplicate(source_url=product_names)
        if dup.get("is_duplicate"):
            return {
                "success": False,
                "error": f"Duplicate detected: {dup.get('reason')}",
            }

        # ── 7. QA check ───────────────────────────────────────────────────────
        qa = run_qa(final_path)
        if qa["overall"] == "FAILED":
            return {
                "success": False,
                "error": f"QA failed: {qa['errors']}",
            }

        # ── 8. Analytics ──────────────────────────────────────────────────────
        video_id = log_video(
            title=hook[:60],
            niche=niche,
            agent_type="product_compilation",
            video_path=final_path,
        )

        register_content(
            video_path=final_path,
            source_url=product_names,
            agent_type="product_compilation",
        )

        return {
            "success": True,
            "products_count": len(products),
            "video_path": final_path,
            "video_id": video_id,
            "safety_status": safety_status,
            "qa_status": qa["overall"],
            "affiliate_code": affiliate_code,
        }

    except Exception as e:
        logger.error(f"Agent Product Compilation failed: {e}")
        return {"success": False, "error": str(e)}
