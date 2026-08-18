"""
Instagram Graph API Analytics — Real performance data from Instagram.

Connects to Instagram Graph API to fetch:
- Post insights (views, likes, comments, shares, saves)
- Account insights (followers, reach, impressions)
- Story insights
- Reel insights (plays, accounts reached, interactions)

Requires: Facebook App + Instagram Business Account + Access Token
Free tier: Instagram Graph API is FREE (no paid API needed)
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("instagram_analytics")

# ─── Configuration ────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent / "data"
ANALYTICS_DIR = DATA_DIR / "analytics"
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

# Instagram Graph API endpoints
BASE_URL = "https://graph.facebook.com/v19.0"

# Required permissions:
# instagram_basic, instagram_manage_insights, pages_show_list, pages_read_engagement
# These are FREE — no paid API needed


class InstagramAnalytics:
    """
    Instagram Graph API analytics client.
    
    Usage:
        analytics = InstagramAnalytics(access_token="...", instagram_account_id="...")
        insights = analytics.get_reel_insights(media_id="...")
        account = analytics.get_account_insights()
    """
    
    def __init__(self, access_token: str = None, instagram_account_id: str = None):
        self.access_token = access_token
        self.instagram_account_id = instagram_account_id
        self._load_config()
    
    def _load_config(self):
        """Load config from env or config file."""
        import os
        if not self.access_token:
            self.access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
        if not self.instagram_account_id:
            self.instagram_account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")
        
        # Also check vault
        vault_file = DATA_DIR / "vault.json"
        if vault_file.exists():
            vault = json.loads(vault_file.read_text())
            if not self.access_token:
                self.access_token = vault.get("instagram_access_token", "")
            if not self.instagram_account_id:
                self.instagram_account_id = vault.get("instagram_account_id", "")
    
    def is_configured(self) -> bool:
        """Check if API credentials are available."""
        return bool(self.access_token and self.instagram_account_id)
    
    def _api_get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request to Instagram Graph API."""
        import urllib.request
        import urllib.parse
        
        if not params:
            params = {}
        params["access_token"] = self.access_token
        
        url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
        
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"Instagram API error: {e}")
            return {"error": str(e)}
    
    def _api_post(self, endpoint: str, data: dict) -> dict:
        """Make POST request to Instagram Graph API."""
        import urllib.request
        import urllib.parse
        
        data["access_token"] = self.access_token
        url = f"{BASE_URL}/{endpoint}"
        
        try:
            encoded = urllib.parse.urlencode(data).encode()
            req = urllib.request.Request(url, data=encoded, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"Instagram API POST error: {e}")
            return {"error": str(e)}
    
    # ─── Reel Insights ────────────────────────────────────────────────────────
    
    def get_reel_insights(self, media_id: str) -> dict:
        """
        Get insights for a specific Reel.
        
        Returns:
            {
                "media_id": str,
                "plays": int,
                "accounts_reached": int,
                "likes": int,
                "comments": int,
                "shares": int,
                "saves": int,
                "total_interactions": int,
                "ig_reels_avg_watch_time": float,
                "ig_reels_video_view_total_time": float,
                "fetched_at": str
            }
        """
        if not self.is_configured():
            return {"error": "Instagram API not configured", "configured": False}
        
        # Get media insights
        insights = self._api_get(f"{media_id}/insights", {
            "metric": ",".join([
                "plays",
                "accounts_reached",
                "likes",
                "comments",
                "shares",
                "saves",
                "total_interactions",
                "ig_reels_avg_watch_time",
                "ig_reels_video_view_total_time",
            ])
        })
        
        if "error" in insights:
            return {"error": insights["error"], "media_id": media_id}
        
        # Parse insights into flat dict
        result = {"media_id": media_id, "fetched_at": datetime.now().isoformat()}
        
        if "data" in insights:
            for item in insights["data"]:
                name = item.get("name", "")
                values = item.get("values", [])
                if values:
                    result[name] = values[0].get("value", 0)
        
        # Calculate derived metrics
        plays = result.get("plays", 0)
        watch_time = result.get("ig_reels_video_view_total_time", 0)
        if plays > 0:
            result["avg_watch_time_per_play"] = watch_time / plays
        else:
            result["avg_watch_time_per_play"] = 0
        
        # Save to file
        self._save_reel_analytics(media_id, result)
        
        logger.info(f"Reel insights fetched: plays={plays}, reached={result.get('accounts_reached', 0)}")
        return result
    
    def get_reel_media_id(self, shortcode: str) -> Optional[str]:
        """Get media ID from shortcode."""
        if not self.is_configured():
            return None
        
        result = self._api_get(f"ig_media_shortcode/{shortcode}", {
            "fields": "id"
        })
        return result.get("id")
    
    # ─── Account Insights ─────────────────────────────────────────────────────
    
    def get_account_insights(self, period: str = "day", since: str = None, until: str = None) -> dict:
        """
        Get account-level insights.
        
        Args:
            period: "day" or "lifetime"
            since: ISO date string (e.g., "2026-08-01")
            until: ISO date string (e.g., "2026-08-18")
        
        Returns:
            {
                "followers_count": int,
                "follows_count": int,
                "media_count": int,
                "reach": int,
                "impressions": int,
                "profile_views": int,
                "website_clicks": int,
                "follower_count": int,
                "fetched_at": str
            }
        """
        if not self.is_configured():
            return {"error": "Instagram API not configured", "configured": False}
        
        # Get account info
        account = self._api_get(self.instagram_account_id, {
            "fields": "followers_count,follows_count,media_count,name,username"
        })
        
        if "error" in account:
            return {"error": account["error"]}
        
        # Get account insights
        params = {
            "metric": ",".join([
                "impressions",
                "reach",
                "profile_views",
                "website_clicks",
                "follower_count",
            ]),
            "period": period,
        }
        
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        insights = self._api_get(f"{self.instagram_account_id}/insights", params)
        
        result = {
            "followers_count": account.get("followers_count", 0),
            "follows_count": account.get("follows_count", 0),
            "media_count": account.get("media_count", 0),
            "username": account.get("username", ""),
            "fetched_at": datetime.now().isoformat(),
        }
        
        if "data" in insights:
            for item in insights["data"]:
                name = item.get("name", "")
                values = item.get("values", [])
                if values:
                    result[name] = values[0].get("value", 0)
        
        # Save
        self._save_account_analytics(result)
        
        logger.info(f"Account insights: followers={result.get('followers_count', 0)}")
        return result
    
    # ─── Recent Media ─────────────────────────────────────────────────────────
    
    def get_recent_media(self, limit: int = 25) -> list:
        """Get recent media with insights."""
        if not self.is_configured():
            return []
        
        result = self._api_get(f"{self.instagram_account_id}/media", {
            "fields": "id,caption,media_type,media_url,timestamp,like_count,comments_count,permalink",
            "limit": limit,
        })
        
        if "error" in result or "data" not in result:
            return []
        
        media_list = result["data"]
        
        # Get insights for each Reel
        for media in media_list:
            if media.get("media_type") == "REELS":
                insights = self.get_reel_insights(media["id"])
                media["insights"] = insights
        
        return media_list
    
    # ─── Bulk Fetch All Reels ─────────────────────────────────────────────────
    
    def fetch_all_reel_analytics(self, days: int = 30) -> dict:
        """
        Fetch analytics for ALL reels in the last N days.
        
        Returns:
            {
                "total_reels": int,
                "total_plays": int,
                "total_reach": int,
                "total_interactions": int,
                "avg_watch_time": float,
                "top_performing": [...],
                "reels": [...]
            }
        """
        if not self.is_configured():
            return {"error": "Instagram API not configured"}
        
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        media_list = self.get_recent_media(limit=100)
        
        reels = []
        total_plays = 0
        total_reach = 0
        total_interactions = 0
        
        for media in media_list:
            if media.get("media_type") == "REELS":
                insights = media.get("insights", {})
                plays = insights.get("plays", 0)
                reached = insights.get("accounts_reached", 0)
                interactions = insights.get("total_interactions", 0)
                
                total_plays += plays
                total_reach += reached
                total_interactions += interactions
                
                reels.append({
                    "media_id": media.get("id"),
                    "caption": (media.get("caption", "") or "")[:100],
                    "timestamp": media.get("timestamp"),
                    "likes": media.get("like_count", 0),
                    "comments": media.get("comments_count", 0),
                    "plays": plays,
                    "reach": reached,
                    "interactions": interactions,
                    "permalink": media.get("permalink", ""),
                })
        
        # Sort by plays (best performing first)
        reels.sort(key=lambda x: x.get("plays", 0), reverse=True)
        
        result = {
            "total_reels": len(reels),
            "total_plays": total_plays,
            "total_reach": total_reach,
            "total_interactions": total_interactions,
            "avg_watch_time": 0,
            "top_performing": reels[:10],
            "reels": reels,
            "fetched_at": datetime.now().isoformat(),
        }
        
        # Save bulk analytics
        self._save_bulk_analytics(result)
        
        logger.info(f"Fetched analytics for {len(reels)} reels: {total_plays} total plays")
        return result
    
    # ─── Storage ──────────────────────────────────────────────────────────────
    
    def _save_reel_analytics(self, media_id: str, data: dict):
        """Save reel analytics to file."""
        filepath = ANALYTICS_DIR / f"reel_{media_id}.json"
        filepath.write_text(json.dumps(data, indent=2))
    
    def _save_account_analytics(self, data: dict):
        """Save account analytics to file."""
        filepath = ANALYTICS_DIR / f"account_{datetime.now().strftime('%Y%m%d')}.json"
        filepath.write_text(json.dumps(data, indent=2))
    
    def _save_bulk_analytics(self, data: dict):
        """Save bulk analytics."""
        filepath = ANALYTICS_DIR / "bulk_analytics.json"
        filepath.write_text(json.dumps(data, indent=2))
    
    def get_local_analytics(self) -> dict:
        """Load the most recent bulk analytics from disk."""
        filepath = ANALYTICS_DIR / "bulk_analytics.json"
        if filepath.exists():
            return json.loads(filepath.read_text())
        return {}


# ─── Convenience Functions ────────────────────────────────────────────────────

def get_analytics() -> InstagramAnalytics:
    """Get configured analytics instance."""
    return InstagramAnalytics()

def fetch_reel_stats(media_id: str) -> dict:
    """Quick fetch for a single reel."""
    a = get_analytics()
    return a.get_reel_insights(media_id)

def fetch_account_stats() -> dict:
    """Quick fetch for account stats."""
    a = get_analytics()
    return a.get_account_insights()

def fetch_all_reels(days: int = 30) -> dict:
    """Quick fetch for all reels."""
    a = get_analytics()
    return a.fetch_all_reel_analytics(days)
