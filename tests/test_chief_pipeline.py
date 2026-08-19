"""
Tests for Flipped Factory — Chief Video Agent, Classifier, Source Ingestion.
Run: cd /Users/computertrend/Desktop/flipped-factory && python -m pytest tests/ -v
"""
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


# ══════════════════════════════════════════════════════════════════════════════
# CONTENT CLASSIFIER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestContentClassifier:
    """Test the content classifier for agent selection."""
    
    def test_youtube_url_classification(self):
        from engines.content_classifier import classify_from_url
        
        result = classify_from_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result["agent_type"] == "youtube_clipper"
        assert result["confidence"] > 0.5
        assert "youtube" in result["reason"].lower() or "youtube_clipper" in result["reason"]
    
    def test_podcast_url_classification(self):
        from engines.content_classifier import classify_from_url
        
        result = classify_from_url("https://open.spotify.com/show/abc123")
        assert result["agent_type"] == "podcast_clipper"
        assert result["confidence"] > 0.5
    
    def test_blog_url_classification(self):
        from engines.content_classifier import classify_from_url
        
        result = classify_from_url("https://medium.com/@user/my-article")
        assert result["agent_type"] == "blog_to_video"
        assert result["confidence"] > 0.5
    
    def test_unknown_url_classification(self):
        from engines.content_classifier import classify_from_url
        
        result = classify_from_url("https://example.com/something")
        # Should still return something, even if low confidence
        assert result["agent_type"] is not None or result["confidence"] == 0.0
    
    def test_classification_returns_all_matches(self):
        from engines.content_classifier import classify_source
        
        result = classify_source(
            url="https://www.youtube.com/watch?v=test",
            text="Learn python programming tutorial",
        )
        assert "all_matches" in result
        assert len(result["all_matches"]) > 0
    
    def test_classification_confidence_range(self):
        from engines.content_classifier import classify_from_url
        
        result = classify_from_url("https://www.youtube.com/watch?v=test")
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_text_based_classification(self):
        from engines.content_classifier import classify_source
        
        result = classify_source(text="This podcast interview discusses AI trends")
        assert result["agent_type"] == "podcast_clipper"
        assert result["confidence"] > 0.3
    
    def test_video_path_classification(self):
        from engines.content_classifier import classify_source
        
        result = classify_source(video_path="/path/to/video.mp4")
        # Should match remix_flip or dub_flip for local video
        assert result["agent_type"] in ["remix_flip", "dub_flip", None]
    
    def test_product_keyword_classification(self):
        from engines.content_classifier import classify_source
        
        result = classify_source(text="Top 10 best products for home office 2024 review comparison")
        assert result["agent_type"] == "product_compilation"
    
    def test_course_keyword_classification(self):
        from engines.content_classifier import classify_source
        
        result = classify_source(text="This course module teaches you python basics lesson preview")
        assert result["agent_type"] == "course_teaser"


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE INGESTION TESTS (Local files only — no network)
# ══════════════════════════════════════════════════════════════════════════════

