import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = sa.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    email = sa.Column(sa.String(150), unique=True, nullable=False)
    full_name = sa.Column(sa.String(150))

    password_hash = sa.Column(sa.String(255), nullable=True)

    provider = sa.Column(sa.String(30))        # "local", "google"
    provider_id = sa.Column(sa.String(200))    # id dari Google

    avatar_url = sa.Column(sa.Text)

    created_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now()
    )
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now()
    )
