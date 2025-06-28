"""
用户标签缓存服务
实现标签计算、缓存管理和定时更新功能
"""

import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

from ..core.database_manager import get_db_connection, get_db_transaction


@dataclass
class TagCacheEntry:
    """标签缓存条目"""
    user_id: int
    tags: List[Dict[str, any]]  # [{"name": "科技", "count": 45}, ...]
    updated_at: datetime
    content_count: int  # 用于判断是否需要重新计算


class TagCacheService:
    """标签缓存服务"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        self.db_path = db_path
        self._init_cache_table()
    
    def _init_cache_table(self):
        """初始化标签缓存表"""
        # 注意：这里保留原有的sqlite3.connect()，因为数据库管理器可能还未初始化
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建用户标签缓存表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_tag_cache (
                    user_id INTEGER PRIMARY KEY,
                    tags_json TEXT NOT NULL,
                    content_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_tag_cache_updated ON user_tag_cache (last_updated)")
            
            conn.commit()
    
    def get_user_tags_from_cache(self, user_id: int) -> Optional[List[Dict[str, any]]]:
        """从缓存获取用户标签"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT tags_json, last_updated, content_count
                    FROM user_tag_cache 
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                tags_json, last_updated, cached_content_count = row
                
                # 检查缓存是否过期（30分钟）
                cache_time = datetime.fromisoformat(last_updated)
                if datetime.now() - cache_time > timedelta(minutes=30):
                    logger.info(f"用户{user_id}标签缓存已过期")
                    return None
                
                # 检查内容是否有更新
                current_content_count = self._get_user_content_count(cursor, user_id)
                if current_content_count != cached_content_count:
                    logger.info(f"用户{user_id}内容有更新，缓存失效")
                    return None
                
                return json.loads(tags_json)
                
        except Exception as e:
            logger.error(f"从缓存获取用户标签失败: {e}")
            return None
    
    def update_user_tags_cache(self, user_id: int) -> List[Dict[str, any]]:
        """更新用户标签缓存"""
        try:
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                
                # 计算用户标签
                tags = self._calculate_user_tags(cursor, user_id)
                content_count = self._get_user_content_count(cursor, user_id)
                
                # 更新缓存
                cursor.execute("""
                    INSERT OR REPLACE INTO user_tag_cache 
                    (user_id, tags_json, content_count, last_updated)
                    VALUES (?, ?, ?, ?)
                """, (
                    user_id, 
                    json.dumps(tags, ensure_ascii=False),
                    content_count,
                    datetime.now().isoformat()
                ))
                
                logger.info(f"用户{user_id}标签缓存已更新: {len(tags)}个标签")
                return tags
                
        except Exception as e:
            logger.error(f"更新用户标签缓存失败: {e}")
            return []
    
    def get_user_tags_with_cache(self, user_id: int) -> List[Dict[str, any]]:
        """获取用户标签（优先使用缓存）"""
        # 尝试从缓存获取
        cached_tags = self.get_user_tags_from_cache(user_id)
        if cached_tags is not None:
            return cached_tags
        
        # 缓存失效，重新计算
        return self.update_user_tags_cache(user_id)
    
    def _calculate_user_tags(self, cursor, user_id: int) -> List[Dict[str, any]]:
        """计算用户标签（基于时间加权）- 适配字段分离"""
        try:
            # 查询用户所有内容的标签统计（时间加权，字段分离版本）
            query = """
                SELECT 
                    tag_value,
                    SUM(
                        CASE 
                            WHEN published_at > datetime('now', '-7 days') THEN 3
                            WHEN published_at > datetime('now', '-30 days') THEN 2
                            ELSE 1
                        END
                    ) as weighted_score,
                    COUNT(*) as tag_count
                FROM (
                    -- 提取topics字段（单个主题字符串）
                    SELECT 
                        c.topics as tag_value, 
                        c.published_at as published_at
                    FROM shared_contents c
                    JOIN user_content_relations r ON c.id = r.content_id
                    WHERE r.user_id = ? 
                    AND r.expires_at > datetime('now')
                    AND c.topics IS NOT NULL 
                    AND c.topics != ''
                    AND c.topics != '其他'  -- 排除默认主题
                    
                    UNION ALL
                    
                    -- 提取tags字段（纯标签JSON数组）
                    SELECT 
                        json_each.value as tag_value, 
                        c.published_at as published_at
                    FROM shared_contents c
                    JOIN user_content_relations r ON c.id = r.content_id
                    CROSS JOIN json_each(c.tags)
                    WHERE r.user_id = ? 
                    AND r.expires_at > datetime('now')
                    AND c.tags IS NOT NULL 
                    AND json_each.value IS NOT NULL
                    AND json_each.value != ''
                ) tagged_content
                GROUP BY tag_value
                ORDER BY weighted_score DESC, tag_count DESC
                LIMIT 15  -- 增加到15个，包含主题+标签
            """
            
            cursor.execute(query, (user_id, user_id))  # 需要两个参数，因为UNION ALL
            rows = cursor.fetchall()
            
            tags = []
            for row in rows:
                tag_name, weighted_score, tag_count = row
                if tag_name and tag_name.strip():  # 过滤空标签
                    tags.append({
                        "name": tag_name.strip(),
                        "count": int(tag_count),
                        "score": float(weighted_score)
                    })
            
            return tags
            
        except Exception as e:
            logger.error(f"计算用户标签失败: {e}")
            return []
    
    def _get_user_content_count(self, cursor, user_id: int) -> int:
        """获取用户内容总数（使用新架构）"""
        try:
            cursor.execute("""
                SELECT COUNT(*)
                FROM shared_contents c
                JOIN user_content_relations r ON c.id = r.content_id
                WHERE r.user_id = ? AND r.expires_at > datetime('now')
            """, (user_id,))
            
            return cursor.fetchone()[0]
            
        except Exception as e:
            logger.error(f"获取用户内容总数失败: {e}")
            return 0
    
    def get_users_need_cache_update(self) -> List[int]:
        """获取需要更新缓存的用户列表（使用新架构）"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 查找活跃用户（最近7天有内容更新的用户，使用新架构）
                cursor.execute("""
                    SELECT DISTINCT r.user_id
                    FROM user_content_relations r
                    JOIN shared_contents c ON c.id = r.content_id
                    WHERE c.created_at > datetime('now', '-7 days')
                    AND r.expires_at > datetime('now')
                """)
                
                active_users = [row[0] for row in cursor.fetchall()]
                
                users_need_update = []
                
                for user_id in active_users:
                    # 检查缓存是否需要更新
                    cursor.execute("""
                        SELECT last_updated, content_count
                        FROM user_tag_cache
                        WHERE user_id = ?
                    """, (user_id,))
                    
                    cache_row = cursor.fetchone()
                    current_content_count = self._get_user_content_count(cursor, user_id)
                    
                    need_update = False
                    
                    if not cache_row:
                        # 没有缓存记录
                        need_update = True
                    else:
                        last_updated, cached_content_count = cache_row
                        cache_time = datetime.fromisoformat(last_updated)
                        
                        # 检查缓存过期（30分钟）
                        if datetime.now() - cache_time > timedelta(minutes=30):
                            need_update = True
                        
                        # 检查内容数量变化
                        elif current_content_count != cached_content_count:
                            need_update = True
                    
                    if need_update:
                        users_need_update.append(user_id)
                
                return users_need_update
                
        except Exception as e:
            logger.error(f"获取需要缓存更新的用户失败: {e}")
            return []
    
    def batch_update_user_tags(self, user_ids: List[int] = None) -> Dict[str, int]:
        """批量更新用户标签缓存"""
        if user_ids is None:
            user_ids = self.get_users_need_cache_update()
        
        success_count = 0
        error_count = 0
        
        for user_id in user_ids:
            try:
                self.update_user_tags_cache(user_id)
                success_count += 1
            except Exception as e:
                logger.error(f"更新用户{user_id}标签缓存失败: {e}")
                error_count += 1
        
        logger.info(f"批量更新标签缓存完成: 成功{success_count}, 失败{error_count}")
        
        return {
            "success": success_count,
            "error": error_count,
            "total": len(user_ids)
        }
    
    def cleanup_expired_cache(self, days: int = 7):
        """清理过期缓存"""
        try:
            with get_db_transaction() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM user_tag_cache
                    WHERE last_updated < datetime('now', '-{} days')
                """.format(days))
                
                deleted_count = cursor.rowcount
                
                logger.info(f"清理过期标签缓存: 删除{deleted_count}条记录")
                return deleted_count
                
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return 0


# 创建全局服务实例
tag_cache_service = TagCacheService() 