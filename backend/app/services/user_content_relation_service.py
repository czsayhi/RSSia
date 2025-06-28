#!/usr/bin/env python3
"""
用户内容关系管理服务
负责用户与内容的关系映射、生命周期管理和状态更新
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger

from app.core.database_manager import get_db_connection, get_db_transaction


class UserContentRelationService:
    """用户内容关系管理服务"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        self.db_path = db_path
        logger.info("🔧 用户内容关系服务初始化完成")
    
    async def create_relation(
        self, 
        user_id: int, 
        content_id: int, 
        subscription_id: int,
        expires_hours: int = 24
    ) -> int:
        """
        创建用户内容关系
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            subscription_id: 订阅ID
            expires_hours: 过期时间（小时）
            
        Returns:
            int: 关系ID
        """
        try:
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                
                # 计算过期时间
                expires_at = datetime.now() + timedelta(hours=expires_hours)
                
                # 检查关系是否已存在
                cursor.execute("""
                    SELECT id FROM user_content_relations 
                    WHERE user_id = ? AND content_id = ? AND subscription_id = ?
                """, (user_id, content_id, subscription_id))
                
                existing = cursor.fetchone()
                if existing:
                    # 更新过期时间
                    cursor.execute("""
                        UPDATE user_content_relations 
                        SET expires_at = ? 
                        WHERE id = ?
                    """, (expires_at, existing[0]))
                    
                    logger.debug(f"更新用户内容关系过期时间: relation_id={existing[0]}")
                    return existing[0]
                
                # 创建新关系
                cursor.execute("""
                    INSERT INTO user_content_relations (
                        user_id, content_id, subscription_id, expires_at, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                """, (user_id, content_id, subscription_id, expires_at, datetime.now()))
                
                relation_id = cursor.lastrowid
                
                logger.info(f"创建用户内容关系: user_id={user_id}, content_id={content_id}, relation_id={relation_id}")
                return relation_id
                
        except Exception as e:
            logger.error(f"创建用户内容关系失败: {e}")
            raise
    
    async def update_relation_status(
        self, 
        user_id: int, 
        content_id: int, 
        **updates
    ) -> bool:
        """
        更新用户内容关系状态
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            **updates: 更新字段（is_read, is_favorited, personal_tags等）
            
        Returns:
            bool: 更新是否成功
        """
        try:
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                
                # 构建更新SQL
                update_fields = []
                update_values = []
                
                if 'is_read' in updates:
                    update_fields.append('is_read = ?')
                    update_values.append(updates['is_read'])
                    if updates['is_read']:
                        update_fields.append('read_at = ?')
                        update_values.append(datetime.now())
                
                if 'is_favorited' in updates:
                    update_fields.append('is_favorited = ?')
                    update_values.append(updates['is_favorited'])
                
                if 'personal_tags' in updates:
                    update_fields.append('personal_tags = ?')
                    update_values.append(json.dumps(updates['personal_tags'], ensure_ascii=False))
                
                if not update_fields:
                    logger.warning("没有提供更新字段")
                    return False
                
                # 执行更新
                update_values.extend([user_id, content_id])
                cursor.execute(f"""
                    UPDATE user_content_relations 
                    SET {', '.join(update_fields)}
                    WHERE user_id = ? AND content_id = ? AND expires_at > datetime('now')
                """, update_values)
                
                updated_rows = cursor.rowcount
                
                if updated_rows > 0:
                    logger.info(f"更新用户内容状态: user_id={user_id}, content_id={content_id}, updates={updates}")
                    return True
                else:
                    logger.warning(f"未找到有效的用户内容关系: user_id={user_id}, content_id={content_id}")
                    return False
                
        except Exception as e:
            logger.error(f"更新用户内容关系状态失败: {e}")
            return False
    
    async def get_user_content_relation(
        self, 
        user_id: int, 
        content_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取用户内容关系信息
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            
        Returns:
            Optional[Dict]: 关系信息
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        id, subscription_id, is_read, is_favorited, 
                        read_at, personal_tags, expires_at, created_at
                    FROM user_content_relations 
                    WHERE user_id = ? AND content_id = ? AND expires_at > datetime('now')
                """, (user_id, content_id))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    'relation_id': row[0],
                    'subscription_id': row[1],
                    'is_read': bool(row[2]),
                    'is_favorited': bool(row[3]),
                    'read_at': row[4],
                    'personal_tags': json.loads(row[5]) if row[5] else [],
                    'expires_at': row[6],
                    'created_at': row[7]
                }
                
        except Exception as e:
            logger.error(f"获取用户内容关系失败: {e}")
            return None
    
    async def cleanup_expired_relations(self) -> int:
        """
        清理过期的用户内容关系
        
        Returns:
            int: 清理的关系数量
        """
        try:
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                
                # 删除过期关系
                cursor.execute("""
                    DELETE FROM user_content_relations 
                    WHERE expires_at < datetime('now')
                """)
                
                deleted_relations = cursor.rowcount
                
                # 清理孤立的共享内容
                cursor.execute("""
                    DELETE FROM shared_contents 
                    WHERE id NOT IN (
                        SELECT DISTINCT content_id 
                        FROM user_content_relations 
                        WHERE expires_at > datetime('now')
                    )
                """)
                
                deleted_contents = cursor.rowcount
                
                logger.info(f"清理过期数据: 关系={deleted_relations}, 内容={deleted_contents}")
                return deleted_relations
                
        except Exception as e:
            logger.error(f"清理过期关系失败: {e}")
            return 0
    
    async def get_user_content_stats(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户内容统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 统计信息
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 总内容数
                cursor.execute("""
                    SELECT COUNT(*) FROM user_content_relations 
                    WHERE user_id = ? AND expires_at > datetime('now')
                """, (user_id,))
                total_contents = cursor.fetchone()[0]
                
                # 已读数量
                cursor.execute("""
                    SELECT COUNT(*) FROM user_content_relations 
                    WHERE user_id = ? AND is_read = 1 AND expires_at > datetime('now')
                """, (user_id,))
                read_count = cursor.fetchone()[0]
                
                # 收藏数量
                cursor.execute("""
                    SELECT COUNT(*) FROM user_content_relations 
                    WHERE user_id = ? AND is_favorited = 1 AND expires_at > datetime('now')
                """, (user_id,))
                favorited_count = cursor.fetchone()[0]
                
                # 按平台统计
                cursor.execute("""
                    SELECT c.platform, COUNT(*) 
                    FROM user_content_relations r
                    JOIN shared_contents c ON r.content_id = c.id
                    WHERE r.user_id = ? AND r.expires_at > datetime('now')
                    GROUP BY c.platform
                """, (user_id,))
                platform_stats = dict(cursor.fetchall())
                
                # 按订阅源统计
                cursor.execute("""
                    SELECT us.custom_name, COUNT(*) 
                    FROM user_content_relations r
                    JOIN user_subscriptions us ON r.subscription_id = us.id
                    WHERE r.user_id = ? AND r.expires_at > datetime('now')
                    GROUP BY r.subscription_id, us.custom_name
                """, (user_id,))
                subscription_stats = dict(cursor.fetchall())
                
                return {
                    'total_contents': total_contents,
                    'read_count': read_count,
                    'unread_count': total_contents - read_count,
                    'favorited_count': favorited_count,
                    'read_percentage': round(read_count / max(total_contents, 1) * 100, 1),
                    'platform_distribution': platform_stats,
                    'subscription_distribution': subscription_stats
                }
                
        except Exception as e:
            logger.error(f"获取用户内容统计失败: {e}")
            return {}
    
    async def extend_content_expiry(
        self, 
        user_id: int, 
        content_id: int, 
        extend_hours: int = 24
    ) -> bool:
        """
        延长内容过期时间
        
        Args:
            user_id: 用户ID
            content_id: 内容ID
            extend_hours: 延长时间（小时）
            
        Returns:
            bool: 是否成功
        """
        try:
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                
                new_expires_at = datetime.now() + timedelta(hours=extend_hours)
                
                cursor.execute("""
                    UPDATE user_content_relations 
                    SET expires_at = ?
                    WHERE user_id = ? AND content_id = ?
                """, (new_expires_at, user_id, content_id))
                
                updated_rows = cursor.rowcount
                
                if updated_rows > 0:
                    logger.info(f"延长内容过期时间: user_id={user_id}, content_id={content_id}, hours={extend_hours}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"延长内容过期时间失败: {e}")
            return False
    
    async def batch_create_relations(
        self, 
        relations: List[Dict[str, Any]]
    ) -> List[int]:
        """
        批量创建用户内容关系
        
        Args:
            relations: 关系列表，每个元素包含 user_id, content_id, subscription_id
            
        Returns:
            List[int]: 创建的关系ID列表
        """
        try:
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                
                relation_ids = []
                
                for relation in relations:
                    expires_at = datetime.now() + timedelta(hours=relation.get('expires_hours', 24))
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO user_content_relations (
                            user_id, content_id, subscription_id, expires_at, created_at
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        relation['user_id'],
                        relation['content_id'],
                        relation['subscription_id'],
                        expires_at,
                        datetime.now()
                    ))
                    
                    relation_ids.append(cursor.lastrowid)
                
                logger.info(f"批量创建用户内容关系: {len(relation_ids)}条")
                return relation_ids
                
        except Exception as e:
            logger.error(f"批量创建用户内容关系失败: {e}")
            return []


# 创建全局实例
user_content_relation_service = UserContentRelationService() 