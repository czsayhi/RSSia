"""
API v1主路由
汇总所有v1版本的API端点
"""

from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth, 
    subscriptions, 
    subscriptions_v2, 
    content, 
    health, 
    subscription_config, 
    subscription_search, 
    fetch_config_api, 
    user_content_api, 
    tag_admin
)

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
    subscriptions_v2.router, 
    prefix="/subscriptions-v2", 
    tags=["订阅管理V2"]
)

api_router.include_router(
    content.router, 
    prefix="/content", 
    tags=["内容管理（旧版）"]
)

api_router.include_router(
    subscription_config.router, 
    prefix="/subscription-config", 
    tags=["订阅配置"]
)

api_router.include_router(
    subscription_search.router,
    prefix="/subscription-search",
    tags=["订阅搜索"]
)

api_router.include_router(
    fetch_config_api.router,
    prefix="/fetch",
    tags=["拉取配置"]
)

# 新的用户内容API（基于共享内容架构）
api_router.include_router(
    user_content_api.router,
    prefix="",
    tags=["用户内容（新架构）"]
)

api_router.include_router(
    tag_admin.router,
    prefix="",
    tags=["标签管理"]
) 