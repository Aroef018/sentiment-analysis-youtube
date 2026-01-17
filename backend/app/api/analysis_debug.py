"""
Debug endpoints for troubleshooting comment fetching.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.core.config import settings
from app.core.security import ALGORITHM

router = APIRouter(prefix="/analysis", tags=["Analysis-Debug"])
auth_scheme = HTTPBearer(auto_error=True)


@router.get("/debug/comments/{video_id}")
async def debug_analysis_comments(
    video_id: str,
    db: AsyncSession = Depends(get_async_db),
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    """
    DEBUG ENDPOINT: Show raw comment data for troubleshooting.
    """
    try:
        token = credentials.credentials
        payload_jwt = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload_jwt.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Invalid token")
        try:
            user_uuid = uuid.UUID(sub)
            video_uuid = uuid.UUID(video_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid video id")

        from app.db.repositories.analysis_repository import AnalysisRepository
        from app.db.repositories.comment_repository import CommentRepository

        # Check if analysis exists
        row = await AnalysisRepository.get_latest_for_video_and_user(db, video_uuid, user_uuid)
        if not row:
            return {"error": "No analysis found for this video", "video_id": str(video_uuid), "user_id": str(user_uuid)}
        
        analysis, video = row

        # Get ALL comments (no pagination, no filtering)
        all_comments, total = await CommentRepository.get_by_analysis_id_paginated(
            db, str(analysis.id), page=1, limit=1000, sentiment_filter=None
        )

        return {
            "analysis_id": str(analysis.id),
            "video_id": str(video.id),
            "user_id": str(user_uuid),
            "total_comments": total,
            "comments": [
                {
                    "id": str(c.id),
                    "author": c.author,
                    "sentiment": c.sentiment,
                    "text": c.text[:50] + "..." if len(c.text) > 50 else c.text,
                }
                for c in all_comments
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}
