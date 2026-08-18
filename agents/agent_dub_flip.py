"""
Agent 5: Dub Flip — Multi-language video versions
Translates script to target languages, generates TTS in each.
Full production lifecycle: rights gate → safety gate → dedup → QA → analytics.
"""
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("agent_dub_flip")

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "videos" / "processed"


def run(video_path: str, niche: str = "health_fitness", languages = None) -> dict:
    """
    Create multi-language versions of a video.

    Steps:
    1. Input validation + rights gate
    2. Transcribe original
    3. Safety check on transcript
    4. For each language: translate → TTS → create video → safety gate → dedup → QA → log
    """
    if languages is None:
        languages = ["en", "es", "hi", "pt"]

    try:
        from tools.transcriber import transcribe_video
        from engines.content_creator import translate_script
        from tools.tts_engine import text_to_speech
        from engines.video_builder import create_text_video
        from tools.video_editor import add_audio_track
        from engines.revenue_tracker import log_video
        from engines.safety_gate import check_safety, get_safety_status
        from engines.dedup_engine import check_duplicate, register_content
        from engines.shared_qa import run_qa
        from engines.content_checker import check_copyright

        logger.info(f"Agent: Dub Flip | Languages: {languages}")

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")

        # ── 1. Input validation ──────────────────────────────────────────────
        if not video_path or not os.path.exists(video_path):
            return {"success": False, "error": "video_path does not exist"}

        if not languages or not isinstance(languages, list):
            return {"success": False, "error": "languages must be a non-empty list"}

        # ── 2. Rights gate ────────────────────────────────────────────────────
        rights = check_copyright(
            title=f"Dub Flip source: {video_path}",
            description="Multi-language dubbing of existing video",
        )
        if rights.get("risk_level") == "HIGH":
            return {
                "success": False,
                "error": f"Rights gate BLOCKED: {rights.get('reason', 'high copyright risk')}",
                "rights": rights,
            }
        logger.info(f"Rights gate: {rights.get('risk_level', 'LOW')}")

        # ── 3. Transcribe original ────────────────────────────────────────────
        trans = transcribe_video(video_path)
        if not trans.get("success"):
            return {"success": False, "error": "Transcription failed"}

        transcript_text = trans.get("text", "")

        # ── 4. Safety check on transcript ─────────────────────────────────────
        safety = check_safety(transcript_text)
        safety_status = get_safety_status(safety)
        if safety_status == "BLOCKED":
            return {
                "success": False,
                "error": f"Source content blocked by safety gate: risk={safety.get('overall_risk', 0)}",
                "safety": safety,
            }
        logger.info(f"Source safety: {safety_status} (risk={safety.get('overall_risk', 0):.3f})")

        # ── 5. Create versions for each language ──────────────────────────────
        results = []
        errors = []

        for lang in languages:
            try:
                # Translate
                script = {
                    "hook": trans["segments"][0]["text"] if trans.get("segments") else "Check this out!",
                    "body": transcript_text[:200],
                    "cta": "Follow for more!",
                    "duration": 60,
                }

                if lang != "en":
                    script = translate_script(script, lang)

                # TTS
                full_text = f"{script.get('hook', '')} {script.get('body', '')} {script.get('cta', '')}"
                audio_path = str(PROCESSED_DIR / f"dub_{lang}_{timestamp}.wav")
                text_to_speech(full_text, audio_path, rate=150)

                # Create video
                video_out = str(PROCESSED_DIR / f"dub_video_{lang}_{timestamp}.mp4")
                create_text_video(script, video_out)

                # Merge audio
                final_path = str(PROCESSED_DIR / f"dub_final_{lang}_{timestamp}.mp4")
                add_audio_track(video_out, audio_path, final_path, volume=0.8)

                # Safety gate on dubbed content
                lang_safety = check_safety(full_text)
                lang_status = get_safety_status(lang_safety)
                if lang_status == "BLOCKED":
                    logger.warning(f"Safety blocked for {lang}: risk={lang_safety.get('overall_risk', 0)}")
                    errors.append({"language": lang, "error": "safety_blocked"})
                    continue

                # Dedup check (source URL based)
                dup = check_duplicate(source_url=video_path)
                if dup.get("is_duplicate"):
                    logger.warning(f"Duplicate detected for {lang}: {dup.get('reason')}")
                    errors.append({"language": lang, "error": f"duplicate: {dup.get('reason')}"})
                    continue

                # QA check
                qa = run_qa(final_path)
                if qa["overall"] == "FAILED":
                    logger.warning(f"QA failed for {lang}: {qa['errors']}")
                    errors.append({"language": lang, "error": f"qa_failed: {qa['errors']}"})
                    continue

                # Analytics log
                video_id = log_video(
                    title=f"Dubbed ({lang})",
                    niche=niche,
                    agent_type="dub_flip",
                    video_path=final_path,
                    language=lang,
                )

                # Register content for dedup
                register_content(
                    video_path=final_path,
                    source_url=video_path,
                    agent_type="dub_flip",
                )

                results.append({
                    "language": lang,
                    "video_path": final_path,
                    "video_id": video_id,
                    "safety_status": lang_status,
                    "qa_status": qa["overall"],
                })

            except Exception as e:
                logger.error(f"Error creating {lang} version: {e}")
                errors.append({"language": lang, "error": str(e)})

        return {
            "success": len(results) > 0,
            "versions_created": len(results),
            "results": results,
            "errors": errors,
            "source_safety": safety_status,
        }

    except Exception as e:
        logger.error(f"Agent Dub Flip failed: {e}")
        return {"success": False, "error": str(e)}
