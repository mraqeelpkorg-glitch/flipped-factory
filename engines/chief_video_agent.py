"""
Chief Video Agent — Top-level production orchestrator for Flipped Factory.

The Chief owns the complete pipeline:
  SOURCE → VALIDATE → CAPTURE → ANALYZE → CLASSIFY → ROUTE → PRODUCE → QA → SAVE → INSTAGRAM

The Chief does NOT do the specialist's work itself.
Chief = ORCHESTRATOR + PRODUCTION OWNER.
Specialist = CONTENT TRANSFORMATION EXPERT.

Flow:
  1. Accept URL/file/source input
  2. Validate input
  3. Inspect the source (Playwright)
  4. Check rights/safety
  5. Capture/ingest source material
  6. Extract metadata/transcript
  7. Analyze content
  8. Auto-classify → select best agent
  9. Route to specialist agent
  10. Monitor specialist progress
  11. Receive final output
  12. Run final QA
  13. Correct/re-render if necessary
  14. Verify final video
  15. Save production artifact
  16. Queue for Instagram publishing
"""
import json
import logging
import time
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("chief_video_agent")

BASE_DIR = Path(__file__).parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
SOURCES_DIR = OUTPUTS_DIR / "sources"
TRANSCRIPTS_DIR = OUTPUTS_DIR / "transcripts"
CLIPS_DIR = OUTPUTS_DIR / "clips"
RENDERS_DIR = OUTPUTS_DIR / "renders"
FINAL_DIR = OUTPUTS_DIR / "final"
QA_DIR = OUTPUTS_DIR / "qa"
METADATA_DIR = OUTPUTS_DIR / "metadata"

