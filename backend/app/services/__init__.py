#!/usr/bin/env python3
"""
服务模块初始化
导出所有服务实例，确保单例模式
"""

from .content_deduplication_service import ContentDeduplicationService
from .user_content_relation_service import UserContentRelationService
from .shared_content_service import SharedContentService
from .rss_content_service import RSSContentService

# 创建全局服务实例
content_dedup_service = ContentDeduplicationService()
user_content_relation_service = UserContentRelationService()
shared_content_service = SharedContentService()
rss_content_service = RSSContentService()

# 导出服务实例
__all__ = [
    'content_dedup_service',
    'user_content_relation_service', 
    'shared_content_service',
    'rss_content_service'
] 