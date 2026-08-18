"""
Instagram Uploader — Post Reels to Instagram.
Uses instagrapi (FREE, open-source).
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger("instagram_uploader")

SESSION_FILE = Path(__file__).parent.parent / "data" / "instagram_session.json"


def get_client():
    """Create authenticated Instagram client."""
    try:
        from instagrapi import Client
        
        client = Client()
        
        # Load session if exists
        if SESSION_FILE.exists():
            try:
                client.load_settings(SESSION_FILE)
                client.get_timeline_feed()  # Test if session valid
                logger.info("Instagram session loaded")
                return client
            except Exception:
                logger.info("Session expired, re-login needed")
        
        return client
    except ImportError:
        logger.warning("instagrapi not installed. Run: pip install instagrapi")
        return None


def login(username: str, password: str) -> bool:
    """Login and save session."""
    import os
    from datetime import datetime
    
    client = get_client()
    if client is None:
        return False
    
    # Check env vars or vault
    username = username or os.getenv("INSTAGRAM_USERNAME", "")
    password = password or os.getenv("INSTAGRAM_PASSWORD", "")
    
    if not username or not password:
        logger.error("Instagram credentials not set")
        return False
    
    try:
        client.login(username, password)
        client.dump_settings(SESSION_FILE)
        logger.info("Instagram login successful")
        return True
    except Exception as e:
        logger.error(f"Instagram login failed: {e}")
        return False


def post_reel(
    video_path: str,
    caption: str,
    hashtags: list = None,
) -> dict:
    """
    Post a video as Instagram Reel.
    
    Returns {success, post_id, post_url}
    """
    client = get_client()
    if client is None:
        return {"success": False, "error": "Instagram client not available"}
    
    # Format caption with hashtags
    if hashtags:
        hashtag_str = " ".join([f"#{t.lstrip('#')}" for t in hashtags])
        full_caption = f"{caption}\n\n{hashtag_str}"
    else:
        full_caption = caption
    
    try:
        # Upload as reel
        media = client.clip_upload(
            video_path,
            caption=full_caption,
        )
        
        post_id = str(media.id)
        post_url = f"https://www.instagram.com/reel/{media.code}/"
        
        logger.info(f"Reel posted: {post_url}")
        return {
            "success": True,
            "post_id": post_id,
            "post_url": post_url,
            "code": media.code,
        }
    except Exception as e:
        logger.error(f"Reel upload failed: {e}")
        return {"success": False, "error": str(e)}


def post_image(image_path: str, caption: str, hashtags: list = None) -> dict:
    """Post an image to Instagram."""
    client = get_client()
    if client is None:
        return {"success": False, "error": "Instagram client not available"}
    
    if hashtags:
        hashtag_str = " ".join([f"#{t.lstrip('#')}" for t in hashtags])
        full_caption = f"{caption}\n\n{hashtag_str}"
    else:
        full_caption = caption
    
    try:
        media = client.photo_upload(image_path, caption=full_caption)
        post_url = f"https://www.instagram.com/p/{media.code}/"
        return {"success": True, "post_id": str(media.id), "post_url": post_url}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_account_info() -> dict:
    """Get account stats."""
    client = get_client()
    if client is None:
        return {"error": "Client not available"}
    
    try:
        user = client.account_info()
        return {
            "username": user.username,
            "full_name": user.full_name,
            "followers": user.follower_count,
            "following": user.following_count,
            "posts": user.media_count,
            "is_private": user.is_private,
        }
    except Exception as e:
        return {"error": str(e)}


def post_with_retry(video_path: str, caption: str, hashtags: list = None, max_retries: int = 3) -> dict:
    """Post with retry logic."""
    for attempt in range(max_retries):
        result = post_reel(video_path, caption, hashtags)
        if result["success"]:
            return result
        
        logger.warning(f"Post attempt {attempt + 1} failed: {result.get('error')}")
        if attempt < max_retries - 1:
            import time
            time.sleep(30)  # Wait 30 seconds before retry
    
    return result
