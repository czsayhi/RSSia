#!/usr/bin/env python3
"""
数据库服务 - RSS内容表初始化
负责创建和维护RSS内容相关的数据库表结构
"""

import sqlite3
from pathlib import Path
from loguru import logger
from typing import Optional


class DatabaseService:
    """数据库服务 - 负责RSS内容表的初始化和维护"""
    
    def __init__(self, db_path: str = "data/rss_subscriber.db"):
        """
        初始化数据库服务
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"🗃️ 数据库服务初始化: {self.db_path}")
    
    def init_content_tables(self) -> bool:
        """
        初始化RSS内容相关表
        包括：rss_contents、content_media_items及相关索引、触发器、视图
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 1. 创建RSS内容主表
                self._create_rss_contents_table(cursor)
                
                # 2. 创建媒体项表
                self._create_media_items_table(cursor)
                
                # 3. 创建索引
                self._create_indexes(cursor)
                
                # 4. 创建触发器
                self._create_triggers(cursor)
                
                # 5. 创建视图
                self._create_views(cursor)
                
                conn.commit()
                logger.success("✅ RSS内容表初始化完成")
                return True
                
        except Exception as e:
            logger.error(f"❌ RSS内容表初始化失败: {e}")
            return False
    
    def _create_rss_contents_table(self, cursor: sqlite3.Cursor) -> None:
        """创建RSS内容主表"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rss_contents (
                -- 基础字段
                id INTEGER PRIMARY KEY AUTOINCREMENT,                    -- 内容唯一标识，系统自动生成
                subscription_id INTEGER NOT NULL,                       -- 关联用户订阅表，实现数据隔离
                content_hash VARCHAR(64) NOT NULL UNIQUE,              -- 内容哈希值，用于去重，基于标题+链接+描述生成
                
                -- Feed级别信息 (订阅源信息)
                feed_title VARCHAR(500) NOT NULL,                      -- 订阅源标题，从RSS Feed头部title字段提取
                feed_description TEXT,                                  -- 订阅源描述，清理"Powered by RSSHub"后的内容
                feed_link VARCHAR(1000),                               -- 订阅源主页地址，区别于内容原文地址
                feed_image_url VARCHAR(1000),                          -- 订阅源头像URL，从Feed头部image字段提取
                platform VARCHAR(50) NOT NULL,                         -- 平台类型：bilibili/weibo/jike
                feed_last_build_date TIMESTAMP,                        -- Feed最后构建时间，从RSS头部提取
                
                -- Item级别信息 (单条内容信息)
                title VARCHAR(500) NOT NULL,                           -- 内容标题，从RSS item提取并清理HTML标签
                author VARCHAR(200),                                    -- 作者信息，优先从item提取，找不到用feed_title兜底
                published_at TIMESTAMP NOT NULL,                       -- 发布时间，从RSS item的pubDate字段解析
                original_link VARCHAR(1000) NOT NULL,                  -- 内容原文地址，区别于订阅源主页地址
                
                -- 内容详情
                content_type VARCHAR(20) NOT NULL DEFAULT 'text',      -- 内容类型：video/image_text/text
                description TEXT,                                       -- 原始HTML描述内容，不做富媒体预处理
                description_text TEXT,                                  -- 纯文本描述内容，从HTML提取的纯文本版本
                cover_image_url VARCHAR(1000),                         -- 封面图片URL，从媒体项中选择第一张图片
                
                -- AI增强字段 (预留)
                summary TEXT,                                           -- AI生成摘要，预留字段，暂时置空
                tags JSON,                                              -- 内容标签数组，后端AI生成，用于筛选
                
                -- 用户交互
                is_read BOOLEAN DEFAULT FALSE,                          -- 是否已读状态
                is_favorited BOOLEAN DEFAULT FALSE,                     -- 是否收藏状态
                read_at TIMESTAMP,                                      -- 阅读时间戳
                
                -- 系统字段
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,        -- 内容拉取时间，系统自动记录
                updated_at TIMESTAMP,                                   -- 内容更新时间
                
                -- 外键约束
                FOREIGN KEY (subscription_id) REFERENCES user_subscriptions (id) ON DELETE CASCADE
            )
        """)
        logger.debug("📋 RSS内容主表创建完成")
    
    def _create_media_items_table(self, cursor: sqlite3.Cursor) -> None:
        """创建媒体项表"""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_media_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,                  -- 媒体项唯一标识
                content_id INTEGER NOT NULL,                           -- 关联rss_contents表
                url VARCHAR(1000) NOT NULL,                            -- 媒体URL地址
                media_type VARCHAR(20) NOT NULL,                       -- 媒体类型：image/video/audio
                description TEXT,                                       -- 媒体描述信息
                sort_order INTEGER DEFAULT 0,                          -- 媒体排序顺序
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,        -- 创建时间
                
                FOREIGN KEY (content_id) REFERENCES rss_contents (id) ON DELETE CASCADE
            )
        """)
        logger.debug("📋 媒体项表创建完成")
    
    def _create_indexes(self, cursor: sqlite3.Cursor) -> None:
        """创建性能优化索引"""
        indexes = [
            # RSS内容表索引
            "CREATE INDEX IF NOT EXISTS idx_rss_contents_subscription_id ON rss_contents (subscription_id)",
            "CREATE INDEX IF NOT EXISTS idx_rss_contents_published_at ON rss_contents (published_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_rss_contents_platform ON rss_contents (platform)",
            "CREATE INDEX IF NOT EXISTS idx_rss_contents_content_type ON rss_contents (content_type)",
            "CREATE INDEX IF NOT EXISTS idx_rss_contents_is_read ON rss_contents (is_read)",
            "CREATE INDEX IF NOT EXISTS idx_rss_contents_created_at ON rss_contents (created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_rss_contents_hash ON rss_contents (content_hash)",
            
            # 媒体项表索引
            "CREATE INDEX IF NOT EXISTS idx_content_media_content_id ON content_media_items (content_id)",
            "CREATE INDEX IF NOT EXISTS idx_content_media_type ON content_media_items (media_type)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        logger.debug("📋 数据库索引创建完成")
    
    def _create_triggers(self, cursor: sqlite3.Cursor) -> None:
        """创建触发器 (自动清理过期内容)"""
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS cleanup_old_contents
            AFTER INSERT ON rss_contents
            BEGIN
                DELETE FROM rss_contents 
                WHERE created_at < datetime('now', '-1 day');
            END
        """)
        logger.debug("📋 内容清理触发器创建完成 (保留1天)")
    
    def _create_views(self, cursor: sqlite3.Cursor) -> None:
        """创建查询视图"""
        
        # 用户友好的内容查询视图
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_user_content AS
            SELECT 
                c.id,
                c.subscription_id,
                us.custom_name as subscription_name,
                c.feed_title,
                c.platform,
                c.title,
                c.author,
                c.published_at,
                c.content_type,
                c.cover_image_url,
                c.is_read,
                c.is_favorited,
                c.created_at,
                GROUP_CONCAT(
                    json_object(
                        'url', m.url, 
                        'type', m.media_type, 
                        'description', m.description
                    )
                ) as media_items_json
            FROM rss_contents c
            LEFT JOIN user_subscriptions us ON c.subscription_id = us.id
            LEFT JOIN content_media_items m ON c.id = m.content_id
            GROUP BY c.id
            ORDER BY c.published_at DESC
        """)
        
        # 内容统计视图
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_content_stats AS
            SELECT 
                platform,
                content_type,
                COUNT(*) as total_count,
                COUNT(CASE WHEN is_read = 1 THEN 1 END) as read_count,
                COUNT(CASE WHEN is_favorited = 1 THEN 1 END) as favorited_count,
                MAX(published_at) as latest_published_at,
                MIN(published_at) as earliest_published_at
            FROM rss_contents
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY platform, content_type
        """)
        
        logger.debug("📋 数据库视图创建完成")
    
    def check_table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 表是否存在
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                """, (table_name,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"❌ 检查表存在性失败: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> Optional[list]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            Optional[list]: 表结构信息
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ 获取表信息失败: {e}")
            return None


# 全局数据库服务实例
_db_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """获取数据库服务实例 (单例)"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service


def init_content_database() -> bool:
    """初始化RSS内容数据库 (便捷函数)"""
    return get_database_service().init_content_tables() 