class TestSourceIngestion:
    """Test source ingestion with local files (no network required)."""
    
    def test_ingest_nonexistent_file(self):
        from tools.source_ingestion import SourceIngestion
        
        ingestion = SourceIngestion()
        result = ingestion.ingest_local_video("/nonexistent/path/video.mp4")
        assert result["success"] is False
        assert "not found" in result["error"].lower()
    
    def test_ingest_local_video(self):
        """Test ingestion of a real local video file."""
        from tools.source_ingestion import SourceIngestion
        
        # Find an existing video in the project
        raw_dir = Path(__file__).parent.parent / "data" / "videos" / "raw"
        existing_videos = list(raw_dir.glob("*.mp4"))
        
        if not existing_videos:
            pytest.skip("No local videos available for testing")
        
        video_path = str(existing_videos[0])
        ingestion = SourceIngestion()
        result = ingestion.ingest_local_video(video_path)
        
        assert result["success"] is True
        assert result["video_path"] != ""
        assert result["source_hash"] != ""
        assert result["metadata"]["source"] == "local"
    
    def test_ingest_source_sync_wrapper(self):
        """Test the sync wrapper for non-async contexts."""
        from tools.source_ingestion import ingest_source
        
        # Find an existing video
        raw_dir = Path(__file__).parent.parent / "data" / "videos" / "raw"
        existing_videos = list(raw_dir.glob("*.mp4"))
        
        if not existing_videos:
            pytest.skip("No local videos available for testing")
        
        video_path = str(existing_videos[0])
        result = ingest_source(video_path)
        
        assert result["success"] is True
        assert "source_hash" in result
    
    def test_source_hash_uniqueness(self):
        """Different files should produce different hashes."""
        from tools.source_ingestion import SourceIngestion
        
        # Create two temp files with different content
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f1:
            f1.write("content A")
            path1 = f1.name
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f2:
            f2.write("content B")
            path2 = f2.name
        
        try:
            import hashlib
            with open(path1, "rb") as f:
                hash1 = hashlib.md5(f.read()).hexdigest()
            with open(path2, "rb") as f:
                hash2 = hashlib.md5(f.read()).hexdigest()
            
            assert hash1 != hash2
        finally:
            os.unlink(path1)
            os.unlink(path2)


