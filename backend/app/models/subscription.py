"""
订阅相关的数据模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class PlatformType(str, Enum):
    """支持的平台类型"""
    BILIBILI = "bilibili"
    WEIBO = "weibo"
    JIKE = "jike"


class SubscriptionType(str, Enum):
    """订阅类型"""
    USER = "user"
    KEYWORD = "keyword"
    TOPIC = "topic"
    CHANNEL = "channel"
    HASHTAG = "hashtag"


class ContentType(str, Enum):
    """内容类型"""
    VIDEO = "video"  # 视频
    DYNAMIC = "dynamic"  # 动态
    POST = "post"  # 帖子
    ARTICLE = "article"  # 文章


class PlatformInfo(BaseModel):
    """平台信息"""
    platform: PlatformType
    name: str
    description: str
    supported_subscription_types: List[SubscriptionType]


class SubscriptionTypeInfo(BaseModel):
    """订阅类型信息"""
    subscription_type: SubscriptionType
    name: str
    description: str


class ParameterConfig(BaseModel):
    """参数配置"""
    name: str
    display_name: str
    description: str
    is_required: bool = True
    parameter_type: str = "string"  # string, number, boolean
    placeholder: Optional[str] = None
    validation_regex: Optional[str] = None
    multi_value: bool = False  # 是否支持多个值（逗号分隔）


class SubscriptionTemplate(BaseModel):
    """订阅模板"""
    id: Optional[int] = None
    platform: PlatformType
    subscription_type: SubscriptionType
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    url_template: str = Field(..., description="RSS URL模板")
    parameters: List[ParameterConfig] = Field(default_factory=list, description="参数配置")
    example_values: Optional[Dict[str, str]] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# 响应模型
class PlatformListResponse(BaseModel):
    """平台列表响应"""
    platforms: List[PlatformInfo]


class SubscriptionTypeListResponse(BaseModel):
    """订阅类型列表响应"""
    subscription_types: List[SubscriptionTypeInfo]


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    templates: List[SubscriptionTemplate]


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
    template_id: str = Field(..., description="订阅模板ID")
    parameters: Dict[str, str] = Field(..., description="订阅参数")
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


class SubscriptionSchedule(BaseModel):
    """订阅调度配置"""
    auto_fetch: bool = Field(True, description="自动获取开关")
    frequency: str = Field("daily", description="频率: daily|three_days|weekly|custom")
    custom_interval_minutes: int = Field(1440, description="自定义间隔(分钟)")
    preferred_time: str = Field("09:00", description="首选时间 HH:MM")
    timezone: str = Field("Asia/Shanghai", description="时区")
    last_fetch_at: Optional[datetime] = Field(None, description="上次获取时间")
    next_fetch_at: Optional[datetime] = Field(None, description="下次获取时间")


class SubscriptionScheduleRequest(BaseModel):
    """订阅调度配置请求"""
    auto_fetch: bool = Field(..., description="自动获取开关")
    frequency: str = Field(..., description="频率: daily|three_days|weekly|custom")
    custom_interval_minutes: Optional[int] = Field(1440, description="自定义间隔(分钟)")
    preferred_time: str = Field("09:00", description="首选时间 HH:MM")
    timezone: str = Field("Asia/Shanghai", description="时区") 