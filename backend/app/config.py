"""Configuration settings for Bunker Game"""

from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "Гра бункер"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./bunker_game.db"

    # Redis (optional)
    REDIS_URL: Optional[str] = None

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Game Settings
    MIN_PLAYERS: int = 4
    MAX_PLAYERS: int = 16
    DISCUSSION_TIME_SECONDS: int = 180  # 3 minutes
    VOTING_TIME_SECONDS: int = 60

    # CORS - can be comma-separated string or list
    CORS_ORIGINS: list[str] = [
        "*",  # Allow all origins for flexibility
        "https://bunker.zelma4.me",
        "http://bunker.zelma4.me",
        "http://localhost:8765",
        "http://localhost:8000",
    ]
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from string or list"""
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    # Rate Limiting
    CHAT_RATE_LIMIT: int = 10  # messages per minute

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
