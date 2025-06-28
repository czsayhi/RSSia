#!/usr/bin/env python3
"""
服务层初始化模块
统一管理所有服务实例
v3.1: 使用简化版RSSContentService + 30天时间范围控制
"""

from .rss_content_service import RSSContentService
from .shared_content_service import SharedContentService
from .subscription_service import SubscriptionService
from .database_service import DatabaseService

# 创建统一的服务实例（避免重复实例化）
rss_content_service = RSSContentService(
    rsshub_base_url="http://rssia-hub:1200",
    content_time_range_days=30  # 只获取30天内的内容
)
shared_content_service = SharedContentService()
subscription_service = SubscriptionService()
database_service = DatabaseService()

__all__ = [
    'rss_content_service',
    'shared_content_service', 
    'subscription_service',
    'database_service',
    'RSSContentService',
    'SharedContentService',
    'SubscriptionService',
    'DatabaseService'
] 