# RSS智能订阅器数据库设计规范

## 📋 文档说明

本文档是RSS智能订阅器项目的完整数据库设计规范，包含所有表结构、字段定义、业务规则和设计原则。

**版本**: v2.0  
**更新时间**: 2025-06-14  
**确认状态**: ✅ 已确认  
**数据库总表数**: 11张（8张实体表 + 2张视图 + 1张系统表）

---

## 🏗️ 数据库总体设计

### 设计原则
- **业务完整性**: 支持RSS订阅全生命周期管理
- **数据一致性**: 外键约束和级联删除保证数据完整性
- **性能优化**: 16个索引优化查询性能
- **扩展性**: AI增强字段预留，JSON灵活存储
- **自动化**: 自动清理机制和智能缓存策略

### 表分类概览

| 分类 | 表数量 | 表名 | 主要功能 |
|------|--------|------|----------|
| **核心业务表** | 5张 | users, user_subscriptions, rss_contents, content_media_items, user_fetch_configs | 核心业务逻辑 |
| **日志监控表** | 2张 | user_fetch_logs, fetch_task_logs | 系统监控和审计 |
| **缓存优化表** | 1张 | user_tag_cache | 性能优化 |
| **数据视图** | 2张 | v_user_content, v_content_stats | 查询优化 |
| **系统表** | 1张 | sqlite_sequence | SQLite系统表 |

---

## 📊 核心业务表详细设计

### 1. 用户信息表 (users)

**表说明**: 系统用户基础信息管理  
**记录数**: 5条  
**与后端匹配**: 🟢 完全匹配 User dataclass

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    access_token VARCHAR(255) UNIQUE,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 字段详细说明

| 字段名 | 数据类型 | 约束 | 业务含义 | 设计理由 |
|--------|----------|------|----------|----------|
| `user_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 用户唯一标识 | 自增主键，系统内部标识 |
| `username` | VARCHAR(50) | UNIQUE NOT NULL | 用户名 | 支持用户名登录，长度限制50字符 |
| `email` | VARCHAR(255) | UNIQUE NOT NULL | 邮箱地址 | 支持邮箱登录，标准邮箱长度 |
| `password_hash` | VARCHAR(255) | NOT NULL | 密码哈希值 | SHA-256哈希，安全存储 |
| `access_token` | VARCHAR(255) | UNIQUE | 访问令牌 | API认证，32字节URL安全编码 |
| `is_active` | BOOLEAN | DEFAULT 1 | 激活状态 | 软删除支持，1=激活，0=禁用 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 审计字段，自动记录 |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 | 审计字段，手动维护 |

#### 索引设计
```sql
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_token ON users(access_token);
```

### 2. 用户订阅表 (user_subscriptions)

**表说明**: 用户RSS订阅配置管理  
**记录数**: 6条  
**与后端匹配**: 🟢 完全匹配 UserSubscription模型

```sql
CREATE TABLE user_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL DEFAULT 1,
    template_id TEXT NOT NULL,  -- JSON模板ID
    target_user_id TEXT NOT NULL,
    custom_name TEXT,
    rss_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    last_update TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 字段详细说明

| 字段名 | 数据类型 | 约束 | 业务含义 | 设计理由 |
|--------|----------|------|----------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 订阅唯一标识 | 自增主键 |
| `user_id` | INTEGER | NOT NULL DEFAULT 1 | 用户ID | 外键关联users表 |
| `template_id` | TEXT | NOT NULL | 订阅模板ID | JSON配置系统，灵活模板 |
| `target_user_id` | TEXT | NOT NULL | 目标用户/关键词 | 支持各平台用户ID或搜索关键词 |
| `custom_name` | TEXT | NULL | 自定义订阅名称 | 用户友好的显示名称 |
| `rss_url` | TEXT | NOT NULL | RSS订阅地址 | 实际的RSSHub订阅URL |
| `is_active` | BOOLEAN | DEFAULT 1 | 订阅状态 | 启用/禁用控制，软删除 |
| `last_update` | TIMESTAMP | NULL | 最后更新时间 | RSS内容拉取时间戳 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 审计字段 |

