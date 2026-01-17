import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Comment(Base):
    __tablename__ = "comments"

    id = sa.Column(sa.String(50), primary_key=True)

    video_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("videos.id", ondelete="CASCADE")
    )

    analysis_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("analyses.id", ondelete="CASCADE")
    )

    author = sa.Column(sa.Text)
    text = sa.Column(sa.Text, nullable=False)

    sentiment = sa.Column(
        sa.Enum(
            "positive",
            "negative",
            "neutral",
            name="sentiment_enum",
            create_type=False   # ⬅️ PENTING
        ),
        nullable=False
    )

    parent_id = sa.Column(sa.String(50))
    is_top_level = sa.Column(sa.Boolean, default=True)
    like_count = sa.Column(sa.Integer)

    published_at = sa.Column(sa.DateTime(timezone=True))
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now()
    )
