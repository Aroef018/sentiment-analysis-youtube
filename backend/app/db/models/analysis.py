import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )

    video_id = sa.Column(
        UUID(as_uuid=True),
        sa.ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False
    )

    total_comments = sa.Column(sa.Integer)
    positive_count = sa.Column(sa.Integer)
    negative_count = sa.Column(sa.Integer)
    neutral_count = sa.Column(sa.Integer)

    created_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now()
    )