for d in [OUTPUTS_DIR, SOURCES_DIR, TRANSCRIPTS_DIR, CLIPS_DIR, RENDERS_DIR, FINAL_DIR, QA_DIR, METADATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ─── Job States ───────────────────────────────────────────────────────────────

class JobState:
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    INSPECTING = "INSPECTING"
    CAPTURING = "CAPTURING"
    TRANSCRIBING = "TRANSCRIBING"
    ANALYZING = "ANALYZING"
    CLASSIFYING = "CLASSIFYING"
    ROUTING = "ROUTING"
    PRODUCING = "PRODUCING"
    RENDERING = "RENDERING"
    QA_PENDING = "QA_PENDING"
    QA_FAILED = "QA_FAILED"
    QA_PASSED = "QA_PASSED"
    CORRECTING = "CORRECTING"
    READY = "READY"
    APPROVED = "APPROVED"
    QUEUED = "QUEUED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"


# ─── Chief Video Agent ───────────────────────────────────────────────────────

class ChiefVideoAgent:
    """
    Top-level orchestrator for Flipped Factory.
    
    Usage:
        chief = ChiefVideoAgent()
        result = chief.process("https://www.youtube.com/watch?v=...")
    """
    
    MAX_QA_RETRIES = 3
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%H%m%S')
        self.job_id = ""
        self.state = JobState.RECEIVED
        self.artifacts = {}
        self.errors = []
        self.warnings = []
    
    def process(
        self,
        source: str,
        niche: str = "",
        language: str = "en",
        agent_override: str = "",
        auto_publish: bool = False,
        capture_duration: int = 30,
    ) -> dict:
        """
        Process a source through the complete Chief pipeline.
        
        Args:
            source: YouTube URL, local video path, blog URL, or text
            niche: Target niche (auto-detected if empty)
            language: Target language
            agent_override: Force a specific agent (skip classification)
            auto_publish: Auto-approve for publishing
            capture_duration: Seconds to capture from web sources
        
        Returns:
            {
                "success": bool,
                "job_id": str,
                "state": str,
                "agent_type": str,
                "video_path": str,
                "qa_result": dict,
                "publish_queued": bool,
                "errors": list,
                "warnings": list,
            }
        """
        self.job_id = f"chief_{self.timestamp}_{hash(source) % 10000:04d}"
        
        logger.info(f"╔══════════════════════════════════════════════════╗")
        logger.info(f"║  CHIEF VIDEO AGENT — Processing Source          ║")
        logger.info(f"║  Job: {self.job_id:<42} ║")
        logger.info(f"║  Source: {source[:40]:<40} ║")
        logger.info(f"╚══════════════════════════════════════════════════╝")
        
        try:
            # ── 1. VALIDATE INPUT ──────────────────────────────────────────
            self._set_state(JobState.VALIDATING)
            validation = self._validate_input(source)
            if not validation["valid"]:
                return self._fail(validation["error"])
            
            # ── 2. INSPECT SOURCE ──────────────────────────────────────────
            self._set_state(JobState.INSPECTING)
            inspection = self._inspect_source(source)
            if not inspection["success"]:
                return self._fail(inspection.get("error", "Inspection failed"))
            
            # ── 3. RIGHTS / SAFETY CHECK ───────────────────────────────────
            rights_check = self._check_rights(source, inspection)
            if rights_check.get("blocked"):
                self._set_state(JobState.BLOCKED)
                return self._fail(f"Rights/Safety blocked: {rights_check.get('reason')}")
            
            # ── 4. CAPTURE / INGEST SOURCE ─────────────────────────────────
            self._set_state(JobState.CAPTURING)
            ingestion = self._ingest_source(source, capture_duration)
            if not ingestion.get("success"):
                return self._fail(f"Ingestion failed: {ingestion.get('error')}")
            
            self.artifacts["source_video"] = ingestion.get("video_path", "")
            self.artifacts["source_metadata"] = ingestion.get("metadata", {})
            self.artifacts["source_frames"] = ingestion.get("frames_dir", "")
            self.artifacts["source_hash"] = ingestion.get("source_hash", "")
            
            # ── 5. TRANSCRIBE ──────────────────────────────────────────────
            self._set_state(JobState.TRANSCRIBING)
            transcript = self._transcribe(ingestion)
            self.artifacts["transcript"] = transcript
            
            # ── 6. ANALYZE CONTENT ─────────────────────────────────────────
            self._set_state(JobState.ANALYZING)
            analysis = self._analyze_content(ingestion, transcript)
            self.artifacts["analysis"] = analysis
            
            # Auto-detect niche if not provided
            if not niche and analysis.get("detected_niche"):
                niche = analysis["detected_niche"]
                logger.info(f"Auto-detected niche: {niche}")
            
            # ── 7. CLASSIFY → SELECT AGENT ─────────────────────────────────
            self._set_state(JobState.CLASSIFYING)
            
            if agent_override:
                agent_type = agent_override
                confidence = 1.0
                reason = f"Manual override: {agent_override}"
            else:
                classification = self._classify_source(source, analysis)
                agent_type = classification["agent_type"]
                confidence = classification["confidence"]
                reason = classification["reason"]
            
            if not agent_type:
                self._set_state(JobState.HUMAN_REVIEW_REQUIRED)
                return self._fail(f"Could not classify source: {reason}")
            
            logger.info(f"Selected agent: {agent_type} (confidence: {confidence:.0%})")
            logger.info(f"Reason: {reason}")
            
            self.artifacts["classification"] = {
                "agent_type": agent_type,
                "confidence": confidence,
                "reason": reason,
            }
            
            # ── 8. ROUTE TO SPECIALIST ─────────────────────────────────────
            self._set_state(JobState.ROUTING)
            production_result = self._route_to_specialist(
                agent_type=agent_type,
                source=source,
                ingestion=ingestion,
                transcript=transcript,
                analysis=analysis,
                niche=niche,
                language=language,
            )
            
            if not production_result.get("success"):
                return self._fail(f"Production failed: {production_result.get('error')}")
            
            # ── 9. QA CHECK ────────────────────────────────────────────────
            self._set_state(JobState.QA_PENDING)
            qa_result = self._run_qa_with_retry(production_result)
            
            if qa_result["overall"] == "FAILED":
                self._set_state(JobState.QA_FAILED)
                return self._fail(f"QA failed after {self.MAX_QA_RETRIES} attempts: {qa_result.get('errors')}")
            
            # ── 10. SAVE ARTIFACTS ─────────────────────────────────────────
            self._set_state(JobState.READY)
            final_path = self._save_artifacts(production_result, qa_result)
            
            # ── 11. QUEUE FOR INSTAGRAM ────────────────────────────────────
            publish_queued = False
            if auto_publish:
                publish_queued = self._queue_for_publishing(
                    final_path, production_result, agent_type
                )
            
            self._set_state(JobState.QUEUED if publish_queued else JobState.READY)
            
            # ── SAVE METADATA ──────────────────────────────────────────────
            self._save_metadata(final_path, qa_result, agent_type, niche)
            
            logger.info(f"╔══════════════════════════════════════════════════╗")
            logger.info(f"║  CHIEF — JOB COMPLETE                           ║")
            logger.info(f"║  Agent: {agent_type:<39} ║")
            logger.info(f"║  QA: {qa_result['overall']:<41} ║")
            logger.info(f"║  Video: {final_path[:40]:<40} ║")
            logger.info(f"╚══════════════════════════════════════════════════╝")
            
            return {
                "success": True,
                "job_id": self.job_id,
                "state": self.state,
                "agent_type": agent_type,
                "confidence": confidence,
                "video_path": final_path,
                "qa_result": {
                    "overall": qa_result["overall"],
                    "errors": qa_result.get("errors", []),
                    "warnings": qa_result.get("warnings", []),
                },
                "publish_queued": publish_queued,
                "artifacts": self.artifacts,
                "errors": self.errors,
                "warnings": self.warnings,
            }
        
        except Exception as e:
            logger.error(f"Chief pipeline error: {e}")
            return self._fail(str(e))
    
    # ─── Pipeline Stages ────────────────────────────────────────────────────
    
    def _validate_input(self, source: str) -> dict:
        """Validate input source."""
        if not source or not source.strip():
            return {"valid": False, "error": "Empty source"}
        
        source = source.strip()
        
        # URL validation
        if source.startswith("http"):
            if not any(x in source for x in [".com", ".org", ".net", ".io", ".co"]):
                return {"valid": False, "error": "Invalid URL format"}
            return {"valid": True, "type": "url"}
        
        # Local file validation
        if Path(source).exists():
            return {"valid": True, "type": "local_file"}
        
        # Text content
        if len(source) > 20:
            return {"valid": True, "type": "text_content"}
        
        return {"valid": False, "error": f"Unrecognized source: {source[:50]}"}
    
    def _inspect_source(self, source: str) -> dict:
        """Inspect source to understand what it is."""
        import re
        
        info = {
            "success": True,
            "source_type": "unknown",
            "platform": "unknown",
            "url": source if source.startswith("http") else "",
            "is_video": False,
            "is_audio": False,
            "is_text": False,
            "is_local": Path(source).exists() if source else False,
        }
        
        source_lower = source.lower()
        
        if "youtube.com" in source_lower or "youtu.be" in source_lower:
            info["source_type"] = "youtube"
            info["platform"] = "youtube"
            info["is_video"] = True
        elif "tiktok.com" in source_lower:
            info["source_type"] = "tiktok"
            info["platform"] = "tiktok"
            info["is_video"] = True
        elif "instagram.com" in source_lower:
            info["source_type"] = "instagram"
            info["platform"] = "instagram"
            info["is_video"] = True
        elif "spotify.com" in source_lower or "podcast" in source_lower:
            info["source_type"] = "podcast"
            info["platform"] = "spotify"
            info["is_audio"] = True
        elif any(x in source_lower for x in ["medium.com", "substack", ".blog"]):
            info["source_type"] = "blog"
            info["platform"] = "web"
            info["is_text"] = True
        elif info["is_local"]:
            ext = Path(source).suffix.lower()
            if ext in [".mp4", ".mov", ".avi", ".webm", ".mkv"]:
                info["source_type"] = "local_video"
                info["is_video"] = True
            elif ext in [".mp3", ".wav", ".m4a", ".ogg"]:
                info["source_type"] = "local_audio"
                info["is_audio"] = True
            elif ext in [".png", ".jpg", ".jpeg", ".gif"]:
                info["source_type"] = "local_image"
            else:
                info["source_type"] = "local_file"
        else:
            info["source_type"] = "text_content"
            info["is_text"] = True
        
        return info
    
    def _check_rights(self, source: str, inspection: dict) -> dict:
        """Check rights and safety for the source."""
        from engines.content_checker import check_copyright
        from engines.safety_gate import check_safety, get_safety_status
        
        # Rights check
        rights = check_copyright(
            title=f"Chief source: {source}",
            description=f"Source type: {inspection.get('source_type', 'unknown')}",
        )
        
        if rights.get("risk_level") == "HIGH":
            return {"blocked": True, "reason": f"High copyright risk: {rights.get('reason')}"}
        
        # Safety check on source text
        safety_text = source
        safety = check_safety(safety_text)
        status = get_safety_status(safety)
        
        if status == "BLOCKED":
            return {"blocked": True, "reason": f"Safety blocked: risk={safety.get('overall_risk', 0)}"}
        
        return {"blocked": False, "rights": rights, "safety": status}
    
    def _ingest_source(self, source: str, capture_duration: int) -> dict:
        """Ingest source using Playwright or local file handling."""
        from tools.source_ingestion import ingest_source
        
        return ingest_source(source, capture_duration=capture_duration)
    
    def _transcribe(self, ingestion: dict) -> dict:
        """Transcribe video/audio if possible."""
        video_path = ingestion.get("video_path", "")
        if not video_path or not Path(video_path).exists():
            return {"success": False, "text": "", "segments": []}
        
        try:
            from tools.transcriber import transcribe_video
            return transcribe_video(video_path)
        except Exception as e:
            logger.warning(f"Transcription failed: {e}")
            return {"success": False, "text": "", "segments": [], "error": str(e)}
    
    def _analyze_content(self, ingestion: dict, transcript: dict) -> dict:
        """Analyze content for topic, niche, language, hooks, etc."""
        metadata = ingestion.get("metadata", {})
        transcript_text = transcript.get("text", "")
        
        # Detect niche from title/content
        title = metadata.get("title", "").lower() if isinstance(metadata, dict) else ""
        content = (title + " " + transcript_text).lower()
        
        niche_signals = {
            "health_fitness": ["workout", "exercise", "fitness", "health", "gym", "yoga", "protein"],
            "finance_crypto": ["bitcoin", "investing", "money", "crypto", "stocks", "finance"],
            "tech_ai": ["ai", "artificial intelligence", "coding", "python", "technology", "chatgpt"],
            "ecommerce": ["dropshipping", "shopify", "amazon", "online store", "ecommerce"],
            "education": ["learn", "course", "tutorial", "education", "study"],
            "motivation": ["success", "mindset", "discipline", "motivation", "goals"],
            "food_nutrition": ["recipe", "food", "nutrition", "diet", "meal", "cooking"],
            "travel": ["travel", "trip", "destination", "backpacking", "hotel"],
            "beauty_skincare": ["skincare", "beauty", "makeup", "glow", "routine"],
            "productivity": ["productivity", "time management", "morning routine", "focus"],
        }
        
        detected_niche = ""
        max_score = 0
        for niche, keywords in niche_signals.items():
            score = sum(1 for kw in keywords if kw in content)
            if score > max_score:
                max_score = score
                detected_niche = niche
        
        # Detect language
        detected_language = transcript.get("language", "en")
        
        # Extract hooks from transcript
        hooks = []
        if transcript.get("segments"):
            for seg in transcript["segments"][:5]:
                text = seg.get("text", "").strip()
                if len(text) > 10 and len(text) < 200:
                    hooks.append(text)
        
        return {
            "title": metadata.get("title", "") if isinstance(metadata, dict) else "",
            "detected_niche": detected_niche,
            "detected_language": detected_language,
            "hooks": hooks,
            "transcript_length": len(transcript_text),
            "content_preview": transcript_text[:200] if transcript_text else "",
        }
    
    def _classify_source(self, source: str, analysis: dict) -> dict:
        """Classify source and select best agent."""
        from engines.content_classifier import classify_source
        
        metadata = {
            "title": analysis.get("title", ""),
            "niche": analysis.get("detected_niche", ""),
        }
        
        # Determine if source is a local file path or URL
        is_local = Path(source).exists() if source else False
        
        return classify_source(
            url="" if is_local else source,
            video_path=source if is_local else "",
            metadata=metadata,
        )
    
    def _route_to_specialist(
        self,
        agent_type: str,
        source: str,
        ingestion: dict,
        transcript: dict,
        analysis: dict,
        niche: str,
        language: str,
    ) -> dict:
        """Route to the selected specialist agent."""
        from engines.agent_runner import run_agent as _run
        
        # Build kwargs based on agent type
        kwargs = {
            "niche": niche,
        }
        
        # Map inputs based on agent type
        video_path = ingestion.get("video_path", "")
        
        if agent_type == "youtube_clipper":
            kwargs["youtube_url"] = source
            # Pass Playwright-captured video so agent skips yt-dlp download
            if video_path:
                kwargs["video_path"] = video_path
        elif agent_type == "podcast_clipper":
            kwargs["source"] = video_path or source
        elif agent_type == "blog_to_video":
            kwargs["blog_url_or_text"] = source
            kwargs["language"] = language
        elif agent_type == "remix_flip":
            kwargs["video_path"] = video_path
        elif agent_type == "dub_flip":
            kwargs["video_path"] = video_path
            kwargs["languages"] = language if isinstance(language, list) else [language]
        elif agent_type == "data_to_video":
            kwargs["niche"] = niche
        elif agent_type == "product_compilation":
            kwargs["niche"] = niche
        elif agent_type == "bts_educational":
            kwargs["bts_video_path"] = video_path
        elif agent_type == "trending_niche":
            kwargs["niche"] = niche
        elif agent_type == "course_teaser":
            kwargs["course_module"] = analysis.get("content_preview", "")
        elif agent_type == "live_highlights":
            kwargs["live_video_path"] = video_path
        elif agent_type == "screenshot_tutorial":
            kwargs["screenshots_dir"] = ingestion.get("source_frames", "")
        
        logger.info(f"Routing to {agent_type} with kwargs: {list(kwargs.keys())}")
        
        result = _run(agent_type, auto_publish=False, **kwargs)
        return result
    
    def _run_qa_with_retry(self, production_result: dict) -> dict:
        """Run QA with automatic correction retry."""
        from engines.shared_qa import run_qa
        
        video_path = production_result.get("video_path", "")
        if not video_path:
            return {"overall": "FAILED", "errors": ["No video path"], "warnings": []}
        
        last_qa = None
        for attempt in range(self.MAX_QA_RETRIES):
            logger.info(f"QA attempt {attempt + 1}/{self.MAX_QA_RETRIES}")
            
            qa = run_qa(video_path)
            last_qa = qa
            
            if qa["overall"] != "FAILED":
                return qa
            
            logger.warning(f"QA failed (attempt {attempt + 1}): {qa.get('errors')}")
            
            # Try correction if not last attempt
            if attempt < self.MAX_QA_RETRIES - 1:
                self._set_state(JobState.CORRECTING)
                logger.info("Attempting correction...")
                # The agent_runner already handles retries internally
                # For now, we just re-run QA
        
        return last_qa or {"overall": "FAILED", "errors": ["QA loop completed without result"], "warnings": []}
    
    def _save_artifacts(self, production_result: dict, qa_result: dict) -> str:
        """Save final artifacts to organized directory structure."""
        import shutil
        
        video_path = production_result.get("video_path", "")
        if not video_path or not Path(video_path).exists():
            return ""
        
        # Copy to final directory
        final_name = f"final_{self.job_id}.mp4"
        final_path = str(FINAL_DIR / final_name)
        
        shutil.copy2(video_path, final_path)
        logger.info(f"Saved final video: {final_path}")
        
        # Save QA report
        qa_report_path = str(QA_DIR / f"qa_{self.job_id}.json")
        with open(qa_report_path, "w") as f:
            json.dump(qa_result, f, indent=2, default=str)
        
        return final_path
    
    def _queue_for_publishing(self, video_path: str, production_result: dict, agent_type: str) -> bool:
        """Queue video for Instagram publishing."""
        try:
            from engines.scheduler import queue_for_publishing
            
            caption = production_result.get("caption", "")
            hashtags = production_result.get("hashtags", [])
            
            queue_for_publishing(
                video_path=video_path,
                caption=caption,
                hashtags=hashtags,
                agent_type=agent_type,
                job_id=self.job_id,
                auto_approve=False,
            )
            
            logger.info(f"Queued for publishing: {video_path}")
            return True
        except Exception as e:
            logger.error(f"Queue failed: {e}")
            return False
    
    def _save_metadata(self, final_path: str, qa_result: dict, agent_type: str, niche: str):
        """Save job metadata for analytics and learning."""
        metadata = {
            "job_id": self.job_id,
            "agent_type": agent_type,
            "niche": niche,
            "final_path": final_path,
            "qa_result": {
                "overall": qa_result["overall"],
                "instagram_compliance": qa_result.get("instagram_compliance", {}),
            },
            "artifacts": self.artifacts,
            "errors": self.errors,
            "warnings": self.warnings,
            "completed_at": datetime.now().isoformat(),
        }
        
        metadata_path = str(METADATA_DIR / f"job_{self.job_id}.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
    
    # ─── Helpers ────────────────────────────────────────────────────────────
    
    def _set_state(self, state: str):
        """Update job state."""
        self.state = state
        logger.info(f"State → {state}")
    
    def _fail(self, error: str) -> dict:
        """Return failure result."""
        self._set_state(JobState.FAILED)
        self.errors.append(error)
        logger.error(f"FAILED: {error}")
        
        return {
            "success": False,
            "job_id": self.job_id,
            "state": self.state,
            "error": error,
            "errors": self.errors,
            "warnings": self.warnings,
        }


# ══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def process_source(
    source: str,
    niche: str = "",
    language: str = "en",
    agent_override: str = "",
    auto_publish: bool = False,
    capture_duration: int = 30,
) -> dict:
    """
    One-call entry point for the Chief pipeline.
    
    Usage:
        result = process_source("https://www.youtube.com/watch?v=...")
        result = process_source("/path/to/video.mp4", agent_override="dub_flip")
    """
    chief = ChiefVideoAgent()
    return chief.process(
        source=source,
        niche=niche,
        language=language,
        agent_override=agent_override,
        auto_publish=auto_publish,
        capture_duration=capture_duration,
    )


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
╔══════════════════════════════════════════════════════╗
║  CHIEF VIDEO AGENT — Flipped Factory Orchestrator   ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  Usage:                                              ║
║    python chief_video_agent.py <source> [options]    ║
║                                                      ║
║  Examples:                                           ║
║    python chief_video_agent.py <youtube_url>         ║
║    python chief_video_agent.py <video.mp4>           ║
║    python chief_video_agent.py <url> --agent dub_flip║
║    python chief_video_agent.py <url> --niche tech    ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
        """)
        sys.exit(0)
    
    source = sys.argv[1]
    
    # Parse optional args
    kwargs = {}
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--agent" and i + 1 < len(args):
            kwargs["agent_override"] = args[i + 1]
            i += 2
        elif args[i] == "--niche" and i + 1 < len(args):
            kwargs["niche"] = args[i + 1]
            i += 2
        elif args[i] == "--language" and i + 1 < len(args):
            kwargs["language"] = args[i + 1]
            i += 2
        elif args[i] == "--auto-publish":
            kwargs["auto_publish"] = True
            i += 1
        elif args[i] == "--duration" and i + 1 < len(args):
            kwargs["capture_duration"] = int(args[i + 1])
            i += 2
        else:
            i += 1
    
    result = process_source(source, **kwargs)
    
    print(f"\n{'='*60}")
    print(f"CHIEF RESULT: {'SUCCESS' if result.get('success') else 'FAILED'}")
    print(f"{'='*60}")
    
    if result.get("success"):
        print(f"  Job ID:     {result.get('job_id')}")
        print(f"  Agent:      {result.get('agent_type')}")
        print(f"  Video:      {result.get('video_path')}")
        print(f"  QA:         {result.get('qa_result', {}).get('overall')}")
        print(f"  Published:  {result.get('publish_queued')}")
    else:
        print(f"  Error:      {result.get('error')}")
        print(f"  State:      {result.get('state')}")
    
    print(f"{'='*60}\n")
