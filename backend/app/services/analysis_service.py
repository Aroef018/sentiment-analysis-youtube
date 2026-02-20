
import asyncio
from fastapi import HTTPException
import gc
import logging
import uuid
from datetime import datetime
from threading import Lock

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.analysis import Analysis
from app.db.models.comment import Comment
from app.db.models.video import Video
from app.db.repositories import (
    VideoRepository,
    AnalysisRepository,
    CommentRepository,
)
from app.services.preprocessing_service import PreprocessingService
from app.services.sentiment_service import SentimentService, OnnxSentimentService
from app.services.youtube_video_service import YouTubeVideoService
from app.services.analysis_task_registry import running_analysis_tasks

logger = logging.getLogger(__name__)

_sentiment_service = None
_service_lock = Lock()

# Semaphore to limit concurrent analysis - initialized lazily
_analysis_semaphore = None


def _get_analysis_semaphore():
    """Lazy initialization of analysis semaphore"""
    global _analysis_semaphore
    if _analysis_semaphore is None:
        _analysis_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_ANALYSIS)
    return _analysis_semaphore


def _get_sentiment_service():
    """Thread-safe singleton for sentiment service"""
    global _sentiment_service
    
    if _sentiment_service is not None:
        return _sentiment_service
    
    with _service_lock:
        # Double-check locking pattern
        if _sentiment_service is not None:
            return _sentiment_service
        
        logger.info("Initializing sentiment service...")
        
        if settings.ONNX_MODEL_PATH:
            logger.info(
                f"Using ONNX model at {settings.ONNX_MODEL_PATH} (base: {settings.MODEL_PATH})"
            )
            _sentiment_service = OnnxSentimentService(
                model_name_or_path=settings.MODEL_PATH,
                onnx_model_path=settings.ONNX_MODEL_PATH,
                batch_size=settings.SENTIMENT_BATCH_SIZE,
            )
        else:
            logger.info(
                f"Using PyTorch model at {settings.MODEL_PATH} (ONNX not configured)"
            )
            _sentiment_service = SentimentService(
                model_name=settings.MODEL_PATH,
                device="cpu",
                batch_size=settings.SENTIMENT_BATCH_SIZE,
            )
        
        logger.info("Sentiment service initialized successfully")
        return _sentiment_service


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
        
        Protected by semaphore to limit concurrent analysis and prevent memory overload.
        """
        semaphore = _get_analysis_semaphore()
        user_id_str = str(user_id)
        current_task = asyncio.current_task()
        running_analysis_tasks[user_id_str] = current_task
        try:
            # Try to acquire semaphore with timeout (5 minutes to wait in queue)
            async with asyncio.timeout(300):  # 5 minutes timeout to acquire semaphore
                async with semaphore:
                    logger.info(f"Analysis started for user {user_id} (semaphore acquired, limit={settings.MAX_CONCURRENT_ANALYSIS})")
                    try:
                        return await AnalysisService._perform_analysis(db, youtube_url, user_id)
                    except asyncio.CancelledError:
                        logger.warning(f"Analysis cancelled for user {user_id}")
                        raise HTTPException(status_code=409, detail="Analisis dibatalkan oleh pengguna.")
        except asyncio.TimeoutError:
            logger.warning(f"Analysis timeout for user {user_id} - server too busy, waited 5 minutes")
            raise Exception(
                "Server sedang memproses analisis lain. Silakan coba lagi dalam beberapa saat."
            )
        finally:
            # Hapus task dari registry jika sudah selesai/cancelled
            if running_analysis_tasks.get(user_id_str) is current_task:
                del running_analysis_tasks[user_id_str]
    
    @staticmethod
    async def _perform_analysis(
        db: AsyncSession,
        youtube_url: str,
        user_id: uuid.UUID
    ) -> dict:
        """Internal method that performs the actual analysis"""

        # ======================
        # 1️⃣ Extract Video ID
        # ======================
        youtube_service = YouTubeVideoService()
        video_id = youtube_service.extract_video_id(youtube_url)

        # ======================
        # 2️⃣ Video (get or create)
        # ======================
        video = await VideoRepository.get_by_youtube_id(db, video_id)
        if video is None:
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
        
        logger.info(f"Analysis {analysis.id} created for video {video_id}")

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
        # 5️⃣ Preprocess + Sentiment + Save Incrementally
        # ======================
        preprocessing_service = PreprocessingService()
        sentiment_service = _get_sentiment_service()
        
        # Process and save in chunks to avoid memory overload
        CHUNK_SIZE = 100  # Process 100 comments at a time
        total_comments_count = len(raw_comments)
        all_sentiments = []  # Track for final statistics
        
        logger.info(f"Starting sentiment analysis for {total_comments_count} comments in chunks of {CHUNK_SIZE}")

        try:
            for chunk_start in range(0, total_comments_count, CHUNK_SIZE):
                await asyncio.sleep(0)  # Responsif terhadap cancel di setiap chunk
                chunk_end = min(chunk_start + CHUNK_SIZE, total_comments_count)
                chunk = raw_comments[chunk_start:chunk_end]

                logger.info(f"Processing chunk {chunk_start}-{chunk_end}/{total_comments_count}")

                # Preprocess texts in this chunk
                cleaned_texts = []
                for idx, raw in enumerate(chunk):
                    if idx % 20 == 0:
                        await asyncio.sleep(0)  # Responsif terhadap cancel di dalam chunk besar
                    try:
                        clean_text = preprocessing_service.clean_text(raw["text"])
                        cleaned_texts.append(clean_text)
                    except Exception as e:
                        logger.error(f"Error preprocessing comment: {str(e)}")
                        cleaned_texts.append(" ")  # Fallback to empty
                
                # Batch sentiment analysis for this chunk
                batch_results = sentiment_service.analyze_batch(cleaned_texts)
                
                # Create comment models for this chunk only
                chunk_comment_models = []
                for raw, sentiment_result in zip(chunk, batch_results):
                    try:
                        sentiment = sentiment_result["sentiment"]
                        all_sentiments.append(sentiment)  # Track for statistics

                        chunk_comment_models.append(
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
                        logger.error(f"Error mapping comment: {str(e)}")
                        # Skip this comment and continue
                        continue
                
                # Save this chunk to database immediately (incremental save)
                try:
                    await CommentRepository.bulk_create(db, chunk_comment_models)
                    logger.info(f"Saved chunk {chunk_start}-{chunk_end} to database ({len(chunk_comment_models)} comments)")
                except Exception as e:
                    logger.error(f"Failed to save chunk {chunk_start}-{chunk_end}: {str(e)}", exc_info=True)
                    raise Exception(f"Gagal menyimpan komentar chunk {chunk_start}-{chunk_end}. Coba lagi nanti.")
                
                # Clear chunk from memory to prevent accumulation
                del chunk_comment_models
                del cleaned_texts
                del batch_results
                
                # Force garbage collection every 2 chunks to keep memory low
                if (chunk_start // CHUNK_SIZE) % 2 == 0:
                    gc.collect()
            
            total_saved = len(all_sentiments)
            logger.info(f"Sentiment analysis and save completed for {total_saved} comments")
                    
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}", exc_info=True)
            raise Exception("Sentiment analysis gagal. Coba lagi nanti.")

        # ======================
        # 6️⃣ Update video and analysis metadata
        # ======================
        
        # Update video's comment_count to reflect saved comments
        try:
            video.comment_count = len(all_sentiments)
            await db.commit()
            await db.refresh(video)
            logger.info(f"Updated video comment_count to {len(all_sentiments)}")
        except Exception as e:
            logger.warning(f"Failed to update video comment_count: {str(e)}")
            # Non-critical, continue anyway

        # ======================
        # 7️⃣ Update analysis counts
        # ======================
        total_comments = len(all_sentiments)
        positive_count = sum(1 for s in all_sentiments if s == "positive")
        negative_count = sum(1 for s in all_sentiments if s == "negative")
        neutral_count = sum(1 for s in all_sentiments if s == "neutral")

        analysis.total_comments = total_comments
        analysis.positive_count = positive_count
        analysis.negative_count = negative_count
        analysis.neutral_count = neutral_count

        # persist changes
        try:
            await db.commit()
            await db.refresh(analysis)
            logger.info(f"Updated analysis counts: pos={positive_count}, neu={neutral_count}, neg={negative_count}")
        except Exception as e:
            logger.error(f"Failed to update analysis counts: {str(e)}", exc_info=True)
            await db.rollback()
            raise Exception("Gagal menyimpan statistik analisis. Coba lagi nanti.")

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
        
        logger.info(f"Analysis completed successfully for user {user_id}, video {video_id}, {total_comments} comments analyzed")

        return summary
