#!/usr/bin/env python3
"""
共享内容服务
整合内容去重和用户关系管理，提供完整的内容存储和查询功能
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from ..core.database_manager import get_db_connection, get_db_transaction
from .content_deduplication_service import ContentDeduplicationService
from .user_content_relation_service import UserContentRelationService


class SharedContentService:
    """共享内容服务"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        self.db_path = db_path
        self.dedup_service = ContentDeduplicationService(db_path)
        self.relation_service = UserContentRelationService(db_path)
        logger.info("🔧 共享内容服务初始化完成")
    
    async def store_rss_content(
        self, 
        rss_items: List[Dict[str, Any]], 
        subscription_id: int, 
        user_id: int
    ) -> Dict[str, Any]:
        """
        存储RSS内容到新架构
        
        Args:
            rss_items: RSS内容项列表
            subscription_id: 订阅ID
            user_id: 用户ID
            
        Returns:
            Dict: 处理结果统计
        """
        try:
            processed_count = 0
            new_content_count = 0
            reused_content_count = 0
            need_ai_processing_ids = []  # 🔥 改名：需要AI处理的内容ID（不管新旧）
            
            logger.info(f"开始处理RSS内容: {len(rss_items)}条, user_id={user_id}, subscription_id={subscription_id}")
            
            for item in rss_items:
                try:
                    # 1. 查找或创建共享内容
                    content_id, is_new = await self.dedup_service.find_or_create_content(item)
                    
                    # 2. 建立用户关系（24小时有效期）
                    relation_id = await self.relation_service.create_relation(
                        user_id=user_id,
                        content_id=content_id,
                        subscription_id=subscription_id,
                        expires_hours=24
                    )
                    
                    # 3. 处理媒体项
                    if item.get('media_items'):
                        await self._store_media_items(content_id, item['media_items'])
                    
                    # 4. 检查是否需要AI处理（直接检查AI字段是否为空）
                    if await self._needs_ai_processing(content_id):
                        need_ai_processing_ids.append(content_id)
                    
                    # 5. 统计
                    if is_new:
                        new_content_count += 1
                        logger.debug(f"创建新内容: content_id={content_id}, title={item.get('title', '')[:50]}...")
                    else:
                        reused_content_count += 1
                        logger.debug(f"复用现有内容: content_id={content_id}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"处理单条RSS内容失败: {e}, item={item.get('title', 'Unknown')}")
                    continue
            
            result = {
                'total_processed': processed_count,
                'new_content': new_content_count,
                'reused_content': reused_content_count,
                'deduplication_rate': round(reused_content_count / max(processed_count, 1) * 100, 1),
                'need_ai_processing_ids': need_ai_processing_ids  # 🔥 返回需要AI处理的内容ID列表
            }
            
            logger.success(f"RSS内容处理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"存储RSS内容失败: {e}")
            raise
    
    async def get_user_contents(
        self, 
        user_id: int, 
        **filters
    ) -> List[Dict[str, Any]]:
        """
        获取用户内容列表
        
        Args:
            user_id: 用户ID
            **filters: 筛选条件
            
        Returns:
            List[Dict]: 内容列表
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 基础查询
                query = """
                    SELECT 
                        c.id as content_id,
                        c.title,
                        c.author,
                        c.published_at,
                        c.original_link,
                        c.description,
                        c.description_text,
                        c.summary,
                        c.tags,
                        c.platform,
                        c.content_type,
                        c.cover_image,
                        c.feed_title,
                        r.subscription_id,
                        r.is_read,
                        r.is_favorited,
                        r.read_at,
                        r.personal_tags,
                        r.expires_at,
                        us.custom_name as subscription_name
                    FROM shared_contents c
                    JOIN user_content_relations r ON c.id = r.content_id
                    LEFT JOIN user_subscriptions us ON r.subscription_id = us.id
                    WHERE r.user_id = ? 
                      AND r.expires_at > datetime('now')
                """
                
                # 应用筛选条件
                params = [user_id]
                
                if filters.get('platform'):
                    query += " AND c.platform = ?"
                    params.append(filters['platform'])
                
                if filters.get('subscription_id'):
                    query += " AND r.subscription_id = ?"
                    params.append(filters['subscription_id'])
                
                if filters.get('is_read') is not None:
                    query += " AND r.is_read = ?"
                    params.append(filters['is_read'])
                
                if filters.get('is_favorited') is not None:
                    query += " AND r.is_favorited = ?"
                    params.append(filters['is_favorited'])
                
                if filters.get('content_type'):
                    query += " AND c.content_type = ?"
                    params.append(filters['content_type'])
                
                # 排序
                query += " ORDER BY c.published_at DESC"
                
                # 分页
                limit = filters.get('limit', 20)
                offset = filters.get('offset', 0)
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # 处理结果
                contents = []
                for row in rows:
                    # 获取媒体项
                    media_items = await self._get_content_media_items(row[0])
                    
                    content = {
                        'content_id': row[0],
                        'title': row[1],
                        'author': row[2],
                        'published_at': row[3],
                        'original_link': row[4],
                        'description': row[5],
                        'description_text': row[6],
                        'summary': row[7],
                        'tags': json.loads(row[8]) if row[8] else [],
                        'platform': row[9],
                        'content_type': row[10],
                        'cover_image': row[11],
                        'feed_title': row[12],
                        'subscription_id': row[13],
                        'is_read': bool(row[14]),
                        'is_favorited': bool(row[15]),
                        'read_at': row[16],
                        'personal_tags': json.loads(row[17]) if row[17] else [],
                        'expires_at': row[18],
                        'subscription_name': row[19],
                        'media_items': media_items
                    }
                    contents.append(content)
                
                logger.info(f"获取用户内容: user_id={user_id}, 返回{len(contents)}条")
                return contents
                
        except Exception as e:
            logger.error(f"获取用户内容失败: {e}")
            return []
    
    async def update_content_status(
        self, 
        user_id: int, 
        content_id: int, 
        **updates
    ) -> bool:
        """
        更新内容状态
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            **updates: 更新字段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            success = await self.relation_service.update_relation_status(
                user_id, content_id, **updates
            )
            
            if success:
                logger.info(f"更新内容状态成功: user_id={user_id}, content_id={content_id}, updates={updates}")
            
            return success
            
        except Exception as e:
            logger.error(f"更新内容状态失败: {e}")
            return False
    
    async def get_user_content_stats(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户内容统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 统计信息
        """
        try:
            # 获取基础统计
            stats = await self.relation_service.get_user_content_stats(user_id)
            
            # 添加系统级统计
            system_stats = await self.dedup_service.get_content_stats()
            stats.update({
                'system_stats': system_stats
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"获取用户内容统计失败: {e}")
            return {}
    
    async def _needs_ai_processing(self, content_id: int) -> bool:
        """
        检查内容是否需要AI处理（直接检查AI字段是否为空）
        
        Args:
            content_id: 内容ID
            
        Returns:
            bool: True表示需要AI处理，False表示已经处理过
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT summary, tags 
                    FROM shared_contents 
                    WHERE id = ?
                """, (content_id,))
                
                result = cursor.fetchone()
                if not result:
                    # 内容不存在，理论上不应该发生
                    return False
                
                summary, tags = result
                
                # 检查摘要和标签是否为空
                has_summary = summary and summary.strip()
                has_tags = tags and tags.strip()
                
                # 只要有一个AI字段为空，就需要处理
                needs_processing = not (has_summary and has_tags)
                
                if needs_processing:
                    logger.debug(f"内容需要AI处理: content_id={content_id}, summary={bool(has_summary)}, tags={bool(has_tags)}")
                
                return needs_processing
                
        except Exception as e:
            logger.error(f"检查AI处理需求失败: {e}")
            # 出错时保守处理，认为需要AI处理
            return True

    async def get_contents_by_ids(self, content_ids: List[int]) -> List[Dict[str, Any]]:
        """
        根据content_ids批量获取内容（用于AI预处理）
        
        Args:
            content_ids: 内容ID列表
            
        Returns:
            List[Dict]: 内容列表
        """
        if not content_ids:
            return []
            
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 构建查询语句
                placeholder = ','.join(['?'] * len(content_ids))
                query = f"""
                    SELECT 
                        id as content_id,
                        title,
                        author,
                        published_at,
                        original_link,
                        description,
                        description_text,
                        summary,
                        tags,
                        platform,
                        content_type,
                        cover_image,
                        feed_title,
                        content_hash
                    FROM shared_contents
                    WHERE id IN ({placeholder})
                    ORDER BY id DESC
                """
                
                cursor.execute(query, content_ids)
                rows = cursor.fetchall()
                
                # 处理结果
                contents = []
                for row in rows:
                    content = {
                        'content_id': row[0],
                        'title': row[1],
                        'author': row[2],
                        'published_at': row[3],
                        'original_link': row[4],
                        'description': row[5],
                        'description_text': row[6],
                        'summary': row[7],
                        'tags': json.loads(row[8]) if row[8] else [],
                        'platform': row[9],
                        'content_type': row[10],
                        'cover_image': row[11],
                        'feed_title': row[12],
                        'content_hash': row[13]
                    }
                    contents.append(content)
                
                logger.info(f"批量读取内容: {len(content_ids)}个ID, 返回{len(contents)}条内容")
                return contents
                
        except Exception as e:
            logger.error(f"批量读取内容失败: {e}")
            return []

    async def get_content_detail(self, content_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取内容详情
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            
        Returns:
            Optional[Dict]: 内容详情
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        c.*,
                        r.is_read,
                        r.is_favorited,
                        r.read_at,
                        r.personal_tags,
                        r.subscription_id,
                        us.custom_name as subscription_name
                    FROM shared_contents c
                    LEFT JOIN user_content_relations r ON c.id = r.content_id AND r.user_id = ?
                    LEFT JOIN user_subscriptions us ON r.subscription_id = us.id
                    WHERE c.id = ?
                """, (user_id, content_id))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # 获取媒体项
                media_items = await self._get_content_media_items(content_id)
                
                content = {
                    'content_id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'description_text': row[3],
                    'author': row[4],
                    'published_at': row[5],
                    'original_link': row[6],
                    'content_type': row[7],
                    'platform': row[8],
                    'content_hash': row[9],
                    'guid': row[10],
                    'feed_title': row[11],
                    'feed_description': row[12],
                    'feed_link': row[13],
                    'feed_image_url': row[14],
                    'feed_last_build_date': row[15],
                    'cover_image': row[16],
                    'summary': row[17],
                    'tags': json.loads(row[18]) if row[18] else [],
                    'created_at': row[19],
                    'updated_at': row[20],
                    'is_read': bool(row[21]) if row[21] is not None else False,
                    'is_favorited': bool(row[22]) if row[22] is not None else False,
                    'read_at': row[23],
                    'personal_tags': json.loads(row[24]) if row[24] else [],
                    'subscription_id': row[25],
                    'subscription_name': row[26],
                    'media_items': media_items
                }
                
                return content
                
        except Exception as e:
            logger.error(f"获取内容详情失败: {e}")
            return None
    
    async def _store_media_items(self, content_id: int, media_items: List[Dict[str, Any]]) -> None:
        """存储媒体项"""
        try:
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                
                for i, item in enumerate(media_items):
                    cursor.execute("""
                        INSERT INTO shared_content_media_items (
                            content_id, url, media_type, description, duration, sort_order
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        content_id,
                        item.get('url', ''),
                        item.get('type', 'image'),
                        item.get('description', ''),
                        item.get('duration'),
                        i
                    ))
                
                logger.debug(f"存储媒体项: content_id={content_id}, count={len(media_items)}")
                
        except Exception as e:
            logger.error(f"存储媒体项失败: {e}")
    
    async def _get_content_media_items(self, content_id: int) -> List[Dict[str, Any]]:
        """获取内容媒体项"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT url, media_type, description, duration
                    FROM shared_content_media_items
                    WHERE content_id = ?
                    ORDER BY sort_order
                """, (content_id,))
                
                rows = cursor.fetchall()
                media_items = []
                
                for row in rows:
                    media_item = {
                        'url': row[0],
                        'type': row[1],
                        'description': row[2],
                        'duration': row[3]
                    }
                    media_items.append(media_item)
                
                return media_items
                
        except Exception as e:
            logger.error(f"获取媒体项失败: {e}")
            return []
    
    async def cleanup_expired_content(self) -> Dict[str, int]:
        """清理过期内容"""
        try:
            # 清理过期关系和孤立内容
            deleted_relations = await self.relation_service.cleanup_expired_relations()
            
            return {
                'deleted_relations': deleted_relations,
                'message': '过期内容清理完成'
            }
            
        except Exception as e:
            logger.error(f"清理过期内容失败: {e}")
            return {'error': str(e)}
    
    async def search_user_contents(
        self, 
        user_id: int, 
        keyword: str, 
        **filters
    ) -> List[Dict[str, Any]]:
        """
        搜索用户内容
        
        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            **filters: 其他筛选条件
            
        Returns:
            List[Dict]: 搜索结果
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT 
                        c.id as content_id,
                        c.title,
                        c.author,
                        c.published_at,
                        c.original_link,
                        c.description_text,
                        c.platform,
                        c.content_type,
                        r.subscription_id,
                        r.is_read,
                        r.is_favorited,
                        us.custom_name as subscription_name
                    FROM shared_contents c
                    JOIN user_content_relations r ON c.id = r.content_id
                    LEFT JOIN user_subscriptions us ON r.subscription_id = us.id
                    WHERE r.user_id = ? 
                      AND r.expires_at > datetime('now')
                      AND (c.title LIKE ? OR c.description_text LIKE ? OR c.author LIKE ?)
                """
                
                params = [user_id, f'%{keyword}%', f'%{keyword}%', f'%{keyword}%']
                
                # 应用其他筛选条件
                if filters.get('platform'):
                    query += " AND c.platform = ?"
                    params.append(filters['platform'])
                
                query += " ORDER BY c.published_at DESC"
                
                # 分页
                limit = filters.get('limit', 20)
                offset = filters.get('offset', 0)
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                contents = []
                for row in rows:
                    content = {
                        'content_id': row[0],
                        'title': row[1],
                        'author': row[2],
                        'published_at': row[3],
                        'original_link': row[4],
                        'description_text': row[5],
                        'platform': row[6],
                        'content_type': row[7],
                        'subscription_id': row[8],
                        'is_read': bool(row[9]),
                        'is_favorited': bool(row[10]),
                        'subscription_name': row[11]
                    }
                    contents.append(content)
                
                logger.info(f"搜索用户内容: user_id={user_id}, keyword={keyword}, 结果{len(contents)}条")
                return contents
                
        except Exception as e:
            logger.error(f"搜索用户内容失败: {e}")
            return []


# 创建全局实例
shared_content_service = SharedContentService() 