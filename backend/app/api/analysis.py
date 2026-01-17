from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.schemas import AnalysisRequest, AnalysisResponse, HistoryResponse, HistoryItem
from app.db.session import get_async_db
from app.services.analysis_service import AnalysisService
from app.core.config import settings
from app.core.security import ALGORITHM
from app.core.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])
auth_scheme = HTTPBearer(auto_error=True)


def decode_token_safely(token: str) -> dict:
    """Safely decode JWT token with proper error handling"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")


def get_user_id_from_token(credentials: HTTPAuthorizationCredentials) -> uuid.UUID:
    """Extract and validate user ID from token"""
    token = credentials.credentials
    payload = decode_token_safely(token)
    
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    
    try:
        user_id = uuid.UUID(sub)
        return user_id
    except ValueError:
        logger.warning(f"Invalid token subject format: {sub}")
        raise HTTPException(status_code=401, detail="Invalid token subject format")


@router.post("/", response_model=AnalysisResponse)
@limiter.limit("3/minute")
async def analyze_youtube_video(
    request: Request,
    payload: AnalysisRequest,
    db: AsyncSession = Depends(get_async_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    """
    Analyze YouTube video for sentiment
    Input: YouTube URL
    Output: Sentiment analysis summary
    """
    try:
        user_id = get_user_id_from_token(credentials)
        
        logger.info(f"Starting analysis for user {user_id}")
        result = await AnalysisService.analyze_youtube_video(
            db=db,
            youtube_url=str(payload.youtube_url),
            user_id=user_id,
        )
        return result

    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed. Please try again later.")


@router.get("/history", response_model=HistoryResponse)
@limiter.limit("30/minute")
async def get_history(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    """Get analysis history for current user"""
    try:
        user_uuid = get_user_id_from_token(credentials)

        from app.db.repositories.analysis_repository import AnalysisRepository

        rows = await AnalysisRepository.get_latest_per_video_for_user(db, user_uuid)

        items: list[HistoryItem] = []
        for analysis, video in rows:
            total = max(analysis.total_comments or 0, 0)
            pos = max(analysis.positive_count or 0, 0)
            neu = max(analysis.neutral_count or 0, 0)
            neg = max(analysis.negative_count or 0, 0)

            def pct(v: int) -> int:
                return int(round((v / total) * 100)) if total > 0 else 0

            items.append(
                HistoryItem(
                    id=str(video.id),
                    title=video.title,
                    channel=video.channel_name,
                    thumbnail=video.thumbnail_url,
                    date=(analysis.created_at.isoformat() if analysis.created_at else ""),
                    positive=pct(pos),
                    neutral=pct(neu),
                    negative=pct(neg),
                )
            )

        logger.info(f"Retrieved history with {len(items)} items for user {user_uuid}")
        return HistoryResponse(items=items)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")


@router.get("/detail/{video_id}")
@limiter.limit("30/minute")
async def get_analysis_detail(
    request: Request,
    video_id: str,
    db: AsyncSession = Depends(get_async_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    """
    Get detailed analysis for a specific video.
    Only returns data if the analysis belongs to the current user.
    """
    try:
        user_uuid = get_user_id_from_token(credentials)
        
        try:
            video_uuid = uuid.UUID(video_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid video ID format")

        from app.db.repositories.analysis_repository import AnalysisRepository

        row = await AnalysisRepository.get_latest_for_video_and_user(db, video_uuid, user_uuid)
        if not row:
            raise HTTPException(
                status_code=404, 
                detail="Analysis not found for this video"
            )

        analysis, video = row

        total = max(analysis.total_comments or 0, 0)
        pos = max(analysis.positive_count or 0, 0)
        neu = max(analysis.neutral_count or 0, 0)
        neg = max(analysis.negative_count or 0, 0)

        def pct(v: int) -> int:
            return int(round((v / total) * 100)) if total > 0 else 0

        logger.info(f"Retrieved analysis detail for video {video_id}")
        return {
            "video": {
                "id": str(video.id),
                "title": video.title,
                "channel": video.channel_name,
                "thumbnail_url": video.thumbnail_url,
                "like_count": video.like_count,
                "comment_count": video.comment_count,
                "published_at": (video.published_at.isoformat() if video.published_at else None),
            },
            "analysis": {
                "id": str(analysis.id),
                "created_at": (analysis.created_at.isoformat() if analysis.created_at else None),
                "total_comments": total,
                "positive": pos,
                "neutral": neu,
                "negative": neg,
                "percentages": {
                    "positive": pct(pos),
                    "neutral": pct(neu),
                    "negative": pct(neg),
                },
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis detail: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis detail")


@router.get("/comments/{video_id}")
@limiter.limit("30/minute")
async def get_analysis_comments(
    request: Request,
    video_id: str,
    page: int = 1,
    limit: int = 20,
    sentiment: str | None = None,
    db: AsyncSession = Depends(get_async_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    """
    Get paginated comments for the latest analysis of a video with optional sentiment filter.
    Only returns comments if the analysis belongs to the current user.
    """
    try:
        user_uuid = get_user_id_from_token(credentials)
        
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
        
        try:
            video_uuid = uuid.UUID(video_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid video ID format")

        from app.db.repositories.comment_repository import CommentRepository
        from app.db.repositories.analysis_repository import AnalysisRepository

        # Get the latest analysis for this video and verify it belongs to the user
        row = await AnalysisRepository.get_latest_for_video_and_user(db, video_uuid, user_uuid)
        if not row:
            raise HTTPException(status_code=404, detail="Analysis not found for this video")
        
        analysis, _ = row

        # Validate sentiment filter if provided
        if sentiment and sentiment not in ["positive", "neutral", "negative"]:
            raise HTTPException(status_code=400, detail="Invalid sentiment filter")

        # Get paginated comments
        comments, total = await CommentRepository.get_by_analysis_id_paginated(
            db, str(analysis.id), page, limit, sentiment
        )

        items = [
            {
                "id": str(c.id),
                "author": c.author,
                "text": c.text,
                "sentiment": c.sentiment,
                "like_count": c.like_count,
                "published_at": (c.published_at.isoformat() if c.published_at else None),
                "is_top_level": c.is_top_level,
            }
            for c in comments
        ]

        total_pages = (total + limit - 1) // limit

        logger.info(f"Retrieved comments page {page} for video {video_id}")
        return {
            "items": items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            },
            "filter": sentiment or "all",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving comments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve comments")


@router.delete("/video/{video_id}")
@limiter.limit("10/minute")
async def delete_video_analysis(
    request: Request,
    video_id: str,
    db: AsyncSession = Depends(get_async_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    """
    Delete all analyses for a specific video owned by the current user.
    This will cascade delete all comments related to those analyses.
    """
    try:
        user_uuid = get_user_id_from_token(credentials)
        
        try:
            video_uuid = uuid.UUID(video_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid video ID format")

        from sqlalchemy import delete
        from app.db.models.analysis import Analysis

        # Delete all analyses for this video by this user (comments will cascade)
        stmt = delete(Analysis).where(
            Analysis.video_id == video_uuid,
            Analysis.user_id == user_uuid
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=404, 
                detail="Video not found or does not belong to you"
            )
        
        logger.info(f"Deleted {result.rowcount} analyses for video {video_id}")
        return {"message": "Analysis deleted successfully", "deleted_count": result.rowcount}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete analysis")