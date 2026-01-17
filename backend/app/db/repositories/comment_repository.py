from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from app.db.models.comment import Comment


class CommentRepository:

    @staticmethod
    async def bulk_create(
        db: AsyncSession,
        comments: List[Comment]
    ) -> None:
        # Upsert: do nothing on conflict of primary key 'id'
        if not comments:
            return

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
            for c in comments
        ]

        stmt = insert(Comment).values(rows).on_conflict_do_nothing(index_elements=["id"])
        await db.execute(stmt)
        await db.commit()

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
        stmt = select(Comment).where(Comment.analysis_id == analysis_id)
        
        if sentiment_filter and sentiment_filter.lower() in ["positive", "neutral", "negative"]:
            stmt = stmt.where(Comment.sentiment == sentiment_filter.lower())
        
        # Get total count
        count_stmt = select(Comment).where(Comment.analysis_id == analysis_id)
        if sentiment_filter and sentiment_filter.lower() in ["positive", "neutral", "negative"]:
            count_stmt = count_stmt.where(Comment.sentiment == sentiment_filter.lower())
        
        from sqlalchemy import func
        total_result = await db.execute(select(func.count()).select_from(Comment).where(Comment.analysis_id == analysis_id) if not sentiment_filter else select(func.count()).select_from(Comment).where(Comment.analysis_id == analysis_id).where(Comment.sentiment == sentiment_filter.lower()))
        total_count = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * limit
        stmt = stmt.order_by(Comment.like_count.desc(), Comment.published_at.desc()).offset(offset).limit(limit)
        
        result = await db.execute(stmt)
        comments = result.scalars().all()
        
        return comments, total_count