### 3. RSS内容表 (rss_contents)

**表说明**: RSS内容存储和管理，支持多媒体和AI增强  
**记录数**: 0条（自动清理机制）  
**与后端匹配**: 🟢 完全匹配 RSSContent模型

```sql
CREATE TABLE rss_contents (
    -- 基础字段
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    
    -- Feed级别信息
    feed_title VARCHAR(500) NOT NULL,
    feed_description TEXT,
    feed_link VARCHAR(1000),
    feed_image_url VARCHAR(1000),  -- 订阅源头像URL
    platform VARCHAR(50) NOT NULL,
    feed_last_build_date TIMESTAMP,
    
    -- Item级别信息
    title VARCHAR(500) NOT NULL,
    author VARCHAR(200),
    published_at TIMESTAMP NOT NULL,
    original_link VARCHAR(1000) NOT NULL,
    
    -- 内容详情
    content_type VARCHAR(20) NOT NULL DEFAULT 'text',
    description TEXT,
    description_text TEXT,
    cover_image VARCHAR(1000),
    
    -- AI增强字段
    summary TEXT,
    tags JSON,
    
    -- 用户交互
    is_read BOOLEAN DEFAULT FALSE,
    is_favorited BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    
    -- 系统字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    
    FOREIGN KEY(subscription_id) REFERENCES user_subscriptions(id) ON DELETE CASCADE
);
```

#### 字段分组说明

**基础字段组**
| 字段名 | 业务含义 | 设计理由 |
|--------|----------|----------|
| `id` | 内容唯一标识 | 自增主键，系统内部标识 |
| `subscription_id` | 关联订阅ID | 外键约束，数据隔离 |
| `content_hash` | 内容哈希值 | 基于标题+链接+描述生成，防重复 |

**Feed级别信息组**（订阅源信息）
| 字段名 | 业务含义 | 设计理由 |
|--------|----------|----------|
| `feed_title` | 订阅源标题 | RSS Feed头部title字段 |
| `feed_description` | 订阅源描述 | 清理"Powered by RSSHub"后的内容 |
| `feed_link` | 订阅源主页 | 区别于内容原文地址 |
| `feed_image_url` | 订阅源头像 | RSS Feed头部image字段 |
| `platform` | 平台类型 | bilibili/weibo/jike等 |
| `feed_last_build_date` | Feed构建时间 | RSS头部lastBuildDate |

**Item级别信息组**（单条内容信息）
| 字段名 | 业务含义 | 设计理由 |
|--------|----------|----------|
| `title` | 内容标题 | 清理HTML标签后的纯文本 |
| `author` | 作者信息 | 优先item提取，用feed_title兜底 |
| `published_at` | 发布时间 | RSS item的pubDate字段 |
| `original_link` | 内容原文地址 | 区别于订阅源主页地址 |

**内容详情组**
| 字段名 | 业务含义 | 取值范围 |
|--------|----------|----------|
| `content_type` | 内容类型 | video/image_text/text |
| `description` | 原始HTML描述 | 不做富媒体预处理 |
| `description_text` | 纯文本描述 | HTML转纯文本版本 |
| `cover_image` | 封面图片URL | 从媒体项中选择第一张 |

**AI增强字段组**（预留扩展）
| 字段名 | 业务含义 | 当前状态 |
|--------|----------|----------|
| `summary` | AI生成摘要 | 预留字段，暂时为空 |
| `tags` | 内容标签数组 | JSON格式，AI生成用于筛选 |

**用户交互组**
| 字段名 | 业务含义 | 交互逻辑 |
|--------|----------|----------|
| `is_read` | 已读状态 | 用户点击阅读后标记 |
| `is_favorited` | 收藏状态 | 用户收藏操作 |
| `read_at` | 阅读时间戳 | 阅读时自动记录 |

