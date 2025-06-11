# RSS订阅器数据库字段规格说明

## 📋 文档说明
本文档用于管理RSS订阅器项目中所有已确认的数据库字段定义，包括字段的业务含义、数据类型、约束条件等。每当讨论到新增或修改字段时，都需要在此文档中维护更新。

**版本**: v1.0  
**更新时间**: 2025-06-11  
**确认状态**: ✅ 已确认

---

## 🏗️ 核心表结构

### 1. RSS内容主表 (rss_contents)

| 字段名 | 数据类型 | 约束 | 业务含义 | 确认时间 |
|--------|----------|------|----------|----------|
| **基础字段** |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 内容唯一标识，系统自动生成 | 2025-06-11 |
| `subscription_id` | INTEGER | NOT NULL, FK | 关联用户订阅表，实现数据隔离 | 2025-06-11 |
| `content_hash` | VARCHAR(64) | NOT NULL UNIQUE | 内容哈希值，用于去重，基于标题+链接+描述生成 | 2025-06-11 |
| **Feed级别信息 (订阅源信息)** |
| `feed_title` | VARCHAR(500) | NOT NULL | 订阅源标题，从RSS Feed头部提取 | 2025-06-11 |
| `feed_description` | TEXT | NULL | 订阅源描述，清理"Powered by RSSHub"后的内容 | 2025-06-11 |
| `feed_link` | VARCHAR(1000) | NULL | 订阅源主页地址，区别于内容原文地址 | 2025-06-11 |
| ~~`feed_image_url`~~ | ~~VARCHAR(1000)~~ | ~~NULL~~ | ~~订阅源头像URL，从Feed头部提取~~ | ~~2025-06-11~~ |
| `platform` | VARCHAR(50) | NOT NULL | 平台类型：bilibili/weibo/jike | 2025-06-11 |
| `feed_last_build_date` | TIMESTAMP | NULL | Feed最后构建时间，从RSS头部提取 | 2025-06-11 |
| **Item级别信息 (单条内容信息)** |
| `title` | VARCHAR(500) | NOT NULL | 内容标题，从RSS item提取并清理HTML标签 | 2025-06-11 |
| `author` | VARCHAR(200) | NULL | 作者信息，优先从item提取，找不到用feed_title兜底 | 2025-06-11 |
| `published_at` | TIMESTAMP | NOT NULL | 发布时间，从RSS item的pubDate字段解析 | 2025-06-11 |
| `original_link` | VARCHAR(1000) | NOT NULL | 内容原文地址，区别于订阅源主页地址 | 2025-06-11 |
| **内容详情** |
| `content_type` | VARCHAR(20) | NOT NULL DEFAULT 'text' | 内容类型：video/image_text/text | 2025-06-11 |
| `description` | TEXT | NULL | 原始HTML描述内容，不做富媒体预处理 | 2025-06-11 |
| `description_text` | TEXT | NULL | 纯文本描述内容，从HTML提取的纯文本版本 | 2025-06-11 |
| `cover_image` | VARCHAR(1000) | NULL | 封面图片URL，从媒体项中选择第一张图片 | 2025-06-11 |
| **AI增强字段 (预留)** |
| `summary` | TEXT | NULL | AI生成摘要，预留字段，暂时置空 | 2025-06-11 |
| `tags` | JSON | NULL | 内容标签数组，后端AI生成，用于筛选 | 2025-06-11 |
| **用户交互** |
| `is_read` | BOOLEAN | DEFAULT FALSE | 是否已读状态 | 2025-06-11 |
| `is_favorited` | BOOLEAN | DEFAULT FALSE | 是否收藏状态 | 2025-06-11 |
| `read_at` | TIMESTAMP | NULL | 阅读时间戳 | 2025-06-11 |
| **系统字段** |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 内容拉取时间，系统自动记录 | 2025-06-11 |
| `updated_at` | TIMESTAMP | NULL | 内容更新时间 | 2025-06-11 |

### 2. 媒体项表 (content_media_items)

