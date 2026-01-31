from pydantic_settings import BaseSettings
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    OPENAI_MODEL: str = "qwen-plus"

    DATABASE_URL: str = "sqlite:///./data/huntingagent.db"

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440

    APP_NAME: str = "HuntingAgent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    TOOL_TIMEOUT: int = 30
    TOOL_MAX_MEMORY: str = "256M"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()