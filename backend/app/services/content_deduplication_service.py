#!/usr/bin/env python3
"""
内容去重服务
负责RSS内容的去重检测和哈希生成
"""

import hashlib
import re
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from loguru import logger

from ..core.database_manager import get_db_connection, get_db_transaction


class ContentDeduplicationService:
    """内容去重服务"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        self.db_path = db_path
        logger.info("🔧 内容去重服务初始化完成")
    
    def generate_content_hash(self, title: str, link: str) -> str:
        """
        生成内容哈希值用于去重
        
        Args:
            title: 内容标题
            link: 内容链接
            
        Returns:
            str: 32位哈希值
        """
        try:
            # 标准化标题（去除多余空白、统一大小写）
            normalized_title = self._normalize_text(title)
            
            # 标准化链接（去除查询参数等）
            normalized_link = self._normalize_link(link)
            
            # 生成哈希
            hash_content = f"{normalized_title}|{normalized_link}"
            hash_value = hashlib.sha256(hash_content.encode('utf-8')).hexdigest()[:32]
            
            logger.debug(f"生成内容哈希: {title[:30]}... -> {hash_value}")
            return hash_value
            
        except Exception as e:
            logger.error(f"生成内容哈希失败: {e}")
            # 降级方案：使用原始内容生成哈希
            fallback_content = f"{title}|{link}"
            return hashlib.md5(fallback_content.encode('utf-8')).hexdigest()[:32]
    
    async def check_content_exists(self, content_hash: str) -> Optional[int]:
        """
        检查内容是否已存在
        
        Args:
            content_hash: 内容哈希值
            
        Returns:
            Optional[int]: 如果存在返回content_id，否则返回None
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id FROM shared_contents 
                    WHERE content_hash = ?
                """, (content_hash,))
                
                result = cursor.fetchone()
                if result:
                    logger.debug(f"发现重复内容: hash={content_hash}, id={result[0]}")
                    return result[0]
                
                return None
                
        except Exception as e:
            logger.error(f"检查内容是否存在失败: {e}")
            return None
    
    async def find_or_create_content(self, content_data: Dict[str, Any]) -> Tuple[int, bool]:
        """
        查找或创建内容
        
        Args:
            content_data: 内容数据字典
            
        Returns:
            Tuple[int, bool]: (content_id, is_new)
        """
        try:
            # 生成内容哈希
            content_hash = self.generate_content_hash(
                content_data.get('title', ''),
                content_data.get('original_link', '')
            )
            
            # 检查是否已存在
            existing_id = await self.check_content_exists(content_hash)
            if existing_id:
                return existing_id, False
            
            # 创建新内容
            content_id = await self._create_shared_content(content_data, content_hash)
            return content_id, True
            
        except Exception as e:
            logger.error(f"查找或创建内容失败: {e}")
            raise
    
    async def _create_shared_content(self, content_data: Dict[str, Any], content_hash: str) -> int:
        """创建新的共享内容"""
        try:
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                
                # 准备插入数据
                insert_data = {
                    'content_hash': content_hash,
                    'title': content_data.get('title', ''),
                    'description': content_data.get('description', ''),
                    'description_text': content_data.get('description_text', ''),
                    'author': content_data.get('author', ''),
                    'published_at': content_data.get('published_at', datetime.now()),
                    'original_link': content_data.get('original_link', ''),
                    'content_type': content_data.get('content_type', 'text'),
                    'platform': content_data.get('platform', ''),
                    'guid': content_data.get('guid', ''),
                    'feed_title': content_data.get('feed_title', ''),
                    'feed_description': content_data.get('feed_description', ''),
                    'feed_link': content_data.get('feed_link', ''),
                    'feed_image_url': content_data.get('feed_image_url', ''),
                    'feed_last_build_date': content_data.get('feed_last_build_date'),
                    'cover_image': content_data.get('cover_image', ''),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # 执行插入
                cursor.execute("""
                    INSERT INTO shared_contents (
                        content_hash, title, description, description_text, author,
                        published_at, original_link, content_type, platform, guid,
                        feed_title, feed_description, feed_link, feed_image_url,
                        feed_last_build_date, cover_image, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    insert_data['content_hash'],
                    insert_data['title'],
                    insert_data['description'],
                    insert_data['description_text'],
                    insert_data['author'],
                    insert_data['published_at'],
                    insert_data['original_link'],
                    insert_data['content_type'],
                    insert_data['platform'],
                    insert_data['guid'],
                    insert_data['feed_title'],
                    insert_data['feed_description'],
                    insert_data['feed_link'],
                    insert_data['feed_image_url'],
                    insert_data['feed_last_build_date'],
                    insert_data['cover_image'],
                    insert_data['created_at'],
                    insert_data['updated_at']
                ))
                
                content_id = cursor.lastrowid
                
                logger.info(f"创建新共享内容: id={content_id}, title={insert_data['title'][:50]}...")
                return content_id
                
        except Exception as e:
            logger.error(f"创建共享内容失败: {e}")
            raise
    
    def _normalize_text(self, text: str) -> str:
        """标准化文本内容"""
        if not text:
            return ""
        
        # 去除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 去除多余空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 转换为小写（用于比较）
        text = text.lower()
        
        return text
    
    def _normalize_link(self, link: str) -> str:
        """标准化链接"""
        if not link:
            return ""
        
        # 去除常见的跟踪参数
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
        
        # 简单处理：去除查询参数中的跟踪参数
        if '?' in link:
            base_url, query_string = link.split('?', 1)
            
            # 过滤跟踪参数
            params = []
            for param in query_string.split('&'):
                if '=' in param:
                    key = param.split('=')[0]
                    if key not in tracking_params:
                        params.append(param)
            
            if params:
                link = f"{base_url}?{'&'.join(params)}"
            else:
                link = base_url
        
        return link.lower().strip()
    
    async def get_content_stats(self) -> Dict[str, Any]:
        """获取内容去重统计信息"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 统计共享内容数量
                cursor.execute("SELECT COUNT(*) FROM shared_contents")
                total_shared_contents = cursor.fetchone()[0]
                
                # 统计用户关系数量
                cursor.execute("SELECT COUNT(*) FROM user_content_relations WHERE expires_at > datetime('now')")
                active_relations = cursor.fetchone()[0]
                
                # 计算去重效率
                if total_shared_contents > 0:
                    dedup_ratio = active_relations / total_shared_contents
                else:
                    dedup_ratio = 0
                
                return {
                    'total_shared_contents': total_shared_contents,
                    'active_user_relations': active_relations,
                    'average_users_per_content': round(dedup_ratio, 2),
                    'storage_efficiency': f"{(1 - 1/max(dedup_ratio, 1)) * 100:.1f}%" if dedup_ratio > 1 else "0%"
                }
                
        except Exception as e:
            logger.error(f"获取内容统计失败: {e}")
            return {}


# 创建全局实例
content_dedup_service = ContentDeduplicationService() 