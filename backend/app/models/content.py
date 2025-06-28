"""
RSS内容相关的数据模型
优化版本 - 支持完整的业务逻辑需求
"""
import json
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
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
    content_id: Optional[int] = Field(None, description="内容ID（后端生成）")
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
    """RSS内容 (向后兼容) - 修复字段不一致问题，添加缺失字段"""
    # 基础标识字段
    content_id: Optional[int] = Field(None, description="内容唯一标识，系统自动生成")
    subscription_id: int = Field(..., description="关联用户订阅表，实现数据隔离")
    content_hash: str = Field(..., description="内容哈希值，用于去重，基于标题+链接+描述生成")
    
    # 内容字段
    title: str = Field(..., description="内容标题，从RSS item提取并清理HTML标签")
    description: Optional[str] = Field(None, description="原始HTML描述内容")
    description_text: Optional[str] = Field(None, description="纯文本描述内容，从HTML提取的纯文本版本")
    author: Optional[str] = Field(None, description="内容作者，优先从item提取，找不到用feed_title兜底")
    
    # 链接和时间字段 (统一命名)
    original_link: str = Field(..., description="内容原文地址，与数据库字段统一")
    link: Optional[str] = Field(None, description="内容原文地址，向后兼容字段名，与original_link保持一致")
    published_at: datetime = Field(..., description="发布时间，与数据库字段统一")
    pub_date: Optional[datetime] = Field(None, description="发布时间，向后兼容字段名，与published_at保持一致")
    
    # Feed级别信息（订阅源信息）
    feed_title: Optional[str] = Field(None, description="订阅源标题，从RSS Feed头部title字段提取")
    feed_description: Optional[str] = Field(None, description="订阅源描述")
    feed_link: Optional[str] = Field(None, description="订阅源主页地址，区别于内容原文地址")
    feed_image_url: Optional[str] = Field(None, description="订阅源头像URL")
    feed_last_build_date: Optional[datetime] = Field(None, description="Feed最后构建时间")
    
    # 内容分类和富媒体
    content_type: Optional[str] = Field(None, description="内容类型：video/image_text/text")
    platform: Optional[str] = Field(None, description="平台信息：bilibili/weibo/jike等")
    cover_image: Optional[str] = Field(None, description="封面图片URL")
    guid: Optional[str] = Field(None, description="全局唯一标识符")
    
    # AI处理字段（字段分离优化）
    summary: Optional[str] = Field(None, description="AI生成摘要，与数据库字段统一")
    smart_summary: Optional[str] = Field(None, description="智能摘要，向后兼容字段名，与summary保持一致")
    topics: Optional[str] = Field(None, description="内容主题，单个主题字符串")
    tags: Union[List[str], str] = Field(default_factory=list, description="内容标签，支持List[str]或JSON字符串")
    
    # 用户交互字段
    is_read: bool = Field(False, description="是否已读状态")
    is_favorited: Optional[bool] = Field(None, description="是否收藏状态")
    read_at: Optional[datetime] = Field(None, description="阅读时间戳")
    personal_tags: Optional[List[str]] = Field(default_factory=list, description="用户个人标签")
    
    # 系统字段
    created_at: Optional[datetime] = Field(None, description="内容拉取时间，系统自动记录")
    updated_at: Optional[datetime] = Field(None, description="内容更新时间")
    
    # 关系字段（用户内容关系）
    subscription_name: Optional[str] = Field(None, description="订阅名称")
    expires_at: Optional[datetime] = Field(None, description="内容过期时间")
    
    @validator('tags', pre=True)
    def parse_tags(cls, v):
        """处理tags字段的类型转换：JSON字符串 → List[str]（字段分离版本）"""
        if isinstance(v, str):
            try:
                # 尝试解析JSON字符串
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    # 新格式：纯标签数组 ["标签1", "标签2", "标签3"]
                    return parsed
                elif isinstance(parsed, dict):
                    # 旧格式兼容：{"topics": [...], "entities": [...]} 
                    # 字段分离后只返回entities作为tags
                    entities = parsed.get('entities', [])
                    return entities
                else:
                    return []
            except (json.JSONDecodeError, TypeError):
                # 如果解析失败，返回空列表
                return []
        elif isinstance(v, list):
            # 如果已经是列表，直接返回
            return v
        else:
            # 其他类型返回空列表
            return []
    
    def __init__(self, **data):
        """初始化时自动同步兼容字段"""
        super().__init__(**data)
        
        # 自动同步 original_link 和 link
        if self.original_link and not self.link:
            self.link = self.original_link
        elif self.link and not self.original_link:
            self.original_link = self.link
            
        # 自动同步 published_at 和 pub_date
        if self.published_at and not self.pub_date:
            self.pub_date = self.published_at
        elif self.pub_date and not self.published_at:
            self.published_at = self.pub_date
            
        # 自动同步 summary 和 smart_summary
        if self.summary and not self.smart_summary:
            self.smart_summary = self.summary
        elif self.smart_summary and not self.summary:
            self.summary = self.smart_summary


