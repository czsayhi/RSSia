#!/usr/bin/env python3
"""
增强RSS内容处理服务
实现您提出的完整业务逻辑
"""

import re
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse, urljoin
import requests
import feedparser
from bs4 import BeautifulSoup
from loguru import logger

from app.models.content import (
    RSSContentItem, FeedInfo, MediaItem, ContentType, 
    PlatformType, ContentProcessingConfig
)


class EnhancedRSSService:
    """增强RSS内容处理服务"""
    
    def __init__(self, config: ContentProcessingConfig = None):
        self.config = config or ContentProcessingConfig()
        self.headers = {
            'User-Agent': 'RSS-Subscriber-Bot/1.0 (RSS智能订阅器)',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        # 视频时长服务暂时禁用，使用内置方法
        self.video_duration_service = None
    
    def fetch_and_process_content(self, rss_url: str, subscription_id: int, platform: PlatformType) -> List[RSSContentItem]:
        """
        主处理函数：拉取并处理RSS内容
        """
        logger.info(f"🚀 开始处理RSS内容: {rss_url}")
        
        try:
            # Step 1: 拉取原始RSS数据
            raw_content = self._fetch_raw_rss(rss_url)
            if not raw_content:
                return []
            
            # Step 2: 解析RSS Feed
            feed = feedparser.parse(raw_content)
            if not feed.entries:
                logger.warning("⚠️ RSS源没有条目")
                return []
            
            # Step 3: 提取Feed级别信息
            feed_info = self._extract_feed_info(feed, platform)
            
            # Step 4: 处理每个条目
            processed_items = []
            for entry in feed.entries:
                try:
                    item = self._process_single_entry(entry, feed_info, subscription_id)
                    if item:
                        processed_items.append(item)
                except Exception as e:
                    logger.error(f"❌ 处理单条条目失败: {e}")
                    continue
            
            logger.success(f"✅ RSS处理完成: {len(processed_items)}条内容")
            return processed_items
            
        except Exception as e:
            logger.error(f"❌ RSS处理失败: {rss_url} | {e}")
            return []
    
    def _fetch_raw_rss(self, rss_url: str) -> Optional[bytes]:
        """拉取RSS原始数据"""
        try:
            response = requests.get(rss_url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            logger.error(f"❌ 拉取RSS失败: {e}")
            return None
    
    def _extract_feed_info(self, feed: feedparser.FeedParserDict, platform: PlatformType) -> FeedInfo:
        """
        提取Feed级别信息 (订阅源信息)
        实现您的业务规则：
        - 订阅源标题、描述、主页地址
        - 清理 'Powered by RSSHub' 描述
        """
        feed_data = feed.feed
        
        # 提取基础信息
        title = feed_data.get('title', '未知订阅源')
        description = feed_data.get('description', '')
        link = feed_data.get('link', '')
        
        # 清理描述中的 'Powered by RSSHub'
        if description:
            description = re.sub(r'\s*-\s*Powered by RSSHub\s*$', '', description, flags=re.IGNORECASE)
            description = description.strip()
        
        # 处理最后更新时间
        last_build_date = None
        if hasattr(feed_data, 'updated_parsed') and feed_data.updated_parsed:
            last_build_date = datetime(*feed_data.updated_parsed[:6])
        
        return FeedInfo(
            feed_title=title,
            feed_description=description,
            feed_link=link,
            platform=platform,
            last_build_date=last_build_date
        )
    
    def _process_single_entry(self, entry: feedparser.util.FeedParserDict, feed_info: FeedInfo, subscription_id: int) -> Optional[RSSContentItem]:
        """
        处理单个RSS条目
        实现您的业务规则：
        - 提取标题、作者、发布时间、原文地址等
        - 处理富媒体内容
        - 判断内容类型
        - 作者信息兜底逻辑
        """
        
        # 基础信息提取
        title = self._clean_text(entry.get('title', '无标题'))
        original_link = entry.get('link', '')
        published_at = self._parse_publish_date(entry)
        
        # 作者信息处理 (含兜底逻辑)
        author = self._extract_author_with_fallback(entry, feed_info)
        
        # 内容描述处理
        description = self._extract_description(entry)
        description_text = self._extract_plain_text(description)
        
        # 媒体内容提取 (包含视频时长)
        media_items = self._extract_media_items(entry, description, original_link, feed_info.platform)
        cover_image = self._determine_cover_image(media_items, feed_info.platform)
        
        # 内容类型判断
        content_type = self._determine_content_type(entry, media_items, feed_info.platform)
        
        # 生成内容哈希
        content_hash = self._generate_content_hash(title, original_link, description)
        
        return RSSContentItem(
            subscription_id=subscription_id,
            content_hash=content_hash,
            feed_info=feed_info,
            
            # Item信息
            title=title,
            author=author,
            published_at=published_at,
            original_link=original_link,
            
            # 内容详情
            content_type=content_type,
            description=description,
            description_text=description_text,
            
            # 媒体
            media_items=media_items,
            cover_image=cover_image,
            
            # 系统字段
            created_at=datetime.now()
        )
    
    def _extract_author_with_fallback(self, entry: feedparser.util.FeedParserDict, feed_info: FeedInfo) -> Optional[str]:
        """
        作者信息提取 (统一兜底逻辑)
        业务规则：
        - 优先从item的author字段获取
        - 找不到时统一用订阅源标题兜底
        """
        
        # 1. 尝试从条目中提取作者
        author = entry.get('author', '').strip()
        if author:
            return author
        
        # 2. 使用订阅源标题兜底 (清理平台特定后缀)
        feed_title = feed_info.feed_title
        
        # 清理不同平台的标题后缀
        if feed_info.platform == PlatformType.WEIBO:
            feed_title = feed_title.replace('的微博', '')
        elif feed_info.platform == PlatformType.BILIBILI:
            feed_title = feed_title.replace(' 的 bilibili 空间', '')
            feed_title = feed_title.replace('的bilibili空间', '')
        
        return feed_title.strip() if feed_title.strip() else None
    
    def _determine_content_type(self, entry: feedparser.util.FeedParserDict, media_items: List[MediaItem], platform: PlatformType) -> ContentType:
        """
        内容类型判断 (简化为3种类型)
        业务规则：
        - VIDEO：包含视频内容，可播放
        - IMAGE_TEXT：没有视频，有图有文，外链也归为文本  
        - TEXT：没有视频没有图片
        """
        
        title = entry.get('title', '').lower()
        description = entry.get('description', '').lower()
        link = entry.get('link', '')
        
        # 1. 视频类型判断
        # B站视频链接
        if platform == PlatformType.BILIBILI and ('bilibili.com/video' in link or 'bv' in title):
            return ContentType.VIDEO
        
        # 媒体项中包含视频
        if any(item.type == 'video' for item in media_items):
            return ContentType.VIDEO
        
        # 2. 图文类型判断  
        # 媒体项中包含图片
        if any(item.type == 'image' for item in media_items):
            return ContentType.IMAGE_TEXT
        
        # 3. 默认纯文本类型
        return ContentType.TEXT
    
    def _extract_media_items(self, entry: feedparser.util.FeedParserDict, description: str, original_link: str, platform: PlatformType) -> List[MediaItem]:
        """提取媒体项目 (包含视频时长获取)"""
        media_items = []
        
        # 从description中提取图片和视频
        soup = BeautifulSoup(description, 'html.parser')
        
        # 提取图片
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                media_items.append(MediaItem(
                    url=src,
                    type='image',
                    description=img.get('alt', '')
                ))
        
        # 提取iframe视频
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src')
            if src:
                duration = self._get_video_duration(src, platform)
                media_items.append(MediaItem(
                    url=src,
                    type='video',
                    description='嵌入视频',
                    duration=duration
                ))
        
        # 提取audio标签
        for audio in soup.find_all('audio'):
            src = audio.get('src')
            if src:
                media_items.append(MediaItem(
                    url=src,
                    type='audio',
                    description='音频内容'
                ))
        
        # 特殊处理：如果是视频平台，从原始链接获取视频信息
        if platform == PlatformType.BILIBILI and 'bilibili.com/video' in original_link:
            duration = self._get_video_duration(original_link, platform)
            # 如果还没有添加视频媒体项，添加一个主视频项
            if not any(item.type == 'video' for item in media_items):
                media_items.append(MediaItem(
                    url=original_link,
                    type='video',
                    description=entry.get('title', '视频'),
                    duration=duration
                ))
            else:
                # 更新现有视频项的时长
                for item in media_items:
                    if item.type == 'video' and not item.duration:
                        item.duration = duration
        
        return media_items[:self.config.max_media_items]
    
    def _determine_cover_image(self, media_items: List[MediaItem], platform: PlatformType) -> Optional[str]:
        """
        确定封面图片
        实现您的业务规则：
        - 优先使用内容中的第一张图片
        - 没有图片时使用平台默认图片
        """
        
        # 查找第一张图片
        for item in media_items:
            if item.type == 'image':
                return item.url
        
        # 使用平台默认图片 (前端处理)
        return None
    
    def _contains_external_links(self, description: str) -> bool:
        """检查是否包含外链"""
        soup = BeautifulSoup(description, 'html.parser')
        links = soup.find_all('a', href=True)
        return len(links) > 0
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        # 清理HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 清理多余空白
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_plain_text(self, html_content: str) -> str:
        """从HTML中提取纯文本"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text().strip()
    
    def _extract_description(self, entry: feedparser.util.FeedParserDict) -> str:
        """提取描述内容"""
        # 优先级：content > summary > description  
        if hasattr(entry, 'content') and entry.content:
            return entry.content[0].value
        elif hasattr(entry, 'summary') and entry.summary:
            return entry.summary
        elif hasattr(entry, 'description') and entry.description:
            return entry.description
        return ""
    
    def _parse_publish_date(self, entry: feedparser.util.FeedParserDict) -> datetime:
        """解析发布时间"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])
        else:
            return datetime.now()
    
    def _generate_content_hash(self, title: str, link: str, description: str) -> str:
        """生成内容哈希用于去重"""
        import hashlib
        content = f"{title}|{link}|{description[:200]}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_video_duration(self, video_url: str, platform: PlatformType) -> Optional[int]:
        """
        获取视频时长（集成到媒体处理流程中）
        
        Args:
            video_url: 视频链接
            platform: 平台类型
            
        Returns:
            int: 视频时长（秒），获取失败返回None
        """
        try:
            if not video_url or platform != PlatformType.BILIBILI:
                return None
            
            # 提取B站视频ID
            import re
            bv_match = re.search(r'BV([A-Za-z0-9]+)', video_url)
            av_match = re.search(r'av(\d+)', video_url)
            
            if bv_match:
                bv_id = f"BV{bv_match.group(1)}"
                api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_id}"
            elif av_match:
                av_id = av_match.group(1)
                api_url = f"https://api.bilibili.com/x/web-interface/view?aid={av_id}"
            else:
                return None
            
            # 调用B站API
            response = requests.get(api_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('code') == 0:
                video_info = data.get('data', {})
                duration = video_info.get('duration')
                
                if duration and isinstance(duration, (int, float)):
                    logger.debug(f"✅ 获取B站视频时长: {duration}秒")
                    return int(duration)
            
            return None
            
        except Exception as e:
            logger.debug(f"⚠️ 获取视频时长失败: {e}")
            return None
    
    def format_duration(self, seconds: Optional[int]) -> str:
        """
        格式化视频时长为可读字符串
        
        Args:
            seconds: 时长秒数
            
        Returns:
            str: 格式化的时长字符串 (如: "1:23", "12:34", "1:23:45")
        """
        if seconds is None or seconds < 0:
            return "0:00"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}" 