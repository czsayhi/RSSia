"""
平台配置文件
实现platform到logo、主题色等资源的映射
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class PlatformConfig:
    """平台配置"""
    name: str
    display_name: str
    primary_color: str
    description: str


# 平台配置映射
PLATFORM_CONFIGS: Dict[str, PlatformConfig] = {
    "bilibili": PlatformConfig(
        name="bilibili",
        display_name="哔哩哔哩",
        primary_color="#00A1D6",
        description="哔哩哔哩视频内容"
    ),
    
    "weibo": PlatformConfig(
        name="weibo",
        display_name="微博",
        primary_color="#E6162D",
        description="微博动态内容"
    ),
    
    "jike": PlatformConfig(
        name="jike",
        display_name="即刻",
        primary_color="#FFD23F",
        description="即刻用户动态"
    ),
    
    "github": PlatformConfig(
        name="github",
        display_name="GitHub",
        primary_color="#181717",
        description="GitHub项目动态"
    ),
    
    "zhihu": PlatformConfig(
        name="zhihu",
        display_name="知乎",
        primary_color="#0084FF",
        description="知乎内容"
    ),
    
    "other": PlatformConfig(
        name="other",
        display_name="其他",
        primary_color="#FF6600",
        description="其他RSS源"
    )
}


def get_platform_config(platform: str) -> PlatformConfig:
    """
    根据平台标识获取平台配置
    
    Args:
        platform: 平台标识 (bilibili/weibo/jike等)
        
    Returns:
        PlatformConfig: 平台配置，找不到时返回默认配置
    """
    return PLATFORM_CONFIGS.get(platform.lower(), PLATFORM_CONFIGS["other"])


def get_platform_logo_name(platform: str) -> str:
    """
    获取平台logo文件名
    前端可以根据这个名称在public目录中查找对应的logo文件
    
    Args:
        platform: 平台标识
        
    Returns:
        str: logo文件名 (如: "bilibili.svg")
    """
    config = get_platform_config(platform)
    return f"{config.name}.svg"


def get_platform_display_name(platform: str) -> str:
    """
    获取平台显示名称
    
    Args:
        platform: 平台标识
        
    Returns:
        str: 平台显示名称
    """
    return get_platform_config(platform).display_name


def get_all_platforms() -> Dict[str, PlatformConfig]:
    """获取所有平台配置"""
    return PLATFORM_CONFIGS.copy()


# 前端logo映射函数
def get_subscription_logo_name(platform: str) -> str:
    """
    获取订阅源logo文件名
    前端根据platform在自己的public/logos目录中查找对应文件
    
    Args:
        platform: 平台标识
        
    Returns:
        str: logo文件名，前端可以拼接路径使用
    """
    return get_platform_logo_name(platform) 