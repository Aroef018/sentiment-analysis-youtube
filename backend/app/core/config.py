# app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    YOUTUBE_API_KEY: str
    MODEL_PATH: str
    SECRET_KEY: str
    GOOGLE_CLIENT_ID: str
    SENTIMENT_SWAP_POS_NEG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
