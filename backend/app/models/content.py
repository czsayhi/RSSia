"""
RSS内容相关的数据模型
优化版本 - 支持完整的业务逻辑需求
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ContentType(str, Enum):
    """内容类型 (简化为3种类型)"""
    VIDEO = "video"           # 视频类：包含视频内容，可播放
    IMAGE_TEXT = "image_text" # 图文类：没有视频，有图有文，外链也归为文本
    TEXT = "text"            # 纯文本：没有视频没有图片


class PlatformType(str, Enum):
    """平台类型"""
    BILIBILI = "bilibili"
    WEIBO = "weibo"
    JIKE = "jike"


class FeedInfo(BaseModel):
    """订阅源信息 (从Feed头部提取)"""
    feed_title: str = Field(..., description="订阅源标题，从RSS Feed头部title字段提取")
    feed_description: str = Field(..., description="订阅源描述，清理'Powered by RSSHub'后的内容")
    feed_link: str = Field(..., description="订阅源主页地址，区别于内容原文地址")
    platform: PlatformType = Field(..., description="平台类型：bilibili/weibo/jike")
    last_build_date: Optional[datetime] = Field(None, description="Feed最后构建时间，从RSS头部提取")


class MediaItem(BaseModel):
    """媒体项 (图片、视频、音频等)"""
    url: str = Field(..., description="媒体URL地址")
    type: str = Field(..., description="媒体类型：image/video/audio")
    description: Optional[str] = Field(None, description="媒体描述信息")
    duration: Optional[int] = Field(None, description="视频时长（秒），仅视频类型使用")


class RSSContentItem(BaseModel):
    """完整的RSS内容项模型，包含所有业务字段"""
    
    # 基础标识字段
    id: Optional[int] = Field(None, description="内容ID（后端生成）")
    subscription_id: int = Field(..., description="订阅ID")
    content_hash: str = Field(..., description="内容哈希（去重用）")
    
    # 订阅源信息（Feed级别）
    feed_title: str = Field(..., description="订阅源标题")
    feed_description: Optional[str] = Field(None, description="订阅源描述")
    feed_link: Optional[str] = Field(None, description="订阅源主页")
    platform: Optional[str] = Field(None, description="平台标识")
    
    # 内容信息（Item级别）
    title: str = Field(..., description="内容标题")
    author: Optional[str] = Field(None, description="内容作者")
    pub_date: datetime = Field(..., description="发布时间")
    description: Optional[str] = Field(None, description="内容描述（HTML）")
    original_link: str = Field(..., description="内容原始链接")
    
    # 富媒体内容
    cover_image: Optional[str] = Field(None, description="封面图片URL")
    media_items: List[MediaItem] = Field(default_factory=list, description="媒体项列表")
    content_type: ContentType = Field(default=ContentType.TEXT, description="内容类型")
    
    # AI处理字段
    tags: List[str] = Field(default_factory=list, description="内容标签")
    summary: Optional[str] = Field(None, description="AI生成摘要")
    
    # 系统字段
    created_at: datetime = Field(default_factory=datetime.now, description="抓取时间")
    
    # 用户交互字段
    is_read: bool = Field(default=False, description="是否已读")
    is_favorite: bool = Field(default=False, description="是否收藏")


class ContentProcessingConfig(BaseModel):
    """内容处理配置"""
    # 文本处理
    max_title_length: int = 200
    max_description_length: int = 2000
    remove_html_tags: bool = True
    
    # 媒体处理
    extract_images: bool = True
    extract_videos: bool = True
    max_media_items: int = 10
    
    # AI处理 (预留)
    enable_ai_summary: bool = False
    enable_ai_tags: bool = False
    max_summary_length: int = 300


class ContentFilter(BaseModel):
    """内容筛选器"""
    platform: Optional[PlatformType] = None
    content_type: Optional[ContentType] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    is_read: Optional[bool] = None
    has_media: Optional[bool] = None


class ContentListResponse(BaseModel):
    """内容列表响应"""
    items: List[RSSContentItem]
    total: int
    page: int
    size: int
    has_next: bool
    filters_applied: ContentFilter


# 兼容现有代码的简化模型
class RSSContent(BaseModel):
    """RSS内容 (向后兼容) - 保持与现有代码的兼容性"""
    id: Optional[int] = Field(None, description="内容唯一标识，系统自动生成")
    subscription_id: int = Field(..., description="关联用户订阅表，实现数据隔离")
    title: str = Field(..., description="内容标题，从RSS item提取并清理HTML标签")
    link: str = Field(..., description="内容原文地址，向后兼容字段名")
    description: Optional[str] = Field(None, description="原始HTML描述内容")
    pub_date: datetime = Field(..., description="发布时间，从RSS item的pubDate字段解析")
    content_hash: str = Field(..., description="内容哈希值，用于去重，基于标题+链接+描述生成")
    is_read: bool = Field(False, description="是否已读状态")
    created_at: Optional[datetime] = Field(None, description="内容拉取时间，系统自动记录")
    
    # 扩展字段 (用于兼容现有的智能处理功能)
    smart_summary: Optional[str] = Field(None, description="智能摘要 (现有代码兼容)")
    tags: List[str] = Field(default_factory=list, description="内容标签 (现有代码兼容)")
    platform: Optional[str] = Field(None, description="平台信息 (现有代码兼容)") 