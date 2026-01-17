# app/services/youtube_video_service.py

import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class YouTubeVideoService:
    def __init__(self):
        self.youtube = build(
            "youtube",
            "v3",
            developerKey=settings.YOUTUBE_API_KEY,
            cache_discovery=False
        )

    def extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL with strict validation
        
        Supports:
        - https://www.youtube.com/watch?v=dQw4w9WgXcQ
        - https://youtu.be/dQw4w9WgXcQ
        - https://youtube.com/watch?v=dQw4w9WgXcQ
        """
        # Validate URL has proper protocol
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        
        # Validate URL length
        if len(url) > 2048:
            raise ValueError("URL is too long")
        
        try:
            parsed = urlparse(url)
            
            # Validate domain
            domain = parsed.netloc.lower()
            if domain not in ("youtube.com", "www.youtube.com", "youtu.be", "www.youtu.be"):
                raise ValueError(f"URL must be from YouTube domain, got: {domain}")
            
            video_id = None
            
            # Handle youtu.be short links
            if domain in ("youtu.be", "www.youtu.be"):
                video_id = parsed.path.lstrip("/").split("?")[0]  # Remove query params
            # Handle youtube.com full links
            else:
                query_params = parse_qs(parsed.query)
                video_id = query_params.get("v", [None])[0]
            
            # Validate video ID format
            if not video_id:
                raise ValueError("No video ID found in URL")
            
            if len(video_id) != 11:
                raise ValueError(f"Invalid video ID length: {len(video_id)} (expected 11)")
            
            # Validate character set (YouTube video IDs contain only alphanumeric, - and _)
            if not re.match(r"^[a-zA-Z0-9_-]{11}$", video_id):
                raise ValueError(f"Invalid video ID format: {video_id}")
            
            logger.info(f"Successfully extracted video ID: {video_id}")
            return video_id
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error parsing YouTube URL: {str(e)}")
            raise ValueError(f"Invalid YouTube URL: {str(e)}")

    def fetch_video_detail(self, url: str) -> dict:
        """
        Fetch video metadata from YouTube API with error handling
        """
        try:
            video_id = self.extract_video_id(url)
            
            response = self.youtube.videos().list(
                part="snippet,statistics",
                id=video_id,
                maxResults=1
            ).execute()

            if not response.get("items"):
                logger.warning(f"Video not found: {video_id}")
                raise ValueError(f"Video tidak ditemukan (ID: {video_id})")

            item = response["items"][0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})

            # Parse ISO 8601 datetime string to datetime object
            published_at_str = snippet.get("publishedAt")
            if not published_at_str:
                logger.warning(f"Missing publishedAt for video: {video_id}")
                published_at = datetime.utcnow()
            else:
                try:
                    published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Invalid publishedAt format: {published_at_str}")
                    published_at = datetime.utcnow()

            # Get thumbnail (prefer high, then medium, then default)
            thumbnails = snippet.get("thumbnails", {})
            thumb_url = None
            for quality in ["high", "medium", "default"]:
                if quality in thumbnails:
                    thumb_url = thumbnails[quality].get("url")
                    if thumb_url:
                        break

            # Safely parse statistics (may be strings or missing)
            try:
                view_count = int(stats.get("viewCount", 0))
            except (ValueError, TypeError):
                view_count = 0
            
            try:
                like_count = int(stats.get("likeCount", 0))
            except (ValueError, TypeError):
                like_count = 0
            
            try:
                comment_count = int(stats.get("commentCount", 0))
            except (ValueError, TypeError):
                comment_count = 0

            result = {
                "youtube_video_id": video_id,
                "title": snippet.get("title", "Unknown Title"),
                "channel_name": snippet.get("channelTitle", "Unknown Channel"),
                "published_at": published_at,
                "thumbnail_url": thumb_url,
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": comment_count,
            }
            
            logger.info(f"Successfully fetched metadata for video: {video_id}")
            return result
            
        except ValueError:
            raise
        except HttpError as e:
            if e.resp.status == 403:
                logger.error(f"YouTube API quota exceeded or forbidden")
                raise ValueError("YouTube API quota exceeded. Please try again later.")
            elif e.resp.status == 404:
                logger.error(f"Video not found: {e}")
                raise ValueError("Video tidak ditemukan di YouTube")
            else:
                logger.error(f"YouTube API error: {e}")
                raise ValueError(f"YouTube API error: {e.resp.status}")
        except Exception as e:
            logger.error(f"Unexpected error fetching video details: {str(e)}")
            raise ValueError(f"Failed to fetch video details: {str(e)}")