#### 自动清理机制
```sql
CREATE TRIGGER cleanup_old_contents
    AFTER INSERT ON rss_contents
    BEGIN
        DELETE FROM rss_contents 
        WHERE created_at < datetime('now', '-1 day');
    END;
```

### 4. 内容媒体项表 (content_media_items)

**表说明**: RSS内容的媒体项（图片、视频、音频）管理  
**记录数**: 0条  
**与后端匹配**: 🟢 完全匹配多媒体内容支持

```sql
CREATE TABLE content_media_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    url VARCHAR(1000) NOT NULL,
    media_type VARCHAR(20) NOT NULL,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(content_id) REFERENCES rss_contents(id) ON DELETE CASCADE
);
```

#### 字段详细说明

| 字段名 | 数据类型 | 约束 | 业务含义 | 取值范围 |
|--------|----------|------|----------|----------|
| `id` | INTEGER | PRIMARY KEY | 媒体项唯一标识 | 自增主键 |
| `content_id` | INTEGER | NOT NULL, FK | 关联内容ID | 外键约束 |
| `url` | VARCHAR(1000) | NOT NULL | 媒体URL地址 | 支持长URL |
| `media_type` | VARCHAR(20) | NOT NULL | 媒体类型 | image/video/audio |
| `description` | TEXT | NULL | 媒体描述信息 | 可选的媒体说明 |
| `sort_order` | INTEGER | DEFAULT 0 | 排序顺序 | 0开始的排序值 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 审计字段 |

### 5. 用户拉取配置表 (user_fetch_configs)

**表说明**: 用户个性化的RSS拉取频率和控制配置  
**记录数**: 5条（每用户一条）  
**与后端匹配**: 🟢 完全匹配 FetchConfigService