| 字段名 | 数据类型 | 约束 | 业务含义 | 确认时间 |
|--------|----------|------|----------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 媒体项唯一标识 | 2025-06-11 |
| `content_id` | INTEGER | NOT NULL, FK | 关联rss_contents表 | 2025-06-11 |
| `url` | VARCHAR(1000) | NOT NULL | 媒体URL地址 | 2025-06-11 |
| `media_type` | VARCHAR(20) | NOT NULL | 媒体类型：image/video/audio | 2025-06-11 |
| `description` | TEXT | NULL | 媒体描述信息 | 2025-06-11 |
| `sort_order` | INTEGER | DEFAULT 0 | 媒体排序顺序 | 2025-06-11 |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 | 2025-06-11 |

---

## 🎯 业务规则说明

### 数据隔离策略
- **用户隔离**: 用户只能看到自己订阅的内容 (`subscription_id` → `user_subscriptions.user_id`)
- **产品用户ID**: 我们系统只有一个user_id概念，即产品用户ID
- **目标用户ID**: 不同平台的用户标识只作为RSS URL生成参数

### 字段处理规则
- **作者信息兜底**: 优先从item.author获取，找不到统一用feed_title兜底
- **内容类型判断**: 简化为3种 - VIDEO(包含视频)/IMAGE_TEXT(有图有文)/TEXT(纯文本)
- **地址区分**: feed_link(订阅源主页) vs original_link(内容原文地址)
- **描述处理**: 只存原始description，富媒体处理由后端统一处理后提供接口
- **订阅源logo**: 根据platform字段从代码配置映射，不存储在数据库中

### 数据保留策略
- **保留时间**: 1天 (通过触发器自动清理过期内容)
- **去重策略**: 基于content_hash字段，由标题+链接+描述生成

---

## 🔄 变更历史

| 版本 | 时间 | 变更内容 | 变更原因 |
|------|------|----------|----------|
| v1.0 | 2025-06-11 | 初始字段定义 | MVP阶段核心需求确认 |
| v1.1 | 2025-06-11 | 向后兼容性优化 | 确保与现有RSS内容服务代码兼容 |
| v1.2 | 2025-06-11 | 订阅源logo设计修正 | 移除feed_image_url，改为platform配置映射 |

### v1.2 详细变更内容：

**订阅源logo设计修正**:
- 移除`feed_image_url`字段，不再从Feed头部提取头像
- 新增平台配置文件 `app/config/platform_config.py`
- 后端只提供platform字段和平台元信息
- 前端根据platform在自己的public目录中查找对应logo文件

**前端logo文件管理**:
- logo文件存放在前端项目的 `public/logos/` 目录中
- 文件命名规则: `{platform}.svg`
- 支持的平台logo文件:
  - `public/logos/bilibili.svg` (哔哩哔哩)
  - `public/logos/weibo.svg` (微博)
  - `public/logos/jike.svg` (即刻) 
  - `public/logos/github.svg` (GitHub)
  - `public/logos/zhihu.svg` (知乎)
  - `public/logos/rss.svg` (默认/其他)

### v1.1 详细变更内容：

**RSSContent模型扩展** (兼容现有代码):
- 保留`link`字段名，映射到`original_link`概念
- 新增`smart_summary`字段，兼容现有智能处理功能  
- 新增`tags`字段，兼容现有标签提取功能
- 新增`platform`字段，兼容现有平台识别功能

**配置调整**:
- `RSS_CONTENT_RETENTION_DAYS`: 从30天调整为1天
- 数据库清理触发器同步调整为1天保留

**业务规则明确**:
- 作者信息兜底逻辑：统一用订阅源标题兜底，清理平台特定后缀
- 内容类型简化：从5种调整为3种（VIDEO/IMAGE_TEXT/TEXT）
- 数据隔离策略：用户只能访问自己订阅的内容

---

## 📝 待确认字段

暂无

---

## 🔗 相关文档

- [RSS原始数据完整分析报告](../analysis/rss-raw-data-complete-analysis.md)
- [v0.6.0任务执行报告](../progress/v0.6.0-task-execution-report.md) 