"""
API v1主路由
汇总所有v1版本的API端点
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, subscriptions, content, health, subscription_config

# 创建API v1路由器
api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(
    health.router, 
    prefix="/health", 
    tags=["健康检查"]
)

api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["用户认证"]
)

api_router.include_router(
    subscriptions.router, 
    prefix="/subscriptions", 
    tags=["订阅管理"]
)

api_router.include_router(
    content.router, 
    prefix="/content", 
    tags=["内容管理"]
)

api_router.include_router(
    subscription_config.router, 
    prefix="/subscription-config", 
    tags=["订阅配置"]
) 