#!/usr/bin/env python3
"""
内容处理工具类 - 简化兜底服务
提供AI处理失败时的基础内容生成规则
"""

import json
from typing import List, Dict
from urllib.parse import urlparse


class ContentProcessingUtils:
    """内容处理工具类 - 简化版兜底服务"""
    
    @staticmethod
    def generate_summary(title: str, description: str) -> str:
        """
        生成摘要（简化规则）
        
        Args:
            title: 标题
            description: 描述
            
        Returns:
            str: 摘要内容
        """
        if not title and not description:
            return "暂无摘要"
        
        # 优先使用标题作为摘要
        if title and len(title.strip()) > 10:
            return title.strip()
        
        # 其次使用描述的前100字符
        if description:
            cleaned_desc = description.strip()[:100]
            if cleaned_desc:
                return cleaned_desc + ("..." if len(description) > 100 else "")
        
        # 兜底返回标题
        return title.strip() if title else "暂无摘要"
    
    @staticmethod
    def generate_topics(title: str, description: str, platform: str = "") -> str:
        """
        生成主题（简化规则）
        
        Args:
            title: 标题
            description: 描述  
            platform: 平台信息
            
        Returns:
            str: 单个主题字符串
        """
        content = f"{title} {description}".lower()
        
        # 基于平台的简单主题分类
        if platform:
            platform_lower = platform.lower()
            if 'bilibili' in platform_lower or 'b站' in platform_lower:
                return '娱乐'
            elif 'github' in platform_lower:
                return '科技' 
            elif 'weibo' in platform_lower or '微博' in platform_lower:
                return '生活'
        
        # 基于内容的简单关键词匹配
        if any(word in content for word in ['python', 'javascript', 'ai', '人工智能', '编程', '代码', '技术']):
            return '科技'
        elif any(word in content for word in ['电影', '音乐', '游戏', '娱乐']):
            return '娱乐'  
        elif any(word in content for word in ['股票', '投资', '经济', '金融']):
            return '财经'
        elif any(word in content for word in ['健康', '美食', '旅游', '生活']):
            return '生活'
        
        # 默认主题
        return '其他'
    
    @staticmethod
    def generate_tags(title: str, description: str, platform: str = "") -> List[str]:
        """
        生成标签（简化规则）
        
        Args:
            title: 标题
            description: 描述
            platform: 平台信息
            
        Returns:
            List[str]: 标签列表
        """
        tags = []
        content = f"{title} {description}".lower()
        
        # 平台标签
        if platform:
            platform_lower = platform.lower()
            if 'bilibili' in platform_lower:
                tags.append('B站')
            elif 'github' in platform_lower:
                tags.append('GitHub')
            elif 'weibo' in platform_lower:
                tags.append('微博')
        
        # 简单技术标签
        tech_keywords = {
            'python': 'Python',
            'javascript': 'JavaScript', 
            'ai': 'AI',
            '人工智能': 'AI',
            '编程': '编程',
            '代码': '编程'
        }
        
        for keyword, tag in tech_keywords.items():
            if keyword in content and tag not in tags:
                tags.append(tag)
        
        # 限制标签数量
        return tags[:5] if tags else ['其他']
    
    @staticmethod
    def detect_platform(link: str) -> str:
        """
        从链接检测平台信息
        
        Args:
            link: 内容链接
            
        Returns:
            str: 平台名称
        """
        if not link:
            return "other"
        
        try:
            domain = urlparse(link).netloc.lower()
            
            if 'bilibili.com' in domain:
                return 'bilibili'
            elif 'weibo.com' in domain:
                return 'weibo'
            elif 'github.com' in domain:
                return 'github'
            elif 'zhihu.com' in domain:
                return 'zhihu'
            
            return "other"
        except:
            return "other"
    
    @staticmethod
    def process_content_with_fallback(
        title: str, 
        description: str, 
        description_text: str = "", 
        author: str = "",
        platform: str = "", 
        feed_title: str = "",
        link: str = ""
    ) -> Dict[str, str]:
        """
        完整的内容处理（简化兜底版本）- 新格式输出
        
        Args:
            title: 标题
            description: HTML描述
            description_text: 纯文本描述
            author: 作者
            platform: 平台
            feed_title: 订阅源标题
            link: 内容链接
            
        Returns:
            Dict[str, str]: 包含summary、topics、tags字段的结果（新格式）
        """
        try:
            # 使用最佳描述文本
            best_description = description_text or description or ""
            
            # 自动检测平台（如果未提供）
            if not platform and link:
                platform = ContentProcessingUtils.detect_platform(link)
            
            # 1. 生成摘要
            summary = ContentProcessingUtils.generate_summary(title, best_description)
            
            # 2. 生成主题（单个字符串）
            topics = ContentProcessingUtils.generate_topics(title, best_description, platform)
            
            # 3. 生成标签（数组）
            tags_list = ContentProcessingUtils.generate_tags(title, best_description, platform)
            
            # 4. 返回新格式（字段分离）
            return {
                "summary": summary,
                "topics": topics,  # 单个主题字符串
                "tags": json.dumps(tags_list, ensure_ascii=False)  # 纯标签数组JSON
            }
            
        except Exception as e:
            # 最终兜底：返回基础内容
            return {
                "summary": title if title else "处理失败",
                "topics": "其他",
                "tags": json.dumps(["其他"], ensure_ascii=False)
            } 