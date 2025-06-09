# RSS智能订阅器需求规范文档

## 一、产品概述

### 1.1 产品背景
在信息爆炸的时代，用户面临内容获取渠道多、重复信息多、筛选难等问题。虽然 RSSHub 能以 RSS 方式整合多平台内容源，但原始 RSS 内容存在信噪比低、阅读体验差、无法聚合归类的问题。本项目旨在基于 RSSHub 实现一个支持用户自定义订阅源、定时抓取、自动摘要、智能标签、主题聚类及 AI 对话式检索的智能 RSS 订阅系统。

### 1.2 产品目标
- **核心目标**：利用 RSSHub 抓取多平台内容，提供友好的订阅配置和内容展示，通过大模型处理订阅内容（摘要、标签、聚类），支持与 AI 助手对话式查询
- **MVP目标**：支持精准订阅和主题聚合两种订阅模式，实现内容抓取、展示和基础管理功能

### 1.3 技术架构
- **前端**：Next.js + React + Tailwind CSS
- **后端**：FastAPI + SQLite + APScheduler
- **RSS引擎**：RSSHub（公共实例 + 后期自部署）
- **AI处理**：OpenAI API（后期阶段）
- **部署**：Docker Compose 一键启动

## 二、功能需求规范

### 2.1 用户认证系统

#### 2.1.1 MVP阶段（简化认证）
- **本地Token认证**：无需第三方登录，使用本地生成的访问密钥
- **用户会话管理**：支持记住登录状态
- **基础用户信息**：用户名、创建时间等基本信息

#### 2.1.2 后期扩展
- **微信登录集成**：支持微信开放平台网页授权
- **多账户同步**：支持跨设备数据同步

### 2.2 双模式订阅系统

#### 2.2.1 精准订阅模式
**功能描述**：按平台+用户/内容维度精确订阅

**用户交互**：
1. 选择平台（B站、微博、知乎等）
2. 选择订阅类型（用户动态、用户视频、关键词搜索等）
3. 输入参数（UID、用户名、关键词等）
4. 智能URL解析：支持直接粘贴用户主页URL自动解析

**技术实现**：
```
数据流：用户输入 → 订阅模板 → RSSHub路由 → RSS内容
存储结构：
- 订阅模板表：存储各平台的路由模板和参数规范
- 用户订阅表：存储用户的订阅配置
- 订阅源实例表：存储生成的具体RSS源
```

**MVP支持平台**：
- B站：用户动态、用户视频、关键词搜索
- 微博：用户微博、关键词搜索
- 知乎：用户动态、话题内容
- GitHub：仓库动态、用户活动
- 掘金：用户文章、标签内容

#### 2.2.2 主题聚合订阅模式
**功能描述**：跨平台主题内容聚合订阅

**用户交互**：
1. 输入主题名称（如"AI科技"）
2. 添加相关关键词（ai、人工智能、机器学习）
3. 选择目标平台（多选）
4. 系统自动生成多个RSS源并聚合展示

**技术实现**：
```
数据流：主题配置 → 多平台关键词订阅 → 内容聚合 → 去重排序
聚合逻辑：
- 为每个平台×关键词组合生成RSS源
- 统一拉取内容并按时间聚合
- 基于标题相似度进行内容去重
- 支持按平台分组或混合时间线显示
```

### 2.3 内容管理系统

#### 2.3.1 内容抓取与处理
- **定时抓取**：基于APScheduler的定时任务系统
- **频率配置**：支持每日、每3天、每7天等抓取频率
- **内容解析**：使用feedparser解析RSS内容
- **数据持久化**：订阅配置永久保存，内容数据保留1天（用户可配置）

#### 2.3.2 内容展示
- **卡片式展示**：现代化的内容卡片设计
- **简化标签过滤**：支持全部/未读/收藏、按平台过滤、按主要标签过滤的下拉框交互
- **标签标准化处理**：自动清理和标准化原生标签，卡片最多显示3个标签
- **内容跳转**：支持跳转到原始内容页面
- **内容收藏**：用户可收藏重要内容
- **阅读状态**：标记已读/未读状态

#### 2.3.3 订阅管理
- **订阅源CRUD**：添加、编辑、删除、暂停订阅
- **批量操作**：批量管理多个订阅源
- **订阅分组**：按主题或平台对订阅进行分组
- **订阅统计**：显示订阅数量、内容更新频率等

### 2.4 AI功能预留

#### 2.4.1 MVP阶段
- **功能入口预留**：在界面中预留AI助手入口、预留摘要入口
- **数据结构准备**：为AI处理预留数据字段（tags、summary等）

#### 2.4.2 后期功能
- **自动摘要**：使用大模型生成内容摘要（分为单个内容的摘要、聚合所有订阅内容的摘要）
- **智能标签**：自动提取关键词标签
- **语义聚类**：基于embedding的内容聚类
- **对话式检索**：AI助手回答用户关于订阅内容的问题

## 三、技术实现规范

### 3.1 数据库设计

