"""create comments table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_create_comments"
down_revision = "003_create_analyses"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "comments",
        sa.Column("id", sa.String(50), primary_key=True),

        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("analyses.id", ondelete="CASCADE"),
        ),

        sa.Column("author", sa.Text),
        sa.Column("text", sa.Text, nullable=False),

        sa.Column(
            "sentiment",
            sa.Enum(
                "positive",
                "negative",
                "neutral",
                name="sentiment_enum",
                create_type=False  # ⬅️ WAJIB
            ),
            nullable=False
        ),

        sa.Column("parent_id", sa.String(50)),
        sa.Column("is_top_level", sa.Boolean, server_default=sa.true()),
        sa.Column("like_count", sa.Integer),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
    )


def downgrade():
    op.drop_table("comments")