```sql
CREATE TABLE user_fetch_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    auto_fetch_enabled BOOLEAN DEFAULT 0,
    frequency VARCHAR(20) DEFAULT 'daily',
    preferred_hour INTEGER DEFAULT 9,
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    daily_limit INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 字段详细说明

| 字段名 | 数据类型 | 约束 | 业务含义 | 默认值/取值范围 |
|--------|----------|------|----------|----------------|
| `user_id` | INTEGER | NOT NULL UNIQUE | 用户ID | 一对一关系 |
| `auto_fetch_enabled` | BOOLEAN | DEFAULT 0 | 自动拉取开关 | 0=关闭，1=开启 |
| `frequency` | VARCHAR(20) | DEFAULT 'daily' | 拉取频率 | daily/three_days/weekly |
| `preferred_hour` | INTEGER | DEFAULT 9 | 首选拉取时间 | 0-23小时 |
| `timezone` | VARCHAR(50) | DEFAULT 'Asia/Shanghai' | 时区设置 | 标准时区字符串 |
| `daily_limit` | INTEGER | DEFAULT 10 | 每日限制次数 | 防滥用限制 |
| `is_active` | BOOLEAN | DEFAULT 1 | 配置状态 | 软删除支持 |

---

## 📈 日志监控表设计

### 6. 用户拉取日志表 (user_fetch_logs)

**表说明**: 用户级别的RSS拉取统计和日志  
**记录数**: 3条  
**与后端匹配**: 🟢 支持拉取统计分析

```sql
CREATE TABLE user_fetch_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    fetch_date DATE NOT NULL,
    fetch_count INTEGER DEFAULT 0,
    auto_fetch_count INTEGER DEFAULT 0,
    manual_fetch_count INTEGER DEFAULT 0,
    last_fetch_at TIMESTAMP,
    last_fetch_success BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, fetch_date)
);
```

### 7. 拉取任务日志表 (fetch_task_logs)

**表说明**: 任务级别的拉取调度和执行日志  
**记录数**: 0条  
**与后端匹配**: 🟢 支持任务调度系统

```sql
CREATE TABLE fetch_task_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    task_type VARCHAR(20) NOT NULL,
    task_key VARCHAR(100) NOT NULL,
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    attempt_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    status VARCHAR(20) DEFAULT 'pending',
    success_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    error_message TEXT,
    next_retry_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_key)
);
```

---

## ⚡ 缓存优化表设计

### 8. 用户标签缓存表 (user_tag_cache)

**表说明**: 用户智能标签推荐的缓存优化表  
**记录数**: 0条  
**与后端匹配**: 🟢 完全匹配 TagCacheService

```sql
CREATE TABLE user_tag_cache (
    user_id INTEGER PRIMARY KEY,
    tags_json TEXT NOT NULL,
    content_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 业务逻辑说明

**缓存策略**:
- **更新频率**: 30分钟检查一次
- **批量处理**: 50用户/批次
- **权重算法**: 7天×3, 30天×2, 更早×1

**JSON数据格式**:
```json
[
  {
    "tag": "技术",
    "count": 15,
    "weight": 45,
    "last_seen": "2025-06-14T10:30:00"
  }
]
```

---

## 🔍 数据视图设计

### 9. 用户内容视图 (v_user_content)

**视图说明**: 用户内容聚合查询优化视图

```sql
CREATE VIEW v_user_content AS
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
    c.cover_image,
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
```

### 10. 内容统计视图 (v_content_stats)

**视图说明**: 内容统计分析优化视图

```sql
CREATE VIEW v_content_stats AS
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
```

---

## 🔗 数据关系设计

### 外键约束
```sql
-- RSS内容表外键
rss_contents.subscription_id → user_subscriptions.id (CASCADE DELETE)

-- 媒体项表外键  
content_media_items.content_id → rss_contents.id (CASCADE DELETE)
```

### 数据完整性保证

**级联删除策略**:
- 用户删除订阅 → 自动删除相关RSS内容和媒体项
- RSS内容删除 → 自动删除相关媒体项

**唯一性约束**:
- `users.username` - 防止用户名重复
- `users.email` - 防止邮箱重复  
- `users.access_token` - 防止令牌冲突
- `rss_contents.content_hash` - 防止内容重复
- `fetch_task_logs.task_key` - 防止任务重复

---

## 📋 索引优化策略

### 主要索引列表
```sql
-- 用户表索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_token ON users(access_token);

-- RSS内容表索引
CREATE INDEX idx_rss_contents_subscription_id ON rss_contents(subscription_id);
CREATE INDEX idx_rss_contents_published_at ON rss_contents(published_at DESC);
CREATE INDEX idx_rss_contents_platform ON rss_contents(platform);
CREATE INDEX idx_rss_contents_content_type ON rss_contents(content_type);
CREATE INDEX idx_rss_contents_is_read ON rss_contents(is_read);
CREATE INDEX idx_rss_contents_created_at ON rss_contents(created_at DESC);
CREATE INDEX idx_rss_contents_hash ON rss_contents(content_hash);

-- 媒体项表索引
CREATE INDEX idx_content_media_content_id ON content_media_items(content_id);
CREATE INDEX idx_content_media_type ON content_media_items(media_type);

-- 其他关键索引
CREATE INDEX idx_user_tag_cache_updated ON user_tag_cache(last_updated);
CREATE INDEX idx_user_auto_fetch ON user_fetch_configs(user_id, auto_fetch_enabled);
CREATE UNIQUE INDEX idx_user_fetch_date ON user_fetch_logs(user_id, fetch_date);
CREATE UNIQUE INDEX idx_task_key ON fetch_task_logs(task_key);
CREATE INDEX idx_user_task_status ON fetch_task_logs(user_id, status);
CREATE INDEX idx_scheduled_at ON fetch_task_logs(scheduled_at);
```

### 查询优化分析

**总索引数**: 16个
**优化目标**:
- 用户内容列表查询 (`subscription_id` + `published_at DESC`)
- 平台内容筛选 (`platform` + `content_type`)
- 已读/收藏状态查询 (`is_read` + `is_favorited`)
- 任务调度查询 (`scheduled_at` + `status`)

---

## 🎯 业务规则说明

### 数据隔离策略
- **用户隔离**: 用户只能访问自己订阅的内容
- **订阅隔离**: 通过 `subscription_id` 实现数据边界
- **产品用户ID**: 系统统一使用 `user_id` 概念
- **目标用户ID**: 不同平台的用户标识仅作为RSS URL参数

### 内容处理规则
- **作者信息兜底**: 优先item.author，找不到用feed_title兜底
- **内容类型判断**: video/image_text/text三种类型
- **地址区分**: feed_link(订阅源主页) vs original_link(内容原文)
- **去重策略**: 基于content_hash（标题+链接+描述）
- **描述处理**: 存储原始description和纯文本版本

### 数据保留策略
- **RSS内容**: 1天自动清理（性能考虑）
- **用户数据**: 永久保留（软删除）
- **日志数据**: 根据业务需要保留
- **缓存数据**: 30分钟更新周期

### 默认配置策略
- **新用户拉取配置**: 自动拉取关闭，每日限制10次，8:00拉取
- **内容类型**: 默认为text类型
- **用户状态**: 默认激活状态
- **订阅状态**: 默认启用状态

---

## 🔄 与后端代码匹配度评估

### 🟢 高度匹配的设计

| 后端组件 | 对应表/字段 | 匹配度 | 说明 |
|----------|-------------|--------|------|
| **UserService** | `users` + `user_fetch_configs` | 🟢 100% | 用户管理和认证完全匹配 |
| **SubscriptionService** | `user_subscriptions` | 🟢 100% | 订阅管理逻辑一致 |
| **RSSContent模型** | `rss_contents` + `content_media_items` | 🟢 100% | 内容结构完全对应 |
| **TagCacheService** | `user_tag_cache` | 🟢 100% | 缓存策略一致 |
| **FetchScheduler** | `fetch_task_logs` + `user_fetch_logs` | 🟢 100% | 任务调度支持 |

### 🟡 可优化的设计

1. **SQLAlchemy集成**: 当前使用原生SQL，可考虑ORM支持
2. **模板配置**: template_id使用JSON配置，可考虑独立表
3. **国际化支持**: 时区和多语言支持可进一步完善

---

## 📊 数据统计报告

### 当前数据分布
- **用户总数**: 5个
- **订阅总数**: 6个（平均1.2个/用户）
- **内容总数**: 0个（自动清理机制）
- **配置完整性**: 100%（所有用户都有拉取配置）

### 表大小分析
- **最大表**: `rss_contents`（设计容量最大，自动清理）
- **最小表**: 系统表和视图
- **索引效率**: 16个索引优化查询性能
- **存储优化**: 1天清理策略保持数据库轻量

---

## 📝 版本变更历史

| 版本 | 时间 | 变更内容 | 变更原因 |
|------|------|----------|----------|
| v1.0 | 2025-06-11 | 初始字段定义 | MVP阶段核心需求 |
| v1.1 | 2025-06-11 | 向后兼容性优化 | 与现有代码兼容 |
| v1.2 | 2025-06-11 | 订阅源logo设计修正 | 前端logo管理策略 |
| **v2.0** | **2025-06-14** | **完整数据库设计规范** | **整合实际结构和现有规范** |

### v2.0 主要更新
- ✅ **完整表结构文档**: 覆盖所有11张表的详细设计
- ✅ **业务逻辑整合**: 结合实际代码的业务规则
- ✅ **性能优化策略**: 索引设计和查询优化
- ✅ **数据完整性保证**: 外键约束和级联删除
- ✅ **与后端匹配度分析**: 代码和数据库的一致性验证

---

## 🔗 相关文档

- [RSS原始数据完整分析报告](../analysis/rss-raw-data-complete-analysis.md)
- [v0.6.0任务执行报告](../progress/v0.6.0-task-execution-report.md)
- [数据库字段规格说明](./field-specifications.md)
- [前后端集成分析](../progress/frontend-backend-integration-analysis.md) 