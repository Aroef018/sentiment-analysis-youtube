from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import asyncio
import logging
from app.db.models.comment import Comment

logger = logging.getLogger(__name__)


class CommentRepository:

    @staticmethod
    async def bulk_create(
        db: AsyncSession,
        comments: List[Comment]
    ) -> None:
        """
        Bulk insert comments in chunks to avoid DB connection timeout.
        Inserts 100 comments per batch with commit.
        Includes retry logic for transient errors.
        """
        if not comments:
            return
        
        CHUNK_SIZE = 100  # Insert 100 comments at a time
        MAX_RETRIES = 3
        total = len(comments)
        
        logger.info(f"Starting bulk insert of {total} comments in chunks of {CHUNK_SIZE}")
        
        for i in range(0, total, CHUNK_SIZE):
            chunk = comments[i:i + CHUNK_SIZE]
            
            rows = [
                {
                    "id": c.id,
                    "video_id": c.video_id,
                    "analysis_id": c.analysis_id,
                    "author": c.author,
                    "text": c.text,
                    "sentiment": c.sentiment,
                    "parent_id": c.parent_id,
                    "is_top_level": c.is_top_level,
                    "like_count": c.like_count,
                    "published_at": c.published_at,
                    "created_at": c.created_at,
                }
                for c in chunk
            ]

            # Retry logic for transient DB errors
            for attempt in range(MAX_RETRIES):
                try:
                    stmt = insert(Comment).values(rows).on_conflict_do_nothing(index_elements=["id"])
                    await db.execute(stmt)
                    await db.commit()
                    logger.info(f"Inserted comments {i}-{i+len(chunk)}/{total}")
                    break  # Success, exit retry loop
                    
                except SQLAlchemyError as e:
                    if attempt < MAX_RETRIES - 1:
                        logger.warning(f"DB error on chunk {i}, retry {attempt + 1}/{MAX_RETRIES}: {str(e)}")
                        await db.rollback()
                        await asyncio.sleep(1)  # Wait before retry
                    else:
                        logger.error(f"DB error on chunk {i} after {MAX_RETRIES} retries: {str(e)}")
                        await db.rollback()
                        raise
        
        logger.info(f"Bulk insert completed: {total} comments")

    @staticmethod
    async def get_by_analysis_id_paginated(
        db: AsyncSession,
        analysis_id: str,
        page: int = 1,
        limit: int = 20,
        sentiment_filter: str | None = None
    ) -> tuple[list[Comment], int]:
        """
        Get paginated comments for an analysis with optional sentiment filter.
        Returns (comments, total_count)
        """
        from sqlalchemy import func
        
        # Build base query with analysis_id filter
        stmt = select(Comment).where(Comment.analysis_id == analysis_id)
        count_stmt = select(func.count()).select_from(Comment).where(Comment.analysis_id == analysis_id)
        
        # Apply sentiment filter if provided
        if sentiment_filter and sentiment_filter.lower() in ["positive", "neutral", "negative"]:
            sentiment_value = sentiment_filter.lower()
            stmt = stmt.where(Comment.sentiment == sentiment_value)
            count_stmt = count_stmt.where(Comment.sentiment == sentiment_value)
        
        # Get total count with filter applied
        total_result = await db.execute(count_stmt)
        total_count = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * limit
        stmt = stmt.order_by(Comment.like_count.desc(), Comment.published_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        comments = result.scalars().all()
        
        return comments, total_count

