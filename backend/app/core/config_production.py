"""
Railway Production Configuration
"""

import os
from typing import Optional

# Database
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Railway uses postgres://, SQLAlchemy needs postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Security
SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

# JWT
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

# CORS
ALLOWED_ORIGINS: list[str] = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    os.getenv("FRONTEND_URL", "http://localhost:5173"),
]

# Google OAuth
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

# YouTube API
YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if ENVIRONMENT == "production" else "DEBUG")
