"""
RSS智能订阅器后端服务主应用
基于FastAPI的RSS聚合和智能订阅平台
"""

from typing import Dict, Any, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.services.auto_fetch_scheduler import AutoFetchScheduler
# 导入标签调度器
from app.scheduler.tag_scheduler import tag_scheduler

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="基于RSSHub和LLM的智能个人订阅器，提供智能内容筛选、摘要生成和个性化推荐功能",
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS中间件 - 修复OPTIONS请求处理
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8000", 
        "http://127.0.0.1:8001"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# 全局调度器实例
scheduler = None

@app.on_event("startup")
async def startup_event() -> None:
    """应用启动时的初始化事件"""
    logger.info("🚀 RSSia后端服务启动中...")
    logger.info(f"📋 项目名称: {settings.PROJECT_NAME}")
    logger.info(f"🔧 版本: {settings.PROJECT_VERSION}")
    logger.info(f"🌐 环境: {settings.ENVIRONMENT}")
    logger.info(f"🔗 API前缀: {settings.API_V1_STR}")
    
    # 启动RSS拉取调度器（使用功能完整的AutoFetchScheduler）
    global scheduler
    scheduler = AutoFetchScheduler()
    scheduler.start()
    logger.info("✅ RSS自动拉取调度器已启动")
    
    # 标签调度器已在导入时自动启动
    logger.info("✅ 标签缓存调度器已启动")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """应用关闭时的清理事件"""
    logger.info("🛑 RSSia后端服务正在关闭...")
    global scheduler
    if scheduler:
        scheduler.stop()
        logger.info("✅ RSS自动拉取调度器已停止")
    
    # 关闭标签调度器
    tag_scheduler.shutdown()
    logger.info("✅ 标签缓存调度器已停止")


@app.get("/")
async def root() -> Dict[str, str]:
    """根路径健康检查接口"""
    return {
        "message": "RSSia后端服务",
        "version": settings.PROJECT_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check() -> Dict[str, Union[str, bool]]:
    """健康检查接口"""
    return {
        "status": "healthy",
        "version": settings.PROJECT_VERSION,
        "service": "rss-smart-subscriber",
        "scheduler_running": scheduler.scheduler.running if scheduler else False,
        "tag_scheduler_running": tag_scheduler.scheduler.running if tag_scheduler else False
    }


# 注册API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 直接运行模式启动服务...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 