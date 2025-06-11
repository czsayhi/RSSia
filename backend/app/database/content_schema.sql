-- RSS内容相关数据库表结构
-- 支持完整的业务逻辑需求

-- 1. RSS内容主表
CREATE TABLE IF NOT EXISTS rss_contents (
    -- 基础字段
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    
    -- Feed级别信息 (订阅源信息)
    feed_title VARCHAR(500) NOT NULL,
    feed_description TEXT,
    feed_link VARCHAR(1000),
    platform VARCHAR(50) NOT NULL,
    feed_last_build_date TIMESTAMP,
    
    -- Item级别信息 (单条内容)
    title VARCHAR(500) NOT NULL,
    author VARCHAR(200),
    published_at TIMESTAMP NOT NULL,
    original_link VARCHAR(1000) NOT NULL,
    
    -- 内容详情
    content_type VARCHAR(20) NOT NULL DEFAULT 'text',
    description TEXT,
    description_text TEXT,
    cover_image_url VARCHAR(1000),
    
    -- AI增强字段 (预留)
    summary TEXT,
    tags JSON, -- 存储标签数组
    
    -- 用户交互
    is_read BOOLEAN DEFAULT FALSE,
    is_favorited BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (subscription_id) REFERENCES user_subscriptions (id) ON DELETE CASCADE
);

-- 2. 媒体项表 (一对多关系)
CREATE TABLE IF NOT EXISTS content_media_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    url VARCHAR(1000) NOT NULL,
    media_type VARCHAR(20) NOT NULL, -- image/video/audio
    description TEXT,
    duration INTEGER, -- 视频时长（秒），仅video类型使用
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (content_id) REFERENCES rss_contents (id) ON DELETE CASCADE
);

-- 3. 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_rss_contents_subscription_id ON rss_contents (subscription_id);
CREATE INDEX IF NOT EXISTS idx_rss_contents_published_at ON rss_contents (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_rss_contents_platform ON rss_contents (platform);
CREATE INDEX IF NOT EXISTS idx_rss_contents_content_type ON rss_contents (content_type);
CREATE INDEX IF NOT EXISTS idx_rss_contents_is_read ON rss_contents (is_read);
CREATE INDEX IF NOT EXISTS idx_rss_contents_created_at ON rss_contents (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rss_contents_hash ON rss_contents (content_hash);

CREATE INDEX IF NOT EXISTS idx_content_media_content_id ON content_media_items (content_id);
CREATE INDEX IF NOT EXISTS idx_content_media_type ON content_media_items (media_type);

-- 4. 内容清理触发器 (自动删除过期内容 - 保留1天)
CREATE TRIGGER IF NOT EXISTS cleanup_old_contents
AFTER INSERT ON rss_contents
BEGIN
    DELETE FROM rss_contents 
    WHERE created_at < datetime('now', '-1 day');
END;

-- 5. 视图：用户友好的内容查询
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
ORDER BY c.published_at DESC;

-- 6. 统计视图：内容数据统计
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
GROUP BY platform, content_type; 