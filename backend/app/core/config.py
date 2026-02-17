# app/core/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    YOUTUBE_API_KEY: str
    MODEL_PATH: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"  # Default HF model
    ONNX_MODEL_PATH: str | None = None
    SENTIMENT_BATCH_SIZE: int = 16
    MAX_CONCURRENT_ANALYSIS: int = 2  # Limit concurrent analysis to prevent memory overload
    SECRET_KEY: str
    GOOGLE_CLIENT_ID: str
    SENTIMENT_SWAP_POS_NEG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
