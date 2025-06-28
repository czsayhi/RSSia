#!/usr/bin/env python3
"""
RSS内容拉取和处理服务
负责RSS内容的拉取、解析、处理、存储等核心功能
v3.0: 简化架构，使用自建RSShub实例，移除复杂重试逻辑
v3.1: 增加内容时间范围控制，只获取指定天数内的内容
"""

import re
import time
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from loguru import logger

from .shared_content_service import SharedContentService


class RSSContentService:
    """RSS内容处理服务（v3.1 - 增加时间控制）"""
    
    def __init__(
        self, 
        timeout: int = 15, 
        rsshub_base_url: str = None,
        content_time_range_days: int = 30,
        test_mode: bool = False,
        test_limit: int = 1
    ):
        """
        初始化RSS内容服务
        
        Args:
            timeout: HTTP请求超时时间(秒) 
            rsshub_base_url: 自建RSShub实例地址
            content_time_range_days: 内容时间范围（天），只获取此范围内的内容
            test_mode: 测试模式，启用后将限制拉取内容数量
            test_limit: 测试模式下的最大内容数量
        """
        self.timeout = timeout
        
        # 简化的User-Agent
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        # 自建RSShub实例配置
        self.rsshub_base_url = rsshub_base_url or "http://rssia-hub:1200"
        
        # 内容时间范围控制
        self.content_time_range_days = content_time_range_days
        self.time_cutoff = datetime.now() - timedelta(days=content_time_range_days)
        
        # 测试模式配置
        self.test_mode = test_mode
        self.test_limit = test_limit
        
        # 简化的重试配置
        self.retry_config = {
            'max_retries': 2,          # 减少到2次重试
            'base_delay': 1,           # 1秒基础延迟
        }
        
        self.shared_content_service = SharedContentService()
        logger.info(
            f"🔧 RSS内容服务初始化完成（v3.1 - 时间控制版）- "
            f"RSShub: {self.rsshub_base_url}, "
            f"时间范围: {content_time_range_days}天, "
            f"测试模式: {'开启(限制'+str(test_limit)+'条)' if test_mode else '关闭'}"
        )
    
    async def fetch_and_store_rss_content(
        self, 
        rss_url: str, 
        subscription_id: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """
        拉取和存储RSS内容的主入口方法（简化版）
        
        Args:
            rss_url: RSS订阅URL
            subscription_id: 订阅ID
            user_id: 用户ID
            
        Returns:
            Dict: 处理结果统计
        """
        logger.info(f"🚀 开始拉取RSS内容: {rss_url}, user_id={user_id}")
        
        try:
            # 第1步：发送HTTP请求拉取RSS原始数据
            raw_content = self._fetch_raw_rss(rss_url)
            if not raw_content:
                return {'error': 'HTTP请求失败'}
            
            # 第2步：使用feedparser解析RSS/Atom内容
            feed_data = self._parse_rss_feed(raw_content)
            if not feed_data:
                return {'error': 'RSS解析失败'}
            
            # 第3步：提取并标准化内容数据
            rss_items = self._extract_and_standardize_entries(feed_data)
            
            # 第4步：使用新架构存储内容
            result = await self.shared_content_service.store_rss_content(
                rss_items=rss_items,
                subscription_id=subscription_id,
                user_id=user_id
            )
            
            # 🔥 第5步：AI预处理 - 基于AI字段是否为空
            need_ai_processing_ids = result.get('need_ai_processing_ids', [])
            if need_ai_processing_ids:
                ai_result = await self._trigger_ai_processing(need_ai_processing_ids, user_id, subscription_id)
                result['ai_processing'] = ai_result
            
            logger.success(
                f"✅ RSS内容处理完成: {rss_url} | "
                f"处理{result.get('total_processed', 0)}条，"
                f"新增{result.get('new_content', 0)}条，"
                f"复用{result.get('reused_content', 0)}条，"
                f"AI处理{result.get('ai_processing', {}).get('processed', 0)}条"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ RSS内容拉取失败: {rss_url} | 错误: {e}")
            return {'error': str(e)}
    
    async def _trigger_ai_processing(
        self, 
        need_ai_processing_ids: List[int], 
        user_id: int,
        subscription_id: int
    ) -> Dict[str, Any]:
        """
        第5步：触发AI预处理（基于AI字段是否为空）
        
        Args:
            need_ai_processing_ids: 需要AI处理的内容ID列表（新内容+缺少AI结果的旧内容）
            user_id: 用户ID
            subscription_id: 订阅ID
            
        Returns:
            Dict: AI处理结果统计
        """
        try:
            logger.info(f"🧠 开始AI预处理: {len(need_ai_processing_ids)}条需要处理的内容, user_id={user_id}")
            
            # 从数据库读取需要AI处理的内容
            db_contents = await self.shared_content_service.get_contents_by_ids(need_ai_processing_ids)
            if not db_contents:
                logger.warning("⚠️ 无法从数据库读取需要处理的内容")
                return {'processed': 0, 'success': 0, 'failed': 0}
            
            # 导入AI内容处理器
            from .ai_content_processor import ai_content_processor
            from ..models.content import RSSContent
            
            # 从数据库记录创建RSSContent对象（包含content_id信息）
            rss_content_objects = []
            for db_content in db_contents:
                try:
                    # 基于数据库记录创建RSSContent对象 - 包含所有标准字段
                    rss_content = RSSContent(
                        content_id=db_content['content_id'],  # 🔥 关键：包含content_id
                        subscription_id=subscription_id,
                        content_hash=db_content['content_hash'],
                        title=db_content['title'],
                        original_link=db_content['original_link'],
                        published_at=db_content['published_at'],
                        description=db_content['description'],
                        description_text=db_content['description_text'],
                        author=db_content['author'],
                        platform=db_content['platform'],
                        feed_title=db_content['feed_title'],
                        cover_image=db_content['cover_image'],
                        content_type=db_content['content_type']
                    )
                    rss_content_objects.append(rss_content)
                except Exception as e:
                    logger.warning(f"⚠️ 数据库内容转换失败，跳过: {db_content.get('title', 'Unknown')[:30]}... | 错误: {e}")
                    continue
            
            if not rss_content_objects:
                logger.warning("⚠️ 没有有效的内容可供AI处理")
                return {'processed': 0, 'success': 0, 'failed': 0}
            
            # 调用AI内容处理器
            processed_entries = await ai_content_processor.process_content_intelligence(rss_content_objects)
            
            # 统计处理结果
            result = {
                'processed': len(rss_content_objects),
                'success': len(processed_entries),
                'failed': len(rss_content_objects) - len(processed_entries),
                'success_rate': round(len(processed_entries) / len(rss_content_objects) * 100, 1) if rss_content_objects else 0
            }
            
            logger.success(f"✅ AI预处理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI预处理失败: {e}")
            # AI处理失败不影响主流程，返回失败统计
            return {
                'processed': len(need_ai_processing_ids),
                'success': 0,
                'failed': len(need_ai_processing_ids),
                'error': str(e)
            }
    
    def _fetch_raw_rss(self, rss_url: str) -> Optional[bytes]:
        """
        第1步：拉取RSS原始数据（v3.0 - 简化版本）
        移除多实例轮换，使用自建RSShub实例
        
        Args:
            rss_url: RSS URL
            
        Returns:
            Optional[bytes]: RSS原始内容字节数据
        """
        logger.debug(f"📡 开始拉取RSS: {rss_url}")
        
        # 构建完整URL
        if rss_url.startswith('http'):
            final_url = rss_url
        else:
            final_url = f"{self.rsshub_base_url}{rss_url}"
        
        # 简化的重试逻辑
        for attempt in range(self.retry_config['max_retries'] + 1):
            try:
                # 简化的请求头
                headers = {
                    'User-Agent': self.user_agent,
                    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
                }
                
                if attempt > 0:
                    time.sleep(self.retry_config['base_delay'] * attempt)
                
                logger.debug(f"🔄 尝试 {attempt + 1}/{self.retry_config['max_retries'] + 1}: {final_url}")
                
                response = requests.get(
                    final_url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                
                if response.content:
                    logger.success(f"✅ 成功获取RSS内容，大小: {len(response.content)} bytes")
                    return response.content
                else:
                    logger.warning("⚠️ 响应内容为空")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ 请求失败 (尝试{attempt + 1}): {e}")
                if attempt == self.retry_config['max_retries']:
                    logger.error(f"❌ 所有重试尝试失败: {final_url}")
                    
        return None
    
    def _parse_rss_feed(self, raw_content: bytes) -> Optional[feedparser.FeedParserDict]:
        """
        第2步：使用feedparser解析RSS/Atom内容
        
        Args:
            raw_content: RSS原始字节内容
            
        Returns:
            Optional[FeedParserDict]: feedparser解析结果
        """
        logger.debug("🔍 开始解析RSS内容...")
        
        try:
            # 使用feedparser解析RSS/Atom格式
            feed = feedparser.parse(raw_content)
            
            # 检查解析是否成功
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.warning(f"⚠️ RSS格式可能有问题: {feed.bozo_exception}")
            
            # 验证feed是否包含entries
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning("⚠️ RSS解析结果中没有条目数据")
                return None
            
            logger.debug(f"✅ RSS解析成功: 标题={feed.feed.get('title', '未知')}, 条目数={len(feed.entries)}")
            return feed
            
        except Exception as e:
            logger.error(f"❌ RSS解析异常: {e}")
            return None
    
    def _extract_and_standardize_entries(self, feed: feedparser.FeedParserDict) -> List[Dict[str, Any]]:
        """
        第3步：提取并标准化RSS条目数据（v3.1 - 增加时间过滤）
        
        Args:
            feed: feedparser解析结果
            
        Returns:
            List[Dict]: 标准化的RSS内容列表（只包含时间范围内的内容）
        """
        logger.debug(f"📝 开始提取RSS条目数据（时间范围: {self.content_time_range_days}天），共{len(feed.entries)}条")
        
        rss_items = []
        filtered_count = 0
        
        # 提取Feed级别信息
        feed_info = {
            'feed_title': self._clean_text(feed.feed.get('title', '未知订阅源')),
            'feed_description': self._clean_text(feed.feed.get('description', '')),
            'feed_link': feed.feed.get('link', ''),
            'feed_image_url': self._extract_feed_image(feed),
            'feed_last_build_date': self._parse_feed_date(feed),
            'platform': self._detect_platform_from_feed(feed)
        }
        
        for entry in feed.entries:
            try:
                # 处理发布时间
                published_at = self._parse_publish_date(entry)
                
                # 🔥 时间范围过滤：只保留指定天数内的内容
                if published_at < self.time_cutoff:
                    filtered_count += 1
                    logger.debug(f"⏰ 过滤旧内容: {entry.get('title', '')[:30]}... (发布时间: {published_at.strftime('%Y-%m-%d')})")
                    continue
                
                # 提取基础字段
                title = self._clean_text(entry.get('title', '无标题'))
                original_link = entry.get('link', '')
                
                # 提取和清洗描述内容
                description = self._extract_description(entry)
                description_text = self._clean_text(description)
                
                # 作者信息（带兜底逻辑）
                author = self._extract_author_with_fallback(entry, feed_info['feed_title'])
                
                # 内容类型判断
                content_type = self._determine_content_type(entry, description)
                
                # 提取媒体项
                media_items = self._extract_media_items(entry, description)
                cover_image = self._determine_cover_image(media_items)
                
                # 创建标准化内容项
                rss_item = {
                    'title': title,
                    'description': description,
                    'description_text': description_text,
                    'author': author,
                    'published_at': published_at,
                    'original_link': original_link,
                    'content_type': content_type,
                    'platform': feed_info['platform'],
                    'guid': entry.get('guid', ''),
                    'cover_image': cover_image,
                    'media_items': media_items,
                    
                    # Feed级别信息
                    'feed_title': feed_info['feed_title'],
                    'feed_description': feed_info['feed_description'],
                    'feed_link': feed_info['feed_link'],
                    'feed_image_url': feed_info['feed_image_url'],
                    'feed_last_build_date': feed_info['feed_last_build_date']
                }
                
                rss_items.append(rss_item)
                logger.debug(f"📄 提取条目: {title[:50]}... (发布时间: {published_at.strftime('%Y-%m-%d %H:%M')})")
                
                # 🧪 测试模式：限制内容数量
                if self.test_mode and len(rss_items) >= self.test_limit:
                    logger.info(f"🧪 测试模式：已达到限制数量({self.test_limit}条)，停止提取")
                    break
                
            except Exception as e:
                logger.warning(f"⚠️ 条目提取失败: {e}")
                continue
        
        logger.success(
            f"✅ 条目提取完成{'（测试模式）' if self.test_mode else '（时间控制版）'}: "
            f"保留{len(rss_items)}条，过滤{filtered_count}条旧内容"
        )
        return rss_items
    
    def _extract_author_with_fallback(self, entry: feedparser.util.FeedParserDict, feed_title: str) -> Optional[str]:
        """
        作者信息提取（带兜底逻辑）
        
        Args:
            entry: feedparser条目
            feed_title: 订阅源标题
            
        Returns:
            Optional[str]: 作者信息
        """
        # 1. 尝试从条目中提取作者
        author = entry.get('author', '').strip()
        if author:
            return author
        
        # 2. 使用订阅源标题兜底（清理平台特定后缀）
        if feed_title:
            # 清理不同平台的标题后缀
            clean_title = feed_title
            suffixes_to_remove = [
                '的微博', ' 的 bilibili 空间', '的bilibili空间',
                ' - 知乎', '的知乎专栏', ' | 少数派'
            ]
            
            for suffix in suffixes_to_remove:
                clean_title = clean_title.replace(suffix, '')
            
            return clean_title.strip() if clean_title.strip() else None
        
        return None
    
    def _determine_content_type(self, entry: feedparser.util.FeedParserDict, description: str) -> str:
        """
        判断内容类型
        
        Args:
            entry: feedparser条目
            description: 描述内容
            
        Returns:
            str: 内容类型
        """
        # 检查是否包含视频
        if any(keyword in description.lower() for keyword in ['video', '视频', 'bilibili.com/video']):
            return 'video'
        
        # 检查是否包含图片
        if any(keyword in description.lower() for keyword in ['<img', 'image', '图片']):
            return 'image_text'
        
        return 'text'
    
    def _extract_media_items(self, entry: feedparser.util.FeedParserDict, description: str) -> List[Dict[str, Any]]:
        """
        提取媒体项
        
        Args:
            entry: feedparser条目
            description: 描述内容
            
        Returns:
            List[Dict]: 媒体项列表
        """
        media_items = []
        
        try:
            # 从描述中提取图片
            soup = BeautifulSoup(description, 'html.parser')
            images = soup.find_all('img')
            
            for img in images:
                src = img.get('src', '')
                if src:
                    media_items.append({
                        'url': src,
                        'type': 'image',
                        'description': img.get('alt', ''),
                        'duration': None
                    })
            
            # 检查是否有视频链接
            if 'bilibili.com/video' in description:
                # 简单的视频检测
                media_items.append({
                    'url': entry.get('link', ''),
                    'type': 'video',
                    'description': '视频内容',
                    'duration': None  # 预留字段
                })
        
        except Exception as e:
            logger.debug(f"媒体项提取失败: {e}")
        
        return media_items
    
    def _determine_cover_image(self, media_items: List[Dict[str, Any]]) -> Optional[str]:
        """
        确定封面图片
        
        Args:
            media_items: 媒体项列表
            
        Returns:
            Optional[str]: 封面图片URL
        """
        for item in media_items:
            if item.get('type') == 'image' and item.get('url'):
                return item['url']
        return None
    
    def _extract_feed_image(self, feed: feedparser.FeedParserDict) -> Optional[str]:
        """提取Feed图像"""
        if hasattr(feed.feed, 'image') and feed.feed.image:
            return feed.feed.image.get('href', '')
        return None
    
    def _parse_feed_date(self, feed: feedparser.FeedParserDict) -> Optional[datetime]:
        """解析Feed构建时间"""
        if hasattr(feed.feed, 'updated_parsed') and feed.feed.updated_parsed:
            try:
                return datetime(*feed.feed.updated_parsed[:6])
            except (ValueError, TypeError):
                pass
        return None
    
    def _detect_platform_from_feed(self, feed: feedparser.FeedParserDict) -> str:
        """从Feed信息检测平台"""
        feed_link = feed.feed.get('link', '')
        feed_title = feed.feed.get('title', '')
        
        if 'bilibili' in feed_link.lower() or 'bilibili' in feed_title.lower():
            return 'bilibili'
        elif 'weibo' in feed_link.lower() or '微博' in feed_title:
            return 'weibo'
        elif 'github' in feed_link.lower():
            return 'github'
        elif 'zhihu' in feed_link.lower() or '知乎' in feed_title:
            return 'zhihu'
        
        return 'other'
    
    def _clean_text(self, text: str) -> str:
        """
        清洗文本内容：去除HTML标签、多余空白字符等
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清洗后的文本
        """
        if not text:
            return ""
        
        # 使用BeautifulSoup去除HTML标签
        clean_text = BeautifulSoup(text, 'html.parser').get_text()
        
        # 去除多余的空白字符
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def _parse_publish_date(self, entry: feedparser.util.FeedParserDict) -> datetime:
        """
        解析发布时间
        
        Args:
            entry: feedparser条目
            
        Returns:
            datetime: 解析后的时间对象
        """
        # 尝试从多个字段获取时间
        time_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        
        for field in time_fields:
            if hasattr(entry, field) and entry.get(field):
                try:
                    time_struct = entry[field]
                    return datetime(*time_struct[:6])
                except (ValueError, TypeError):
                    continue
        
        # 如果都失败，使用当前时间
        logger.debug("⚠️ 无法解析发布时间，使用当前时间")
        return datetime.now()
    
    def _extract_description(self, entry: feedparser.util.FeedParserDict) -> str:
        """
        提取和处理描述内容
        
        Args:
            entry: feedparser条目
            
        Returns:
            str: 处理后的描述内容
        """
        # 尝试从多个字段获取描述
        desc_fields = ['summary', 'description', 'content']
        
        for field in desc_fields:
            if hasattr(entry, field) and entry.get(field):
                description = entry[field]
                
                # 如果是列表格式（如content字段），取第一个
                if isinstance(description, list) and description:
                    description = description[0].get('value', '')
                
                if description:
                    return description
        
        return "无描述内容"
    

