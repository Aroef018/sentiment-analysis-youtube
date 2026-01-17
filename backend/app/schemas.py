from pydantic import BaseModel, HttpUrl, Field, EmailStr, field_validator
from typing import Dict
import re


class AnalysisRequest(BaseModel):
    youtube_url: HttpUrl = Field(..., description="Valid YouTube URL")


class VideoSummary(BaseModel):
    id: str
    title: str
    channel: str
    thumbnail_url: str | None = None
    like_count: int | None = None
    comment_count: int | None = None


class AnalysisResponse(BaseModel):
    video: VideoSummary
    analysis_id: str
    total_comments: int
    sentiment_distribution: Dict[str, int]


class HistoryItem(BaseModel):
    id: str  # use video id for stable selection
    title: str
    channel: str
    thumbnail: str | None = None
    date: str
    positive: int
    neutral: int
    negative: int


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


# Auth request schemas
class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(min_length=8, max_length=128, description="Password must be 8-128 characters")
    full_name: str | None = Field(None, max_length=200, description="Full name (optional, max 200 characters)")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength requirements"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # At least one uppercase letter
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # At least one lowercase letter
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # At least one digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        """Validate full name format"""
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError("Full name must be at least 2 characters long")
            # Only allow alphanumeric, spaces, and common punctuation
            if not re.match(r"^[a-zA-Z0-9\s\-\.\']$", v):
                raise ValueError("Full name contains invalid characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(min_length=1, description="User password")


class GoogleLoginRequest(BaseModel):
    token: str = Field(min_length=1, max_length=2048, description="Google OAuth token")
