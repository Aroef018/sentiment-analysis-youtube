from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models.analysis import Analysis
from app.db.models.video import Video
import uuid


class AnalysisRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        analysis: Analysis
    ) -> Analysis:
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        return analysis

    @staticmethod
    async def get_latest_per_video_for_user(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[tuple[Analysis, Video]]:
        latest_subq = (
            select(
                Analysis.video_id,
                func.max(Analysis.created_at).label("max_created"),
            )
            .where(Analysis.user_id == user_id)
            .group_by(Analysis.video_id)
            .subquery()
        )

        stmt = (
            select(Analysis, Video)
            .join(latest_subq, (Analysis.video_id == latest_subq.c.video_id) & (Analysis.created_at == latest_subq.c.max_created))
            .join(Video, Video.id == Analysis.video_id)
            .order_by(Analysis.created_at.desc())
        )

        result = await db.execute(stmt)
        rows = result.all()
        return rows

    @staticmethod
    async def get_latest_for_video_and_user(
        db: AsyncSession,
        video_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[Analysis, Video] | None:
        """
        Get the latest analysis for a specific video belonging to a user.
        """
        stmt = (
            select(Analysis, Video)
            .join(Video, Video.id == Analysis.video_id)
            .where(Analysis.user_id == user_id)
            .where(Analysis.video_id == video_id)
            .order_by(Analysis.created_at.desc())
            .limit(1)
        )

        result = await db.execute(stmt)
        row = result.first()
        return row
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        analysis_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Analysis | None:
        """
        Get an analysis by ID, verifying it belongs to the user.
        """
        stmt = (
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .where(Analysis.user_id == user_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()