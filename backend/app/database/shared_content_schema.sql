-- RSS内容共享存储架构
-- 新存储方案：内容去重共享 + 用户关系映射
-- 创建时间: 2025-01-14
-- 修改时间: 2025-06-28 (字段分离优化)

-- 1. 共享内容表（去重后的内容存储）
CREATE TABLE IF NOT EXISTS shared_contents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 内容字段（与现有rss_contents兼容）
    title VARCHAR(500) NOT NULL,
    description TEXT,
    description_text TEXT,
    author VARCHAR(200),
    published_at TIMESTAMP NOT NULL,
    original_link VARCHAR(1000) NOT NULL,
    content_type VARCHAR(20) NOT NULL DEFAULT 'text',
    platform VARCHAR(50) NOT NULL,
    
    -- 去重字段
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    guid VARCHAR(500),
    
    -- Feed级别信息
    feed_title VARCHAR(500) NOT NULL,
    feed_description TEXT,
    feed_link VARCHAR(1000),
    feed_image_url VARCHAR(1000),
    feed_last_build_date TIMESTAMP,
    
    -- 富媒体内容
    cover_image VARCHAR(1000),
    
    -- AI处理结果（共享，统一处理）- 字段分离优化
    summary TEXT,
    topics VARCHAR(50) NOT NULL DEFAULT '其他',  -- 单个主题字符串
    tags JSON,  -- 纯标签数组 ["标签1", "标签2", "标签3"]
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- 2. 用户内容关系表（用户-内容映射）
CREATE TABLE IF NOT EXISTS user_content_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content_id INTEGER NOT NULL,
    subscription_id INTEGER NOT NULL,
    
    -- 用户个人状态
    is_read BOOLEAN DEFAULT FALSE,
    is_favorited BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    personal_tags JSON,
    
    -- 生命周期管理（关键：每用户独立过期时间）
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 约束
    UNIQUE(user_id, content_id, subscription_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id),
    FOREIGN KEY(content_id) REFERENCES shared_contents(id) ON DELETE CASCADE,
    FOREIGN KEY(subscription_id) REFERENCES user_subscriptions(id) ON DELETE CASCADE
);

-- 3. 共享媒体项表（关联到shared_contents）
CREATE TABLE IF NOT EXISTS shared_content_media_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    url VARCHAR(1000) NOT NULL,
    media_type VARCHAR(20) NOT NULL, -- image/video/audio
    description TEXT,
    duration INTEGER, -- 视频时长（秒），仅video类型使用
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (content_id) REFERENCES shared_contents (id) ON DELETE CASCADE
);

-- 4. 关键索引优化（新增主题索引）
-- 共享内容表索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_shared_content_hash ON shared_contents(content_hash);
CREATE INDEX IF NOT EXISTS idx_shared_content_guid ON shared_contents(guid);
CREATE INDEX IF NOT EXISTS idx_shared_content_platform ON shared_contents(platform);
CREATE INDEX IF NOT EXISTS idx_shared_content_published ON shared_contents(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_shared_content_type ON shared_contents(content_type);
CREATE INDEX IF NOT EXISTS idx_shared_content_topics ON shared_contents(topics);  -- 新增：主题索引

-- 用户关系表索引
CREATE INDEX IF NOT EXISTS idx_relations_expires ON user_content_relations(expires_at);
CREATE INDEX IF NOT EXISTS idx_relations_user ON user_content_relations(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_relations_subscription ON user_content_relations(subscription_id);
CREATE INDEX IF NOT EXISTS idx_relations_content ON user_content_relations(content_id);
CREATE INDEX IF NOT EXISTS idx_relations_user_read ON user_content_relations(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_relations_user_fav ON user_content_relations(user_id, is_favorited);

-- 媒体项表索引
CREATE INDEX IF NOT EXISTS idx_shared_media_content_id ON shared_content_media_items(content_id);
CREATE INDEX IF NOT EXISTS idx_shared_media_type ON shared_content_media_items(media_type);

-- 5. 自动清理触发器（基于用户关系过期时间）
CREATE TRIGGER IF NOT EXISTS cleanup_expired_relations
AFTER INSERT ON user_content_relations
BEGIN
    -- 清理过期的用户关系
    DELETE FROM user_content_relations 
    WHERE expires_at < datetime('now');
    
    -- 清理没有用户关系的孤立内容
    DELETE FROM shared_contents 
    WHERE id NOT IN (
        SELECT DISTINCT content_id 
        FROM user_content_relations 
        WHERE expires_at > datetime('now')
    );
END;

-- 6. 用户友好的查询视图（适配字段分离）
CREATE VIEW IF NOT EXISTS v_user_shared_content AS
SELECT 
    c.id as content_id,
    r.subscription_id,
    r.user_id,
    us.custom_name as subscription_name,
    c.feed_title,
    c.platform,
    c.title,
    c.author,
    c.published_at,
    c.original_link,
    c.content_type,
    c.cover_image,
    c.description,
    c.description_text,
    c.summary,
    c.topics,      -- 新：直接的主题字段
    c.tags,        -- 新：纯标签JSON数组
    r.is_read,
    r.is_favorited,
    r.read_at,
    r.personal_tags,
    r.expires_at,
    c.created_at,
    GROUP_CONCAT(
        json_object(
            'url', m.url, 
            'type', m.media_type, 
            'description', m.description,
            'duration', m.duration
        )
    ) as media_items_json
FROM shared_contents c
JOIN user_content_relations r ON c.id = r.content_id
LEFT JOIN user_subscriptions us ON r.subscription_id = us.id
LEFT JOIN shared_content_media_items m ON c.id = m.content_id
WHERE r.expires_at > datetime('now')
GROUP BY c.id, r.id
ORDER BY c.published_at DESC;

-- 7. 内容统计视图（适配字段分离）
CREATE VIEW IF NOT EXISTS v_shared_content_stats AS
SELECT 
    c.platform,
    c.content_type,
    c.topics,      -- 新：按主题统计
    COUNT(DISTINCT c.id) as unique_content_count,
    COUNT(r.id) as total_user_relations,
    COUNT(CASE WHEN r.is_read = 1 THEN 1 END) as read_count,
    COUNT(CASE WHEN r.is_favorited = 1 THEN 1 END) as favorited_count,
    MAX(c.published_at) as latest_published_at,
    MIN(c.published_at) as earliest_published_at,
    AVG(
        (SELECT COUNT(*) FROM user_content_relations ur WHERE ur.content_id = c.id)
    ) as avg_users_per_content
FROM shared_contents c
LEFT JOIN user_content_relations r ON c.id = r.content_id
WHERE r.expires_at > datetime('now') OR r.expires_at IS NULL
GROUP BY c.platform, c.content_type, c.topics; 