# Core Configuration
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LLM Router & Matching Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Hugging Face
    HF_API_TOKEN: Optional[str] = None
    HF_RATE_LIMIT: int = 60  # requests per minute
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./hardware.db"
    
    # Calculation
    DEFAULT_OVERHEAD_FACTOR: float = 0.20  # 20% overhead
    HIGH_LOAD_OVERHEAD_FACTOR: float = 0.40  # 40% for production
    MOBILE_MEMORY_RATIO: float = 0.75  # 75% available for Apple Silicon
    
    class Config:
        env_file = ".env"


settings = Settings()
