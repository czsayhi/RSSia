#!/usr/bin/env python3
"""
RSS内容拉取和处理服务
负责RSS内容的拉取、解析、处理、存储等核心功能
已升级为使用新的共享内容存储架构
"""

import hashlib
import re
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from loguru import logger

from app.models.subscription import RSSContent
from .shared_content_service import SharedContentService


class RSSContentService:
    """RSS内容处理服务（已升级为新架构）"""
    
    def __init__(self, timeout: int = 15, user_agent: str = None):
        """
        初始化RSS内容服务
        
        Args:
            timeout: HTTP请求超时时间(秒)
            user_agent: 用户代理字符串
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            "RSS-Subscriber-Bot/1.0 "
            "(RSS智能订阅器; https://github.com/user/rss-subscriber)"
        )
        
        # 配置请求头
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache'
        }
        
        # 集成新的共享内容服务
        self.shared_service = SharedContentService()
        
        logger.info("🔧 RSS内容服务初始化完成（新架构）")
    
    async def fetch_and_store_rss_content(
        self, 
        rss_url: str, 
        subscription_id: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """
        拉取和存储RSS内容的主入口方法（新架构）
        
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
            result = await self.shared_service.store_rss_content(
                rss_items=rss_items,
                subscription_id=subscription_id,
                user_id=user_id
            )
            
            logger.success(
                f"✅ RSS内容处理完成: {rss_url} | "
                f"处理{result.get('total_processed', 0)}条，"
                f"新增{result.get('new_content', 0)}条，"
                f"复用{result.get('reused_content', 0)}条"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ RSS内容拉取失败: {rss_url} | 错误: {e}")
            return {'error': str(e)}
    
    def fetch_rss_content(self, rss_url: str, subscription_id: int) -> List[RSSContent]:
        """
        向后兼容方法：返回旧格式的RSSContent列表
        
        Args:
            rss_url: RSS订阅URL
            subscription_id: 订阅ID
            
        Returns:
            List[RSSContent]: 解析后的RSS内容列表（兼容格式）
        """
        logger.info(f"🚀 开始拉取RSS内容（兼容模式）: {rss_url}")
        
        try:
            # 第1步：发送HTTP请求拉取RSS原始数据
            raw_content = self._fetch_raw_rss(rss_url)
            if not raw_content:
                return []
            
            # 第2步：使用feedparser解析RSS/Atom内容
            feed_data = self._parse_rss_feed(raw_content)
            if not feed_data:
                return []
            
            # 第3步：提取并清洗内容数据（兼容格式）
            rss_entries = self._extract_entries_legacy(feed_data, subscription_id)
            
            # 第4步：内容去重和验证
            unique_entries = self._deduplicate_content(rss_entries)
            
            # 第5步：智能内容处理（摘要生成、标签提取）
            processed_entries = self._process_content_intelligence(unique_entries)
            
            logger.success(
                f"✅ RSS内容拉取完成（兼容模式）: {rss_url} | "
                f"原始{len(feed_data.entries)}条 → 处理后{len(processed_entries)}条"
            )
            
            return processed_entries
            
        except Exception as e:
            logger.error(f"❌ RSS内容拉取失败: {rss_url} | 错误: {e}")
            return []
    
    def _fetch_raw_rss(self, rss_url: str) -> Optional[bytes]:
        """
        第1步：拉取RSS原始数据
        
        Args:
            rss_url: RSS URL
            
        Returns:
            Optional[bytes]: RSS原始内容字节数据
        """
        logger.debug(f"📡 发送HTTP请求: {rss_url}")
        
        try:
            # 修复中文编码问题的headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Charset': 'utf-8',
                'Cache-Control': 'no-cache'
            }
            
            response = requests.get(
                rss_url, 
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # 检查HTTP状态码
            if response.status_code == 200:
                logger.debug(f"✅ HTTP请求成功: {response.status_code} | 内容长度: {len(response.content)}")
                return response.content
            else:
                logger.warning(f"⚠️ HTTP请求返回非200状态: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ HTTP请求超时: {rss_url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ HTTP连接错误: {rss_url}")
            return None
        except Exception as e:
            logger.error(f"❌ HTTP请求异常: {rss_url} | {e}")
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
        第3步：提取并标准化RSS条目数据（新架构）
        
        Args:
            feed: feedparser解析结果
            
        Returns:
            List[Dict]: 标准化的RSS内容列表
        """
        logger.debug(f"📝 开始提取RSS条目数据（新架构），共{len(feed.entries)}条")
        
        rss_items = []
        
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
                # 提取基础字段
                title = self._clean_text(entry.get('title', '无标题'))
                original_link = entry.get('link', '')
                
                # 处理发布时间
                published_at = self._parse_publish_date(entry)
                
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
                logger.debug(f"📄 提取条目: {title[:50]}...")
                
            except Exception as e:
                logger.warning(f"⚠️ 条目提取失败: {e}")
                continue
        
        logger.debug(f"✅ 条目提取完成（新架构）: {len(rss_items)}条")
        return rss_items
    
    def _extract_entries_legacy(self, feed: feedparser.FeedParserDict, subscription_id: int) -> List[RSSContent]:
        """
        第3步：提取并清洗RSS条目数据（兼容模式）
        
        Args:
            feed: feedparser解析结果
            subscription_id: 订阅ID
            
        Returns:
            List[RSSContent]: 提取的RSS内容列表
        """
        logger.debug(f"📝 开始提取RSS条目数据（兼容模式），共{len(feed.entries)}条")
        
        rss_entries = []
        
        for entry in feed.entries:
            try:
                # 提取基础字段
                title = self._clean_text(entry.get('title', '无标题'))
                link = entry.get('link', '')
                
                # 处理发布时间
                pub_date = self._parse_publish_date(entry)
                
                # 提取和清洗描述内容
                description = self._extract_description(entry)
                
                # 生成内容哈希用于去重
                content_hash = self._generate_content_hash(title, link, description)
                
                # 创建RSSContent对象
                rss_content = RSSContent(
                    subscription_id=subscription_id,
                    title=title,
                    link=link,
                    description=description,
                    pub_date=pub_date,
                    content_hash=content_hash,
                    is_read=False,
                    created_at=datetime.now()
                )
                
                rss_entries.append(rss_content)
                logger.debug(f"📄 提取条目: {title[:50]}...")
                
            except Exception as e:
                logger.warning(f"⚠️ 条目提取失败: {e}")
                continue
        
        logger.debug(f"✅ 条目提取完成（兼容模式）: {len(rss_entries)}条")
        return rss_entries
    
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
    
    def _generate_content_hash(self, title: str, link: str, description: str) -> str:
        """
        生成内容哈希值用于去重
        
        Args:
            title: 标题
            link: 链接
            description: 描述
            
        Returns:
            str: MD5哈希值
        """
        content = f"{title}{link}{description}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _deduplicate_content(self, entries: List[RSSContent]) -> List[RSSContent]:
        """
        第4步：内容去重
        
        Args:
            entries: RSS内容列表
            
        Returns:
            List[RSSContent]: 去重后的内容列表
        """
        seen_hashes = set()
        unique_entries = []
        
        for entry in entries:
            if entry.content_hash not in seen_hashes:
                seen_hashes.add(entry.content_hash)
                unique_entries.append(entry)
            else:
                logger.debug(f"🔄 重复内容已过滤: {entry.title[:50]}...")
        
        logger.debug(f"✅ 去重完成: {len(entries)}条 → {len(unique_entries)}条")
        return unique_entries
    
    def _process_content_intelligence(self, entries: List[RSSContent]) -> List[RSSContent]:
        """
        第5步：智能内容处理（摘要生成、标签提取）
        
        Args:
            entries: RSS内容列表
            
        Returns:
            List[RSSContent]: 智能处理后的内容列表
        """
        logger.debug(f"🧠 开始智能内容处理，共{len(entries)}条")
        
        processed_entries = []
        
        for entry in entries:
            try:
                # 生成智能摘要（目前使用规则，未来可接入LLM）
                entry.smart_summary = self._generate_summary(entry.title, entry.description)
                
                # 提取智能标签（目前使用规则，未来可接入LLM）
                entry.tags = self._extract_tags(entry.title, entry.description)
                
                # 识别平台信息
                entry.platform = self._detect_platform(entry.link)
                
                processed_entries.append(entry)
                
            except Exception as e:
                logger.warning(f"⚠️ 智能处理失败: {e}")
                # 即使智能处理失败，也保留原始内容
                processed_entries.append(entry)
        
        logger.debug(f"✅ 智能处理完成: {len(processed_entries)}条")
        return processed_entries
    
    def _generate_summary(self, title: str, description: str) -> str:
        """
        生成智能摘要（简化版规则，未来可接入LLM）
        
        Args:
            title: 标题
            description: 描述
            
        Returns:
            str: 生成的摘要
        """
        # 简化摘要生成逻辑
        if len(description) <= 100:
            return description
        
        # 取前80个字符作为摘要
        summary = description[:80].rstrip()
        
        # 避免在句子中间截断
        if not summary.endswith(('。', '！', '？', '.', '!', '?')):
            last_punct = max(
                summary.rfind('。'), summary.rfind('！'), 
                summary.rfind('？'), summary.rfind('.')
            )
            if last_punct > 30:  # 确保摘要不会太短
                summary = summary[:last_punct + 1]
        
        return summary + "..."
    
    def _extract_tags(self, title: str, description: str) -> List[str]:
        """
        提取智能标签（简化版规则，未来可接入LLM）
        
        Args:
            title: 标题
            description: 描述
            
        Returns:
            List[str]: 标签列表
        """
        tags = []
        content = f"{title} {description}".lower()
        
        # 技术相关标签
        tech_keywords = {
            'python': 'Python',
            'javascript': 'JavaScript', 
            'react': 'React',
            'vue': 'Vue',
            'docker': 'Docker',
            'kubernetes': 'Kubernetes',
            'ai': 'AI',
            '人工智能': 'AI',
            '机器学习': '机器学习',
            '深度学习': '深度学习'
        }
        
        for keyword, tag in tech_keywords.items():
            if keyword in content:
                tags.append(tag)
        
        # 平台相关标签
        if 'bilibili' in content or '哔哩哔哩' in content:
            tags.append('B站')
        if 'github' in content:
            tags.append('GitHub')
        if 'weibo' in content or '微博' in content:
            tags.append('微博')
        
        return list(set(tags))  # 去重
    
    def _detect_platform(self, link: str) -> str:
        """
        从链接检测平台信息
        
        Args:
            link: 内容链接
            
        Returns:
            str: 平台名称
        """
        if not link:
            return "unknown"
        
        domain = urlparse(link).netloc.lower()
        
        platform_mapping = {
            'bilibili.com': 'bilibili',
            'weibo.com': 'weibo', 
            'github.com': 'github',
            'juejin.cn': 'juejin',
            'zhihu.com': 'zhihu',
            'v2ex.com': 'v2ex'
        }
        
        for domain_key, platform in platform_mapping.items():
            if domain_key in domain:
                return platform
        
        return "other"


# 创建全局实例
rss_content_service = RSSContentService()


# 使用示例和测试方法
async def example_usage():
    """RSS内容服务使用示例（新架构）"""
    
    # 初始化服务
    rss_service = RSSContentService()
    
    # 测试RSS URL
    test_urls = [
        "https://rsshub.app/bilibili/user/video/2267573",  # B站视频
        "https://rsshub.app/weibo/user/1195230310",        # 微博动态
    ]
    
    for i, rss_url in enumerate(test_urls, 1):
        print(f"\n{'='*60}")
        print(f"测试RSS拉取 {i}: {rss_url}")
        print('='*60)
        
        # 使用新架构拉取和存储RSS内容
        result = await rss_service.fetch_and_store_rss_content(
            rss_url=rss_url, 
            subscription_id=i, 
            user_id=1
        )
        
        # 显示结果
        print(f"处理结果: {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage()) 