#### 3.1.1 核心表结构
```sql
-- 订阅模板表（系统预设）
CREATE TABLE subscription_templates (
    id INTEGER PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    rss_template VARCHAR(200) NOT NULL,
    params_schema JSON NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户订阅表
CREATE TABLE user_subscriptions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    subscription_type VARCHAR(20) NOT NULL, -- 'precise' | 'theme'
    name VARCHAR(100) NOT NULL,
    config JSON NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订阅源实例表
CREATE TABLE subscription_feeds (
    id INTEGER PRIMARY KEY,
    subscription_id INTEGER NOT NULL,
    template_id INTEGER,
    rss_url VARCHAR(500) NOT NULL,
    params JSON,
    weight FLOAT DEFAULT 1.0,
    last_fetch_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (subscription_id) REFERENCES user_subscriptions(id),
    FOREIGN KEY (template_id) REFERENCES subscription_templates(id)
);

-- 内容表
CREATE TABLE contents (
    id INTEGER PRIMARY KEY,
    feed_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source_url VARCHAR(500) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    publish_time TIMESTAMP NOT NULL,
    raw_tags JSON,              -- 原始标签（完整保存）
    display_tags JSON,          -- 处理后的展示标签（最多5个）
    primary_tag VARCHAR(50),    -- 主要标签（用于快速过滤）
    summary TEXT,               -- AI生成摘要（预留）
    is_read BOOLEAN DEFAULT FALSE,
    is_favorited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (feed_id) REFERENCES subscription_feeds(id)
);

-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    access_token VARCHAR(100) UNIQUE NOT NULL,
    settings JSON DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 API设计规范

#### 3.2.1 RESTful API结构
```
GET    /api/subscription-templates     # 获取订阅模板
POST   /api/subscriptions              # 创建订阅
GET    /api/subscriptions              # 获取用户订阅列表
PUT    /api/subscriptions/{id}         # 更新订阅
DELETE /api/subscriptions/{id}         # 删除订阅

GET    /api/contents                   # 获取内容列表
POST   /api/contents/{id}/favorite     # 收藏内容
POST   /api/contents/{id}/read         # 标记已读

POST   /api/auth/login                 # 用户登录
POST   /api/auth/logout                # 用户登出
GET    /api/auth/profile               # 获取用户信息
```

#### 3.2.2 统一响应格式
```json
{
    "success": true,
    "data": {...},
    "message": "操作成功",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### 3.3 RSSHub集成规范

#### 3.3.1 URL生成逻辑
```python
def generate_rss_url(template: str, params: dict, base_url: str = "https://rsshub.app") -> str:
    """生成标准RSSHub URL"""
    route = template.format(**params)
    return f"{base_url}{route}"

# 示例
template = "/bilibili/user/dynamic/{uid}"
params = {"uid": "12345"}
url = generate_rss_url(template, params)
# 结果: https://rsshub.app/bilibili/user/dynamic/12345
```

#### 3.3.2 错误处理
- RSS源不可访问时的降级策略
- 频率限制的退避重试机制
- 内容解析失败的异常处理

### 3.4 扩展性设计

#### 3.4.1 新平台接入流程
1. 在`subscription_templates`表中添加新平台的模板配置
2. 如需要，添加对应的URL解析器
3. 测试RSS内容抓取和解析
4. 更新前端平台选择列表

#### 3.4.2 配置化管理
- 所有平台配置通过数据库管理，无需代码变更
- 支持动态启用/禁用特定平台
- 模板参数验证和用户输入验证

## 四、非功能性需求

### 4.1 性能要求
- **响应时间**：页面加载时间 < 2秒
- **并发处理**：支持10+用户同时使用
- **数据处理**：单用户支持100+订阅源

### 4.2 可用性要求
- **易用性**：用户侧轻量化配置，支持URL智能解析
- **可控性**：提供抓取频次、数量限制等配置
- **监控性**：抓取状态监控和错误日志

### 4.3 部署要求
- **本地部署**：Docker Compose一键启动
- **环境兼容**：支持macOS、Linux、Windows
- **资源需求**：最低1GB内存、500MB磁盘空间

## 五、开发计划

### 5.1 MVP开发阶段
**时间目标**：2-3周完成核心功能

**里程碑1**：基础架构搭建（3-4天）
- [x] 项目框架搭建（前后端）
- [x] 数据库设计和初始化
- [x] 基础API框架
- [x] 用户认证系统

**里程碑2**：订阅系统实现（5-6天）
- [x] 订阅模板配置系统
- [x] 精准订阅功能
- [x] 主题聚合订阅功能
- [x] RSSHub集成和内容抓取

**里程碑3**：前端界面开发（4-5天）
- [x] 订阅创建界面
- [x] 内容展示界面
- [x] 订阅管理界面
- [x] 用户个人中心

**里程碑4**：测试和优化（2-3天）
- [x] 功能测试和bug修复
- [x] 性能优化
- [x] 部署配置优化

### 5.2 后期扩展阶段
- **AI功能集成**：大模型摘要、标签、对话功能
- **更多平台支持**：扩展到20+主流平台
- **高级功能**：推荐算法、社交分享等

## 六、验收标准

### 6.1 功能验收
- [x] 用户可以成功创建精准订阅和主题聚合订阅
- [x] 系统能够正确抓取和解析RSS内容
- [x] 用户界面友好，操作流程顺畅
- [x] 内容展示完整，支持收藏和跳转

### 6.2 技术验收
- [x] 代码结构清晰，符合规范
- [x] 数据库设计合理，支持扩展
- [x] API接口稳定，错误处理完善
- [x] 部署流程简单，文档完整

### 6.3 性能验收
- [x] 系统响应时间满足要求
- [x] 并发处理能力达标
- [x] 内存和磁盘使用合理

---

**文档版本**：v1.0  
**最后更新**：2024-12-XX  
**状态**：待确认 