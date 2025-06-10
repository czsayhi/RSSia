#!/usr/bin/env python3
"""
RSS内容拉取和处理服务
负责RSS内容的拉取、解析、处理、存储等核心功能
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


class RSSContentService:
    """RSS内容处理服务"""
    
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
        
        logger.info("🔧 RSS内容服务初始化完成")
    
    def fetch_rss_content(self, rss_url: str, subscription_id: int) -> List[RSSContent]:
        """
        拉取和解析RSS内容的主入口方法
        
        Args:
            rss_url: RSS订阅URL
            subscription_id: 订阅ID
            
        Returns:
            List[RSSContent]: 解析后的RSS内容列表
        """
        logger.info(f"🚀 开始拉取RSS内容: {rss_url}")
        
        try:
            # 第1步：发送HTTP请求拉取RSS原始数据
            raw_content = self._fetch_raw_rss(rss_url)
            if not raw_content:
                return []
            
            # 第2步：使用feedparser解析RSS/Atom内容
            feed_data = self._parse_rss_feed(raw_content)
            if not feed_data:
                return []
            
            # 第3步：提取并清洗内容数据
            rss_entries = self._extract_entries(feed_data, subscription_id)
            
            # 第4步：内容去重和验证
            unique_entries = self._deduplicate_content(rss_entries)
            
            # 第5步：智能内容处理（摘要生成、标签提取）
            processed_entries = self._process_content_intelligence(unique_entries)
            
            logger.success(
                f"✅ RSS内容拉取完成: {rss_url} | "
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
            response = requests.get(
                rss_url, 
                headers=self.headers,
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
    
    def _extract_entries(self, feed: feedparser.FeedParserDict, subscription_id: int) -> List[RSSContent]:
        """
        第3步：提取并清洗RSS条目数据
        
        Args:
            feed: feedparser解析结果
            subscription_id: 订阅ID
            
        Returns:
            List[RSSContent]: 提取的RSS内容列表
        """
        logger.debug(f"📝 开始提取RSS条目数据，共{len(feed.entries)}条")
        
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
        
        logger.debug(f"✅ 条目提取完成: {len(rss_entries)}条")
        return rss_entries
    
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
                
                # 清洗文本
                clean_desc = self._clean_text(description)
                
                if clean_desc:
                    # 限制长度
                    return clean_desc[:500] + "..." if len(clean_desc) > 500 else clean_desc
        
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
        提取内容标签（简化版规则，未来可接入LLM）
        
        Args:
            title: 标题
            description: 描述
            
        Returns:
            List[str]: 提取的标签列表
        """
        content = f"{title} {description}".lower()
        tags = []
        
        # 游戏相关标签
        game_keywords = {
            '游戏': '游戏', '帕鲁': '幻兽帕鲁', '英雄联盟': '游戏',
            '王者荣耀': '游戏', '原神': '游戏', 'steam': '游戏'
        }
        
        # 娱乐相关标签
        entertainment_keywords = {
            '音乐': '音乐', '歌手': '音乐', '演唱会': '音乐',
            '电影': '娱乐', '综艺': '娱乐', '明星': '娱乐'
        }
        
        # 技术相关标签
        tech_keywords = {
            'python': '编程', 'javascript': '编程', 'ai': '人工智能',
            '人工智能': '人工智能', '机器学习': '技术', '开源': '技术'
        }
        
        # 合并所有关键词
        all_keywords = {**game_keywords, **entertainment_keywords, **tech_keywords}
        
        # 检查关键词匹配
        for keyword, tag in all_keywords.items():
            if keyword in content and tag not in tags:
                tags.append(tag)
        
        # 如果没有匹配到标签，使用默认标签
        if not tags:
            if 'bilibili' in content or 'b站' in content:
                tags.append('视频')
            elif 'weibo' in content or '微博' in content:
                tags.append('社交')
            else:
                tags.append('其他')
        
        # 限制标签数量
        return tags[:3]
    
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


# 使用示例和测试方法
async def example_usage():
    """RSS内容服务使用示例"""
    
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
        
        # 拉取和处理RSS内容
        contents = rss_service.fetch_rss_content(rss_url, subscription_id=i)
        
        # 显示结果
        for content in contents:
            print(f"📄 标题: {content.title}")
            print(f"🔗 链接: {content.link}")
            print(f"📝 摘要: {content.smart_summary}")
            print(f"🏷️  标签: {content.tags}")
            print(f"📱 平台: {content.platform}")
            print(f"📅 发布: {content.pub_date}")
            print("-" * 50)


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage()) 