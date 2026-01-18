import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.services.youtube_video_service import YouTubeVideoService
from app.services.preprocessing_service import PreprocessingService
from app.services.sentiment_service import SentimentService
from app.core.config import settings

from app.db.repositories import (
    VideoRepository,
    AnalysisRepository,
    CommentRepository,
)

from app.db.models.video import Video
from app.db.models.analysis import Analysis
from app.db.models.comment import Comment

logger = logging.getLogger(__name__)


class AnalysisService:

    @staticmethod
    async def analyze_youtube_video(
        db: AsyncSession,
        youtube_url: str,
        user_id: uuid.UUID
    ) -> dict:
        """
        1. Extract video ID
        2. Get video metadata
        3. Get comments
        4. Preprocess + sentiment
        5. Save to DB
        6. Return summary
        """

        # ======================
        # 1️⃣ Extract Video ID
        # ======================
        youtube_service = YouTubeVideoService()
        video_id = youtube_service.extract_video_id(youtube_url)

        # ======================
        # 2️⃣ Video (get or create)
        # ======================
        video = await VideoRepository.get_by_youtube_id(db, video_id)

        if not video:
            metadata = youtube_service.fetch_video_detail(youtube_url)

            video = Video(
                id=uuid.uuid4(),
                youtube_video_id=video_id,
                title=metadata["title"],
                channel_name=metadata["channel_name"],
                published_at=metadata["published_at"],
                thumbnail_url=metadata.get("thumbnail_url"),
                like_count=metadata.get("like_count"),
                comment_count=metadata.get("comment_count"),
                created_at=datetime.utcnow(),
            )

            video = await VideoRepository.create(db, video)
        else:
            # update existing video metadata (thumbnail, like/comment counts)
            try:
                metadata = youtube_service.fetch_video_detail(youtube_url)
                video.thumbnail_url = metadata.get("thumbnail_url")
                video.like_count = metadata.get("like_count")
                video.comment_count = metadata.get("comment_count")
                await db.commit()
                await db.refresh(video)
            except Exception:
                # ignore metadata update failures to avoid breaking analysis
                pass

        # ======================
        # 3️⃣ Create Analysis
        # ======================
        analysis = Analysis(
            id=uuid.uuid4(),
            user_id=user_id,
            video_id=video.id,
            created_at=datetime.utcnow(),
        )

        analysis = await AnalysisRepository.create(db, analysis)

        # ======================
        # 4️⃣ Fetch Comments
        # ======================
        from app.services.youtube_comment_service import YouTubeCommentService

        comment_service = YouTubeCommentService()
        raw_comments = comment_service.fetch_all_comments(youtube_url)

        # Check if no comments found
        if not raw_comments or len(raw_comments) == 0:
            raise Exception("Video ini tidak memiliki komentar yang dapat dianalisis")

        # ======================
        # 5️⃣ Preprocess + Sentiment
        # ======================
        preprocessing_service = PreprocessingService()
        sentiment_service = SentimentService(
            model_name=settings.MODEL_PATH,
            device="cpu"
        )
        comment_models = []

        try:
            for idx, raw in enumerate(raw_comments):
                try:
                    clean_text = preprocessing_service.clean_text(raw["text"])
                    result = sentiment_service.analyze(clean_text)
                    sentiment = result["sentiment"]

                    comment_models.append(
                        Comment(
                            id=raw["comment_id"],
                            video_id=video.id,
                            analysis_id=analysis.id,
                            author=raw["author"],
                            text=raw["text"],
                            sentiment=sentiment,
                            parent_id=raw.get("parent_id"),
                            is_top_level=raw["is_top_level"],
                            like_count=raw["like_count"],
                            published_at=raw["published_at"],
                            created_at=datetime.utcnow(),
                        )
                    )
                except Exception as e:
                    logger.error(f"Error analyzing comment {idx}: {str(e)}")
                    # Skip this comment and continue
                    continue
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            raise Exception("Sentiment analysis gagal. Coba lagi nanti.")

        # ======================
        # 6️⃣ Save Comments
        # ======================
        await CommentRepository.bulk_create(db, comment_models)

        # update video's comment_count to reflect saved comments
        try:
            video.comment_count = len(comment_models)
            await db.commit()
            await db.refresh(video)
        except Exception:
            pass

        # ======================
        # 7️⃣ Update analysis counts
        # ======================
        total_comments = len(comment_models)
        positive_count = sum(1 for c in comment_models if c.sentiment == "positive")
        negative_count = sum(1 for c in comment_models if c.sentiment == "negative")
        neutral_count = sum(1 for c in comment_models if c.sentiment == "neutral")

        analysis.total_comments = total_comments
        analysis.positive_count = positive_count
        analysis.negative_count = negative_count
        analysis.neutral_count = neutral_count

        # persist changes
        await db.commit()
        await db.refresh(analysis)

        # ======================
        # 8️⃣ Return Summary
        # ======================
        summary = {
            "video": {
                "id": str(video.id),
                "title": video.title,
                "channel": video.channel_name,
                "thumbnail_url": video.thumbnail_url,
                "like_count": video.like_count,
                "comment_count": video.comment_count,
            },
            "analysis_id": str(analysis.id),
            "total_comments": total_comments,
            "sentiment_distribution": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
            },
        }

        return summary
