"""
订阅配置文件
定义平台、订阅类型和具体模板的映射关系
"""

from typing import Dict, List
from app.models.subscription import PlatformType, SubscriptionType, ParameterConfig

# 平台信息配置
PLATFORM_CONFIG = {
    PlatformType.BILIBILI: {
        "name": "哔哩哔哩",
        "description": "B站视频和动态订阅",
        "supported_types": [SubscriptionType.USER]
    },
    PlatformType.WEIBO: {
        "name": "微博",
        "description": "微博用户和关键词订阅",
        "supported_types": [SubscriptionType.USER, SubscriptionType.KEYWORD]
    },
    PlatformType.JIKE: {
        "name": "即刻",
        "description": "即刻用户和圈子订阅",
        "supported_types": [SubscriptionType.USER, SubscriptionType.TOPIC]
    }
}

# 订阅类型展示名称
SUBSCRIPTION_TYPE_NAMES = {
    SubscriptionType.USER: "用户订阅",
    SubscriptionType.KEYWORD: "关键词订阅", 
    SubscriptionType.TOPIC: "圈子订阅",
    SubscriptionType.CHANNEL: "频道订阅",
    SubscriptionType.HASHTAG: "话题标签"
}

# 订阅模板配置
SUBSCRIPTION_TEMPLATES = [
    # B站用户订阅
    {
        "platform": PlatformType.BILIBILI,
        "subscription_type": SubscriptionType.USER,
        "name": "UP主视频",
        "description": "订阅B站UP主的最新视频投稿",
        "url_template": "https://rsshub.app/bilibili/user/video/{uid}",
        "parameters": [
            ParameterConfig(
                name="uid",
                display_name="UP主UID", 
                parameter_type="string",
                is_required=True,
                description="B站UP主的用户ID",
                placeholder="2267573",
                validation_regex=r"^[0-9]+$",
                multi_value=True
            )
        ]
    },
    {
        "platform": PlatformType.BILIBILI,
        "subscription_type": SubscriptionType.USER,
        "name": "UP主动态",
        "description": "订阅B站UP主的最新动态",
        "url_template": "https://rsshub.app/bilibili/user/dynamic/{uid}",
        "parameters": [
            ParameterConfig(
                name="uid",
                display_name="UP主UID",
                parameter_type="string", 
                is_required=True,
                description="B站UP主的用户ID",
                placeholder="297572288",
                validation_regex=r"^[0-9]+$",
                multi_value=True
            )
        ]
    },
    
    # 微博用户订阅
    {
        "platform": PlatformType.WEIBO,
        "subscription_type": SubscriptionType.USER,
        "name": "用户动态",
        "description": "订阅微博用户的最新动态",
        "url_template": "https://rsshub.app/weibo/user/{uid}",
        "parameters": [
            ParameterConfig(
                name="uid",
                display_name="用户UID",
                parameter_type="string",
                is_required=True,
                description="微博用户的UID",
                placeholder="1195230310",
                validation_regex=r"^[0-9]+$",
                multi_value=True
            )
        ]
    },
    
    # 微博关键词订阅
    {
        "platform": PlatformType.WEIBO,
        "subscription_type": SubscriptionType.KEYWORD,
        "name": "关键词搜索",
        "description": "订阅包含特定关键词的微博内容",
        "url_template": "https://rsshub.app/weibo/keyword/{keyword}",
        "parameters": [
            ParameterConfig(
                name="keyword",
                display_name="搜索关键词",
                parameter_type="string",
                is_required=True,
                description="要搜索的关键词",
                placeholder="人工智能",
                validation_regex=None,
                multi_value=True
            )
        ]
    },
    
    # 即刻用户订阅
    {
        "platform": PlatformType.JIKE,
        "subscription_type": SubscriptionType.USER,
        "name": "用户动态",
        "description": "订阅即刻用户的最新动态",
        "url_template": "https://rsshub.app/jike/user/{id}",
        "parameters": [
            ParameterConfig(
                name="id",
                display_name="用户ID",
                parameter_type="string",
                is_required=True,
                description="即刻用户ID",
                placeholder="82D23B32-CF36-4C59-AD6F-D05E3552CBF3",
                validation_regex=None,
                multi_value=True
            )
        ]
    },
    
    # 即刻圈子订阅
    {
        "platform": PlatformType.JIKE,
        "subscription_type": SubscriptionType.TOPIC,
        "name": "圈子动态",
        "description": "订阅即刻圈子的最新内容",
        "url_template": "https://rsshub.app/jike/topic/{id}",
        "parameters": [
            ParameterConfig(
                name="id",
                display_name="圈子ID",
                parameter_type="string",
                is_required=True,
                description="即刻圈子的ID",
                placeholder="556688fae4b00c57d9dd46ee",
                validation_regex=None,
                multi_value=True
            )
        ]
    }
]


def get_platform_info():
    """获取所有平台信息"""
    from app.models.subscription import PlatformInfo
    
    platforms = []
    for platform_type, config in PLATFORM_CONFIG.items():
        platforms.append(PlatformInfo(
            platform=platform_type,
            name=config["name"],
            description=config["description"],
            supported_subscription_types=config["supported_types"]
        ))
    return platforms


def get_subscription_types_for_platform(platform: PlatformType):
    """获取指定平台支持的订阅类型"""
    if platform not in PLATFORM_CONFIG:
        return []
    
    supported_types = PLATFORM_CONFIG[platform]["supported_types"]
    return [
        {"type": sub_type.value, "name": SUBSCRIPTION_TYPE_NAMES[sub_type]}
        for sub_type in supported_types
    ]


def get_templates_for_platform_and_type(platform: PlatformType, subscription_type: SubscriptionType):
    """获取指定平台和订阅类型的模板"""
    return [
        template for template in SUBSCRIPTION_TEMPLATES
        if template["platform"] == platform and template["subscription_type"] == subscription_type
    ]


def validate_subscription_parameters(template_id: int, parameters: Dict[str, str]) -> tuple[bool, str]:
    """验证订阅参数"""
    # 根据template_id找到对应的模板（临时使用索引作为ID）
    template = None
    if 1 <= template_id <= len(SUBSCRIPTION_TEMPLATES):
        template = SUBSCRIPTION_TEMPLATES[template_id - 1]
    
    if not template:
        return False, "订阅模板不存在"
    
    # 验证必填参数
    for param in template["parameters"]:
        if param.is_required and param.name not in parameters:
            return False, f"缺少必填参数: {param.display_name}"
        
        if param.name in parameters:
            value = parameters[param.name]
            
            # 验证正则表达式
            if param.validation_regex:
                import re
                if param.multi_value:
                    # 支持多个值，逗号分隔
                    values = [v.strip() for v in value.split(',')]
                    for v in values:
                        if not re.match(param.validation_regex, v):
                            return False, f"参数 {param.display_name} 格式不正确: {v}"
                else:
                    if not re.match(param.validation_regex, value):
                        return False, f"参数 {param.display_name} 格式不正确: {value}"
    
    return True, "验证通过" 