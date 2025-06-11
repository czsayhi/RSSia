"""
应用程序配置管理
使用Pydantic Settings进行环境变量管理和配置验证
"""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用程序配置类"""
    
    # 基础项目信息
    PROJECT_NAME: str = "RSS智能订阅器"
    PROJECT_VERSION: str = "0.2.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # 安全配置
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8天
    
    # CORS配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",  # Next.js开发服务器
        "http://localhost:3001",  # Next.js开发服务器备用端口
        "http://localhost:8000",  # FastAPI开发服务器
        "http://localhost:8001",  # FastAPI开发服务器实际端口
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001", 
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """验证和组装CORS源"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./rss_subscriber.db"
    DATABASE_ECHO: bool = False  # 生产环境中应设为False
    
    # RSSHub配置
    RSSHUB_BASE_URL: str = "https://rsshub.app"
    RSSHUB_FALLBACK_URLS: List[str] = [
        "https://rss.shab.fun",
        "https://rsshub.feeded.xyz"
    ]
    RSSHUB_REQUEST_TIMEOUT: int = 30
    RSSHUB_MAX_RETRIES: int = 3
    
    # RSS内容抓取配置
    RSS_FETCH_INTERVAL_MINUTES: int = 30  # RSS内容抓取间隔(分钟)
    RSS_CONTENT_RETENTION_DAYS: int = 1   # 内容保留天数 - 调整为1天
    RSS_MAX_ENTRIES_PER_FEED: int = 100   # 每个Feed最大条目数
    
    # 定时任务配置
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    SCHEDULER_MAX_WORKERS: int = 4
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    
    # API限流配置
    API_RATE_LIMIT_PER_MINUTE: int = 100
    API_RATE_LIMIT_BURST: int = 200
    
    # AI功能预留配置
    OPENAI_API_KEY: Optional[str] = None
    AI_MODEL_NAME: str = "gpt-3.5-turbo"
    AI_MAX_TOKENS: int = 1000
    AI_TEMPERATURE: float = 0.7
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER: str = "./uploads"
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".pdf"]
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取应用程序配置实例"""
    return settings 