class ContentDataConverter:
    """内容数据转换工具类 - 处理数据库数据与模型之间的转换"""
    
    @staticmethod
    def dict_to_rss_content(data: Dict[str, Any]) -> RSSContent:
        """将字典数据转换为RSSContent模型"""
        # 处理tags字段的JSON转换
        if 'tags' in data and isinstance(data['tags'], str):
            try:
                parsed_tags = json.loads(data['tags'])
                if isinstance(parsed_tags, dict):
                    # 合并topics和entities
                    topics = parsed_tags.get('topics', [])
                    entities = parsed_tags.get('entities', [])
                    data['tags'] = topics + entities
                elif isinstance(parsed_tags, list):
                    data['tags'] = parsed_tags
            except (json.JSONDecodeError, TypeError):
                data['tags'] = []
        
        # 处理时间字段的统一
        if 'published_at' in data and 'pub_date' not in data:
            data['pub_date'] = data['published_at']
        if 'original_link' in data and 'link' not in data:
            data['link'] = data['original_link']
        if 'summary' in data and 'smart_summary' not in data:
            data['smart_summary'] = data['summary']
            
        return RSSContent(**data)
    
    @staticmethod
    def rss_content_to_dict(content: RSSContent) -> Dict[str, Any]:
        """将RSSContent模型转换为字典数据（用于数据库存储）"""
        data = content.dict()
        
        # 处理tags字段的JSON转换
        if 'tags' in data and isinstance(data['tags'], list):
            # 将List[str]转换为JSON格式
            tags_json = {
                "topics": data['tags'][:3] if data['tags'] else [],  # 前3个作为主题
                "entities": data['tags'][3:] if len(data['tags']) > 3 else []  # 其余作为实体
            }
            data['tags'] = json.dumps(tags_json, ensure_ascii=False)
        
        # 确保使用数据库字段名
        if 'link' in data:
            data['original_link'] = data['link']
        if 'pub_date' in data:
            data['published_at'] = data['pub_date']
        if 'smart_summary' in data:
            data['summary'] = data['smart_summary']
            
        return data
    
    @staticmethod
    def parse_tags_from_json(tags_json: str) -> List[str]:
        """从JSON字符串解析标签列表"""
        if not tags_json:
            return []
            
        try:
            parsed = json.loads(tags_json)
            if isinstance(parsed, dict):
                topics = parsed.get('topics', [])
                entities = parsed.get('entities', [])
                return topics + entities
            elif isinstance(parsed, list):
                return parsed
            else:
                return []
        except (json.JSONDecodeError, TypeError):
            return []
    
    @staticmethod
    def tags_to_json(tags: List[str]) -> str:
        """将标签列表转换为JSON字符串"""
        if not tags:
            return json.dumps({"topics": [], "entities": []}, ensure_ascii=False)
        
        # 简单策略：前3个作为主题，其余作为实体
        topics = tags[:3] if tags else []
        entities = tags[3:] if len(tags) > 3 else []
        
        tags_json = {
            "topics": topics,
            "entities": entities
        }
        
        return json.dumps(tags_json, ensure_ascii=False) 