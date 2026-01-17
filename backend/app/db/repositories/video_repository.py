from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.video import Video


class VideoRepository:

    @staticmethod
    async def get_by_youtube_id(
        db: AsyncSession,
        youtube_video_id: str
    ) -> Video | None:
        result = await db.execute(
            select(Video).where(Video.youtube_video_id == youtube_video_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        video: Video
    ) -> Video:
        db.add(video)
        await db.commit()
        await db.refresh(video)
        return video
