"""
订阅相关的数据模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class PlatformType(str, Enum):
    """支持的平台类型"""
    BILIBILI = "bilibili"
    WEIBO = "weibo"
    TWITTER = "twitter"
    YOUTUBE = "youtube"


class ContentType(str, Enum):
    """内容类型"""
    VIDEO = "video"  # 视频
    DYNAMIC = "dynamic"  # 动态
    POST = "post"  # 帖子
    ARTICLE = "article"  # 文章


class SubscriptionTemplate(BaseModel):
    """订阅模板"""
    id: Optional[int] = None
    platform: PlatformType
    content_type: ContentType
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    url_template: str = Field(..., description="RSS URL模板")
    example_user_id: str = Field(..., description="示例用户ID")
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserSubscription(BaseModel):
    """用户订阅"""
    id: Optional[int] = None
    user_id: int = Field(..., description="用户ID")
    template_id: int = Field(..., description="订阅模板ID")
    target_user_id: str = Field(..., description="目标用户ID")
    custom_name: Optional[str] = Field(None, description="自定义名称")
    rss_url: str = Field(..., description="完整的RSS URL")
    is_active: bool = True
    last_update: Optional[datetime] = None
    created_at: Optional[datetime] = None


class SubscriptionCreateRequest(BaseModel):
    """创建订阅请求"""
    template_id: int = Field(..., description="订阅模板ID")
    target_user_id: str = Field(..., description="目标用户ID（如B站UID、微博UID等）")
    custom_name: Optional[str] = Field(None, description="自定义订阅名称")


class SubscriptionResponse(BaseModel):
    """订阅响应"""
    id: int
    platform: PlatformType
    content_type: ContentType
    template_name: str
    target_user_id: str
    custom_name: Optional[str]
    rss_url: str
    is_active: bool
    last_update: Optional[datetime]
    created_at: datetime


class SubscriptionListResponse(BaseModel):
    """订阅列表响应"""
    subscriptions: List[SubscriptionResponse]
    total: int
    page: int
    size: int


class RSSContent(BaseModel):
    """RSS内容"""
    id: Optional[int] = None
    subscription_id: int = Field(..., description="订阅ID")
    title: str = Field(..., description="内容标题")
    link: str = Field(..., description="内容链接")
    description: Optional[str] = Field(None, description="内容描述")
    pub_date: datetime = Field(..., description="发布时间")
    content_hash: str = Field(..., description="内容哈希值，用于去重")
    is_read: bool = False
    created_at: Optional[datetime] = None 