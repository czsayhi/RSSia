"""
健康检查端点
提供系统状态和健康检查功能
"""

from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends
from loguru import logger

from app.core.config import get_settings, Settings

router = APIRouter()


@router.get("/", summary="基础健康检查")
async def health_check(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    基础健康检查接口
    返回服务基本状态信息
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "rss-smart-subscriber",
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/detailed", summary="详细健康检查")
async def detailed_health_check(
    settings: Settings = Depends(get_settings)
) -> Dict[str, Any]:
    """
    详细健康检查接口
    返回系统各组件的详细状态
    """
    try:
        # TODO: 添加数据库连接检查
        database_status = "healthy"
        
        # TODO: 添加RSSHub连接检查
        rsshub_status = "healthy"
        
        # TODO: 添加定时任务状态检查
        scheduler_status = "healthy"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "rss-smart-subscriber",
            "version": settings.PROJECT_VERSION,
            "environment": settings.ENVIRONMENT,
            "components": {
                "database": {
                    "status": database_status,
                    "url": settings.DATABASE_URL
                },
                "rsshub": {
                    "status": rsshub_status,
                    "base_url": settings.RSSHUB_BASE_URL
                },
                "scheduler": {
                    "status": scheduler_status,
                    "timezone": settings.SCHEDULER_TIMEZONE
                }
            },
            "configuration": {
                "api_version": settings.API_V1_STR,
                "log_level": settings.LOG_LEVEL,
                "rss_fetch_interval": f"{settings.RSS_FETCH_INTERVAL_MINUTES}分钟"
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        } 