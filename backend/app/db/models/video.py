import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class Video(Base):
    __tablename__ = "videos"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    youtube_video_id = sa.Column(sa.String(50), nullable=False, unique=True, index=True)
    title = sa.Column(sa.Text)
    channel_name = sa.Column(sa.Text)
    thumbnail_url = sa.Column(sa.Text)
    like_count = sa.Column(sa.Integer)
    comment_count = sa.Column(sa.Integer)
    published_at = sa.Column(sa.DateTime(timezone=True))

    created_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now()
    )

    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
    )