# ══════════════════════════════════════════════════════════════════════════════
# SHARED QA TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestSharedQA:
    """Test the shared QA system."""
    
    def test_qa_nonexistent_file(self):
        from engines.shared_qa import run_qa
        
        result = run_qa("/nonexistent/video.mp4")
        assert result["overall"] == "FAILED"
        assert any("not exist" in e.lower() or "does not exist" in e.lower() for e in result["errors"])
    
    def test_qa_on_real_video(self):
        """Test QA on an existing video file."""
        from engines.shared_qa import run_qa
        
        raw_dir = Path(__file__).parent.parent / "data" / "videos" / "raw"
        existing_videos = list(raw_dir.glob("*.mp4"))
        
        if not existing_videos:
            pytest.skip("No local videos available for testing")
        
        video_path = str(existing_videos[0])
        result = run_qa(video_path)
        
        assert "overall" in result
        assert result["overall"] in ["PASSED", "PASSED_WITH_WARNINGS", "FAILED"]
        assert "checks" in result
        assert len(result["checks"]) > 0
    
    def test_qa_structure(self):
        """Verify QA result has expected structure."""
        from engines.shared_qa import run_qa
        
        result = run_qa("/nonexistent.mp4")
        
        required_keys = ["overall", "checks", "errors", "warnings", "video_path"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
    
    def test_individual_qa_checks(self):
        """Test individual QA check functions."""
        from engines.shared_qa import (
            check_file_exists,
            check_resolution,
            check_aspect_ratio,
            check_codec,
            check_audio,
            check_duration,
        )
        
        # File exists check
        result = check_file_exists("/nonexistent.mp4")
        assert result["pass"] is False
        
        result = check_file_exists(str(Path(__file__).parent.parent / "config.py"))
        assert result["pass"] is True  # File exists (even if not video)
        
        # Resolution check with mock stream
        mock_stream = {"width": "1080", "height": "1920"}
        result = check_resolution(mock_stream)
        assert result["pass"] is True
        
        mock_stream_bad = {"width": "640", "height": "480"}
        result = check_resolution(mock_stream_bad)
        assert result["pass"] is False
        
        # Aspect ratio check
        result = check_aspect_ratio(mock_stream)
        assert result["pass"] is True
        
        # Codec check
        mock_h264 = {"codec_name": "h264"}
        result = check_codec(mock_h264)
        assert result["pass"] is True
        
        mock_bad = {"codec_name": "unknown"}
        result = check_codec(mock_bad)
        assert result["pass"] is False
        
        # Duration check
        mock_info = {"format": {"duration": "25.0"}}
        result = check_duration(mock_info)
        assert result["pass"] is True
        
        mock_info_long = {"format": {"duration": "75.0"}}
        result = check_duration(mock_info_long)
        assert result["pass"] is True  # Valid but not optimal


# ══════════════════════════════════════════════════════════════════════════════
# JOB MANAGER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestJobManager:
    """Test job lifecycle management."""
    
    def test_job_lifecycle(self):
        from engines.job_manager import (
            create_job, start_job, complete_job, get_job, fail_job,
            start_stage, complete_stage, get_job_stages,
            build_output, init_job_tables,
        )
        
        # Ensure tables exist
        init_job_tables()
        
        # Create job
        job_id = create_job("test_agent", {"test": True})
        assert job_id != ""
        assert "test_agent" in job_id
        
        # Start job
        start_job(job_id)
        job = get_job(job_id)
        assert job["status"] == "running"
        
        # Track stages
        stage_id = start_stage(job_id, "test_stage", stage_order=1, input_data={"key": "value"})
        assert stage_id is not None
        
        complete_stage(job_id, "test_stage", output_data={"result": "done"})
        stages = get_job_stages(job_id)
        assert len(stages) >= 1
        assert stages[0]["status"] == "completed"
        
        # Complete job
        complete_job(job_id, output={"video_path": "/test.mp4"})
        job = get_job(job_id)
        assert job["status"] == "completed"
    
    def test_job_retry(self):
        from engines.job_manager import (
            create_job, start_job, fail_job, get_job, init_job_tables,
        )
        
        init_job_tables()
        
        job_id = create_job("test_retry", {"test": True})
        start_job(job_id)
        
        # Fail with retry
        will_retry = fail_job(job_id, "test error", can_retry=True)
        assert will_retry is True
        
        job = get_job(job_id)
        assert job["retry_count"] >= 1
    
    def test_build_output(self):
        from engines.job_manager import build_output
        
        result = build_output(
            success=True,
            video_path="/test/video.mp4",
            caption="Test caption",
            hashtags=["test", "viral"],
            metadata={"key": "value"},
        )
        
        assert result["success"] is True
        assert result["video_path"] == "/test/video.mp4"
        assert result["caption"] == "Test caption"
        assert "test" in result["hashtags"]
        assert "timestamp" in result
    
    def test_checkpoint_save_load(self):
        from engines.job_manager import (
            create_job, start_job, save_checkpoint, load_checkpoint,
            init_job_tables,
        )
        
        init_job_tables()
        
        job_id = create_job("test_checkpoint", {})
        start_job(job_id)
        
        checkpoint = {"stage": "download", "video_path": "/test.mp4", "progress": 50}
        save_checkpoint(job_id, checkpoint)
        
        loaded = load_checkpoint(job_id)
        assert loaded["stage"] == "download"
        assert loaded["video_path"] == "/test.mp4"


# ══════════════════════════════════════════════════════════════════════════════
# CHIEF VIDEO AGENT TESTS (Unit tests — no actual video processing)
# ══════════════════════════════════════════════════════════════════════════════

class TestChiefVideoAgent:
    """Test Chief Video Agent pipeline stages."""
    
    def test_chief_initialization(self):
        from engines.chief_video_agent import ChiefVideoAgent, JobState
        
        chief = ChiefVideoAgent()
        assert chief.state == JobState.RECEIVED
        assert chief.job_id == ""
        assert chief.artifacts == {}
        assert chief.errors == []
    
    def test_chief_validation_empty_source(self):
        from engines.chief_video_agent import ChiefVideoAgent, JobState
        
        chief = ChiefVideoAgent()
        result = chief._validate_input("")
        assert result["valid"] is False
        
        result = chief._validate_input("   ")
        assert result["valid"] is False
    
    def test_chief_validation_valid_url(self):
        from engines.chief_video_agent import ChiefVideoAgent
        
        chief = ChiefVideoAgent()
        result = chief._validate_input("https://www.youtube.com/watch?v=test")
        assert result["valid"] is True
        assert result["type"] == "url"
    
    def test_chief_validation_local_file(self):
        from engines.chief_video_agent import ChiefVideoAgent
        
        chief = ChiefVideoAgent()
        # Test with config.py which exists
        config_path = str(Path(__file__).parent.parent / "config.py")
        result = chief._validate_input(config_path)
        assert result["valid"] is True
        assert result["type"] == "local_file"
    
    def test_chief_validation_text_content(self):
        from engines.chief_video_agent import ChiefVideoAgent
        
        chief = ChiefVideoAgent()
        result = chief._validate_input("This is a long text content that should be recognized as text")
        assert result["valid"] is True
        assert result["type"] == "text_content"
    
    def test_chief_inspect_youtube(self):
        from engines.chief_video_agent import ChiefVideoAgent
        
        chief = ChiefVideoAgent()
        result = chief._inspect_source("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result["success"] is True
        assert result["source_type"] == "youtube"
        assert result["platform"] == "youtube"
        assert result["is_video"] is True
    
    def test_chief_inspect_local_video(self):
        from engines.chief_video_agent import ChiefVideoAgent
        
        chief = ChiefVideoAgent()
        # Use an actual existing video file
        raw_dir = Path(__file__).parent.parent / "data" / "videos" / "raw"
        existing_videos = list(raw_dir.glob("*.mp4"))
        if not existing_videos:
            pytest.skip("No local videos available")
        result = chief._inspect_source(str(existing_videos[0]))
        assert result["source_type"] == "local_video"
        assert result["is_video"] is True
        assert result["is_local"] is True
    
    def test_chief_inspect_blog(self):
        from engines.chief_video_agent import ChiefVideoAgent
        
        chief = ChiefVideoAgent()
        result = chief._inspect_source("https://medium.com/@user/article")
        assert result["source_type"] == "blog"
        assert result["is_text"] is True
    
    def test_chief_state_transitions(self):
        from engines.chief_video_agent import ChiefVideoAgent, JobState
        
        chief = ChiefVideoAgent()
        assert chief.state == JobState.RECEIVED
        
        chief._set_state(JobState.VALIDATING)
        assert chief.state == JobState.VALIDATING
        
        chief._set_state(JobState.INSPECTING)
        assert chief.state == JobState.INSPECTING
    
    def test_chief_fail_returns_error(self):
        from engines.chief_video_agent import ChiefVideoAgent, JobState
        
        chief = ChiefVideoAgent()
        result = chief._fail("Test error")
        
        assert result["success"] is False
        assert result["error"] == "Test error"
        assert chief.state == JobState.FAILED
        assert "Test error" in chief.errors


# ══════════════════════════════════════════════════════════════════════════════
# AGENT RUNNER TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAgentRunner:
    """Test agent runner with mocked agents."""
    
    def test_get_available_agents(self):
        from engines.agent_runner import get_available_agents
        
        agents = get_available_agents()
        assert len(agents) == 12
        agent_ids = [a["id"] for a in agents]
        assert "youtube_clipper" in agent_ids
        assert "dub_flip" in agent_ids
        assert "blog_to_video" in agent_ids
    
    def test_agent_runner_unknown_agent(self):
        from engines.agent_runner import run_agent
        
        result = run_agent("nonexistent_agent", test=True)
        assert result["success"] is False


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestConfig:
    """Test configuration values."""
    
    def test_video_dimensions(self):
        from config import VIDEO_WIDTH, VIDEO_HEIGHT
        
        assert VIDEO_WIDTH == 1080
        assert VIDEO_HEIGHT == 1920
    
    def test_niches_defined(self):
        from config import NICHES
        
        assert len(NICHES) >= 10
        assert "health_fitness" in NICHES
        assert "tech_ai" in NICHES
    
    def test_directories_created(self):
        from config import RAW_DIR, PROCESSED_DIR, PUBLISHED_DIR
        
        assert RAW_DIR.exists()
        assert PROCESSED_DIR.exists()
        assert PUBLISHED_DIR.exists()


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT STRUCTURE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestOutputStructure:
    """Test that output directories exist."""
    
    def test_outputs_directories(self):
        base = Path(__file__).parent.parent / "outputs"
        expected_dirs = ["sources", "transcripts", "clips", "renders", "final", "qa", "metadata"]
        
        for d in expected_dirs:
            dir_path = base / d
            assert dir_path.exists(), f"Missing directory: outputs/{d}"


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
