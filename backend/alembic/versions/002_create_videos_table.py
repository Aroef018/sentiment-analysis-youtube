"""create videos table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_create_videos"
down_revision = "001_create_users"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("youtube_video_id", sa.String(50), nullable=False, unique=True),
        sa.Column("title", sa.Text),
        sa.Column("channel_name", sa.Text),
        sa.Column("thumbnail_url", sa.Text),
        sa.Column("like_count", sa.Integer),
        sa.Column("comment_count", sa.Integer),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("videos")
