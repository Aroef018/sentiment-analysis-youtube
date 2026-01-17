# app/services/youtube_comment_service.py

from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.config import settings
from app.services.youtube_video_service import YouTubeVideoService
from app.core.sanitizer import sanitize_comment
import logging

logger = logging.getLogger(__name__)

# Safety limits
MAX_PAGES = 100  # Limit pagination to prevent infinite loops
MAX_RETRIES = 3  # Retry failed requests
MAX_COMMENTS = 10000  # Absolute limit on total comments


class YouTubeCommentService:
    def __init__(self):
        self.youtube = build(
            "youtube",
            "v3",
            developerKey=settings.YOUTUBE_API_KEY,
            cache_discovery=False
        )
        self.video_service = YouTubeVideoService()

    def _get_top_level_comments(self, video_id: str) -> list[dict]:
        """Fetch top-level comments with error handling and pagination limits"""
        comments = []
        next_page_token = None
        page_count = 0

        try:
            while page_count < MAX_PAGES and len(comments) < MAX_COMMENTS:
                try:
                    response = self.youtube.commentThreads().list(
                        part="snippet",
                        videoId=video_id,
                        maxResults=100,
                        textFormat="plainText",
                        pageToken=next_page_token,
                    ).execute()

                    items = response.get("items", [])
                    if not items:
                        break

                    for item in items:
                        try:
                            snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                            
                            # Validate required fields
                            if not snippet:
                                logger.warning("Missing snippet in comment item")
                                continue
                            
                            comment_text = snippet.get("textDisplay", "").strip()
                            if not comment_text:
                                logger.warning("Empty comment text, skipping")
                                continue

                            published_at_str = snippet.get("publishedAt")
                            published_at = None
                            if published_at_str:
                                try:
                                    published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                                except ValueError:
                                    logger.warning(f"Invalid publishedAt format: {published_at_str}")

                            comment_id = item.get("id")
                            if not comment_id:
                                logger.warning("Missing comment ID, skipping")
                                continue

                            # Sanitize comment text to prevent XSS
                            sanitized_text = sanitize_comment(comment_text)

                            comments.append({
                                "comment_id": comment_id,
                                "author": snippet.get("authorDisplayName", "Unknown"),
                                "text": sanitized_text,
                                "published_at": published_at,
                                "like_count": int(snippet.get("likeCount", 0)),
                                "parent_id": None,
                                "is_top_level": True,
                            })

                        except (KeyError, TypeError) as e:
                            logger.warning(f"Error parsing comment: {str(e)}, skipping")
                            continue

                    # Check if we've reached max comments
                    if len(comments) >= MAX_COMMENTS:
                        logger.warning(f"Reached maximum comment limit: {MAX_COMMENTS}")
                        break

                    next_page_token = response.get("nextPageToken")
                    page_count += 1

                    if not next_page_token:
                        break

                except HttpError as e:
                    if e.resp.status == 403:
                        logger.error(f"Access denied for video {video_id}")
                        if "commentDisabled" in str(e):
                            raise Exception("Video ini menonaktifkan komentar")
                        else:
                            raise Exception("Akses ke komentar ditolak")
                    elif e.resp.status == 400:
                        # Invalid video ID or similar
                        logger.error(f"Bad request for video {video_id}: {e}")
                        raise Exception("Video ID tidak valid")
                    else:
                        logger.error(f"YouTube API error on page {page_count}: {e}")
                        raise Exception(f"YouTube API error: {e.resp.status}")
                except Exception as e:
                    if isinstance(e, Exception) and ("commentDisabled" in str(e) or "menonaktifkan" in str(e) or "ditolak" in str(e)):
                        raise
                    logger.error(f"Error fetching comments on page {page_count}: {str(e)}")
                    raise Exception(f"Failed to fetch comments: {str(e)}")

            logger.info(f"Successfully fetched {len(comments)} top-level comments for video {video_id}")

        except Exception as e:
            if isinstance(e, Exception) and "Video ini" in str(e):
                raise  # Re-raise our custom messages
            logger.error(f"Fatal error fetching top-level comments: {str(e)}")
            raise

        return comments

    def _get_replies(self, parent_id: str) -> list[dict]:
        """Fetch replies to a comment with error handling"""
        replies = []
        next_page_token = None
        page_count = 0

        try:
            while page_count < MAX_PAGES and len(replies) < MAX_COMMENTS:
                try:
                    response = self.youtube.comments().list(
                        part="snippet",
                        parentId=parent_id,
                        maxResults=100,
                        textFormat="plainText",
                        pageToken=next_page_token,
                    ).execute()

                    items = response.get("items", [])
                    if not items:
                        break

                    for item in items:
                        try:
                            snippet = item.get("snippet", {})
                            
                            if not snippet:
                                logger.warning("Missing snippet in reply item")
                                continue

                            reply_text = snippet.get("textDisplay", "").strip()
                            if not reply_text:
                                continue

                            published_at_str = snippet.get("publishedAt")
                            published_at = None
                            if published_at_str:
                                try:
                                    published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                                except ValueError:
                                    logger.warning(f"Invalid publishedAt in reply: {published_at_str}")

                            reply_id = item.get("id")
                            if not reply_id:
                                continue

                            # Sanitize reply text to prevent XSS
                            sanitized_text = sanitize_comment(reply_text)

                            replies.append({
                                "comment_id": reply_id,
                                "author": snippet.get("authorDisplayName", "Unknown"),
                                "text": sanitized_text,
                                "published_at": published_at,
                                "like_count": int(snippet.get("likeCount", 0)),
                                "parent_id": parent_id,
                                "is_top_level": False,
                            })

                        except (KeyError, TypeError) as e:
                            logger.warning(f"Error parsing reply: {str(e)}")
                            continue

                    if len(replies) >= MAX_COMMENTS:
                        logger.warning(f"Reached maximum replies limit: {MAX_COMMENTS}")
                        break

                    next_page_token = response.get("nextPageToken")
                    page_count += 1

                    if not next_page_token:
                        break

                except HttpError as e:
                    logger.warning(f"Error fetching replies for comment {parent_id}: {e}")
                    break  # Skip this thread's replies but continue with others
                except Exception as e:
                    logger.warning(f"Unexpected error fetching replies: {str(e)}")
                    break

        except Exception as e:
            logger.error(f"Fatal error in _get_replies: {str(e)}")
            # Don't raise here - just return partial results

        return replies

    def fetch_all_comments(self, url: str) -> list[dict]:
        """
        Fetch all comments (top-level + replies) with comprehensive error handling
        """
        try:
            video_id = self.video_service.extract_video_id(url)

            all_comments = []
            top_comments = self._get_top_level_comments(video_id)

            if not top_comments:
                logger.warning(f"No top-level comments found for video {video_id}")
                raise Exception("Video ini tidak memiliki komentar yang dapat dianalisis")

            # Fetch replies for each top-level comment
            for comment in top_comments:
                try:
                    replies = self._get_replies(comment["comment_id"])
                    all_comments.append(comment)
                    all_comments.extend(replies)
                except Exception as e:
                    logger.warning(f"Error fetching replies for comment {comment['comment_id']}: {str(e)}")
                    # Still add the top-level comment even if replies fail
                    all_comments.append(comment)

            logger.info(f"Successfully fetched total {len(all_comments)} comments for video {video_id}")
            return all_comments

        except Exception as e:
            if isinstance(e, Exception) and "Video ini" in str(e):
                raise  # Re-raise our custom messages
            logger.error(f"Failed to fetch comments: {str(e)}")
            raise Exception(f"Failed to fetch comments: {str(e)}")

