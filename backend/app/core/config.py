import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "Novel to Video API"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/novel_to_video"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    UPLOAD_DIR: str = "storage/uploads"
    OUTPUT_DIR: str = "storage/output"
    LOG_DIR: str = "storage/logs"
    MODEL_DIR: str = "storage/models"
    MAX_UPLOAD_SIZE_MB: int = 100

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    ARK_API_KEY: str = ""
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    ARK_ENDPOINT_ID: str = ""
    SD_WEBUI_URL: str = "http://127.0.0.1:7860"

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # 工作流模式：simple (简单线程) 或 celery (Celery+Redis)
    WORKFLOW_MODE: str = "simple"

    @property
    def cors_origins_list(self):
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def upload_dir_path(self):
        return BASE_DIR / Path(self.UPLOAD_DIR)

    @property
    def output_dir_path(self):
        return BASE_DIR / Path(self.OUTPUT_DIR)

    @property
    def log_dir_path(self):
        return BASE_DIR / Path(self.LOG_DIR)

    @property
    def model_dir_path(self):
        return BASE_DIR / Path(self.MODEL_DIR)

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

# 确保目录存在
settings.upload_dir_path.mkdir(parents=True, exist_ok=True)
settings.output_dir_path.mkdir(parents=True, exist_ok=True)
settings.log_dir_path.mkdir(parents=True, exist_ok=True)
settings.model_dir_path.mkdir(parents=True, exist_ok=True)
