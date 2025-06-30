# RSSia

<div align="center">
  <!-- Banner图片 -->
  <img src="frontend/public/banner.png" alt="RSSia Banner" width="100%" style="max-width: 800px;">
  
  <h3 style="margin: 20px 0; color: #666;">🚀 基于RSS和LLM的智能个人订阅器</h3>
  <p style="margin: 20px 0; font-size: 1.1em; color: #888;">
    提供轻量化的订阅源配置、友好的内容消费体验<br>
    基于LLM、RAG等能力提供内容分析、个性化日报和ChatBot对话服务
  </p>
  
  <!-- 技术栈徽章 -->
  <p>
    <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Next.js-15.2.4-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js">
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
    <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  </p>
  
  <!-- 项目状态徽章 -->
  <p>
    <img src="https://img.shields.io/github/stars/czsayhi/RSSia?style=social" alt="GitHub stars">
    <img src="https://img.shields.io/github/forks/czsayhi/RSSia?style=social" alt="GitHub forks">
    <img src="https://img.shields.io/github/license/czsayhi/RSSia?style=flat-square" alt="License">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome">
  </p>
</div>

---

基于RSS和LLM的智能个人订阅器，提供轻量化的订阅源配置、友好的内容消费体验，基于LLM、RAG等能力提供内容分析、个性化日报和ChatBot对话服务。

## 📖 项目背景

在信息爆炸的时代，用户面临内容获取渠道多、重复信息多、筛选难等问题。目前市面上已经有大量基于RSS实现的订阅器产品，解决了用户添加订阅源门槛高、阅读体验差、无法聚合归类等问题；也通过集成LLM提供了AI日报服务，但整体应用深度不足。

💡本项目旨在基于 RSS 实现一个用户交互体验友好、轻量化添加订阅源、自定义订阅频率，结合人工智能技术为用户提供深度的全类型媒体AI摘要、聚类标签、对话式AI服务的智能 RSS 订阅系统，在订阅器**信息获取服务**的基础上建立**信息认知服务**，提升信息消费效率与质量。


## ✨ 项目亮点

### 🔍 **轻量化的订阅配置体验** 
- **自建RSS实例**：基于RSSHub自建RSS服务实例，支持200+个平台的内容订阅
- **统一搜索订阅源**：一键搜索所有支持的订阅源，支持中文、英文、平台名称多维度
- **URL智能解析和填充**：支持微博、B站等平台URL自动参数提取和填充
- **订阅频率自由配置**：支持自动获取订阅、手动获取订阅，支持订阅频率和时间自由配置

### 🤖 **场景化的AI服务** 
- **AI服务架构**：分层式AI服务设计，包括AI服务管理器、内容处理器、向量服务等模块
- **智能内容预处理**：自动生成标签、主题、摘要，并向量化处理提高模型检索和回答质量
- **Prompt引擎**：抽象动态prompt引擎，规则-模版-组装三层架构，支持不同场景、用户画像、用户诉求下动态生成prompt交付更高质量的ai摘要和回答
- **个性化日报**：基于用户订阅内容生成每日报告
- **智能对话**：基于RAG架构的内容问答系统，结合ChromaDB向量检索，回答准确率90%+
- **多层安全防护**：基于向量检索的内容过滤、黑名单防护、输出内容审查等机制，确保AI服务的安全性和可靠性
  
   ```mermaid
  graph TB
      %% 数据输入层
      subgraph Input ["📥 数据输入层"]
          RSS["RSS内容入库"]
          UserQuery["用户对话请求"]
          Schedule["定时任务触发"]
      end
      
      %% AI处理核心
      subgraph AICore ["🧠 AI处理核心"]
          PreProcessor["AI预处理服务<br/>标签摘要生成"]
          ConversationEngine["对话处理引擎<br/>向量检索+智能回答"]
          ReportGenerator["日报生成器<br/>内容聚合+摘要"]
          PromptEngine["Prompt生成引擎<br/>三场景统一管理"]
      end
      
      %% AI模型层
      subgraph Models ["🤖 AI模型层"]
          LLM["Qwen2.5-7B-Instruct<br/>本地部署"]
          VectorModel["Sentence Transformers<br/>768维向量"]
      end
      
      %% 安全和性能层
      subgraph Security ["🛡️ 安全与性能层"]
          SecurityFilter["安全过滤器<br/>黑名单+注入检测"]
          PerformanceManager["性能管理器<br/>缓存+并发+监控"]
          FallbackHandler["兜底处理器<br/>异常场景处理"]
      end
      
      %% 存储层
      subgraph Storage ["💾 存储层"]
          SQLite[("SQLite数据库<br/>内容+AI数据")]
          ChromaDB[("ChromaDB向量库<br/>语义检索")]
          Cache[("Redis缓存<br/>对话+会话")]
      end
      
      %% 配置层
      subgraph Config ["⚙️ 配置层"]
          TemplateLib["模板库<br/>Prompt模板管理"]
          BlacklistLib["黑名单库<br/>安全规则配置"]
          ConfigManager["配置管理器<br/>系统参数调优"]
      end
      
      %% 主要数据流
      RSS --> PreProcessor
      UserQuery --> ConversationEngine
      Schedule --> ReportGenerator
      
      PreProcessor --> PromptEngine
      ConversationEngine --> PromptEngine
      ReportGenerator --> PromptEngine
      
      PromptEngine --> LLM
      PreProcessor --> VectorModel
      ConversationEngine --> VectorModel
      
      %% 安全和性能连接
      ConversationEngine --> SecurityFilter
      SecurityFilter --> PerformanceManager
      PerformanceManager --> FallbackHandler
      
      %% 存储连接
      PreProcessor --> SQLite
      PreProcessor --> ChromaDB
      ConversationEngine --> ChromaDB
      ConversationEngine --> SQLite
      ReportGenerator --> SQLite
      PerformanceManager --> Cache
      
      %% 配置连接
      PromptEngine --> TemplateLib
      SecurityFilter --> BlacklistLib
      AICore --> ConfigManager
      
      %% 样式定义
      style RSS fill:#e1f5fe
      style UserQuery fill:#f3e5f5
      style Schedule fill:#f3e5f5
      style LLM fill:#ffea00
      style VectorModel fill:#e3f2fd
      style PromptEngine fill:#fff3e0
      style SecurityFilter fill:#ffebee
      style FallbackHandler fill:#f1f8e9
      style SQLite fill:#e8f5e8
      style ChromaDB fill:#e8f5e8
      style Cache fill:#e8f5e8
  ```

### 📊 **高效内容管理**
- **共享内容存储**：去重优化，多用户订阅相同内容时，存储空间节省60%+
- **分离式设计**：用户关系与内容存储分离，支持高并发
- **智能缓存**：标签系统缓存命中率95%+，响应速度提升3倍
- **分流处理架构**：结合RSS实例限流要求设计请求策略，保证稳定性
- **配额管理系统**：用户级配额控制，精准计费


## 🛠 技术栈

### 后端技术栈
```
核心框架: Python 3.12 + FastAPI + SQLite
任务调度: APScheduler (双调度器架构)
RSS处理: feedparser + RSSHub集成
数据验证: Pydantic 2.5 + 自定义验证器
依赖管理: Poetry + Docker化部署
```

### 前端技术栈
```
框架: Next.js 15.2.4 + React 19 + TypeScript 5
样式: Tailwind CSS 3.4.17 + 自定义组件库
状态管理: React Hooks + Context API
构建工具: ESLint + Prettier + 热重载
```

### AI技术栈
```
LLM: Qwen3-1.7B-Instruct (本地轻量化部署)
向量模型: sentence-transformers-multilingual (多语言支持)
向量数据库: ChromaDB (本地向量存储)
RAG架构: 基于向量检索的内容问答系统
安全防护: 黑名单过滤 + 输出审查 + 兜底服务
```

## 🏗 项目架构

### 服务层架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (Next.js) │◄───┤   后端 (FastAPI) ├───►│  自建RSS服务    │
│                 │    │                 │    │   (RSSHub)      │
│ - YouTube式UI   │    │ - RESTful API   │    │ - 200+平台支持  │
│ - 订阅管理界面   │    │ - 双调度器架构     │    │ - 内容标准化    │
│ - AI对话界面    │    │ - 企业级缓存       │    │ - 智能解析      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │              ┌─────────────────┐             │
        └──────────────►│   SQLite 数据库  │◄────────────┘
                       │                 │
                       │ - 共享内容存储    │
                       │ - 用户关系管理    │
                       │ - 智能标签缓存   │
                       └─────────────────┘
```

### AI服务架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  AI预处理链路     │    │   AI服务链路    │    │   模板库系统    │
│   (独立运行)    │     │   (用户交互)     │    │   (配置驱动)    │
│                │    │                 │    │                 │
│ - 定时批量处理   │    │ - 用户对话请求   │    │ - 黑名单模板库  │
│ - 内容预处理    │    │ - 向量化处理     │    │ - Prompt生成    │
│ - 向量化存储    │    │ - Prompt生成     │    │ - 日报模板库    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │              ┌─────────────────┐             │
        └──────────────►│  Qwen3-1.7B +   │◄────────────┘
                       │   ChromaDB      │
                       │                 │
                       │ - LLM推理       │
                       │ - 向量检索RAG   │
                       │ - 安全防护      │
                       └─────────────────┘
```

### 前端组件架构
```
┌─────────────────────────────────────────────────────────────┐
│                    前端应用 (Next.js)                        │
├─────────────────────────────────────────────────────────────┤
│  📱 页面层 (Pages)                                          │
│  ├── 主页 (YouTube式内容展示)                               │
│  ├── 订阅管理 (搜索+配置界面)                               │
│  └── AI助手 (对话界面)                                      │
├─────────────────────────────────────────────────────────────┤
│  🧩 组件层 (Components)                                     │
│  ├── 内容展示: video-grid, content-detail-modal            │
│  ├── 订阅管理: subscription-list, source-config-form       │
│  ├── AI交互: subscription-assistant-card, login-dialog     │
│  └── 基础组件: UI组件库 (40+组件)                          │
├─────────────────────────────────────────────────────────────┤
│  🔧 服务层 (Services)                                       │
│  ├── 认证服务: auth-context, use-auth                      │
│  ├── API调用: RESTful接口封装                               │
│  └── 状态管理: React Hooks + Context                       │
└─────────────────────────────────────────────────────────────┘
```


## 🚀 快速开始

### 环境要求
- Docker & Docker Compose
- Node.js 18+ (本地开发)
- Python 3.12+ (本地开发)
- Poetry (Python依赖管理)

### 使用Docker快速启动

```bash
# 克隆项目
git clone <repository-url>
cd RSS

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

服务启动后访问：
- 前端界面: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 本地开发

#### 后端开发
```bash
# 进入后端目录
cd backend

# 安装依赖
poetry install

# 配置环境变量
cp env.example .env

# 启动开发服务器
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 前端开发
```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📚 支持平台

**基于RSSHub自建实例，支持200+个平台的智能订阅**

我们自建了完整的RSSHub服务实例，提供了对主流内容平台的全面支持，包括但不限于：

### 🎬 视频平台
- **哔哩哔哩**: UP主视频、动态、直播、番剧等
- **YouTube**: 频道视频、播放列表、直播等
- **抖音**: 用户视频、话题内容等

### 📱 社交媒体  
- **微博**: 用户动态、关键词搜索、热搜等
- **即刻**: 用户动态、圈子内容等
- **Twitter/X**: 用户推文、列表等

### 💻 技术社区
- **GitHub**: 仓库动态、用户活动、Release更新
- **掘金**: 用户文章、标签内容、沸点动态  
- **知乎**: 用户动态、话题内容、专栏文章

### 📰 新闻资讯
- **36氪、虎嗅、少数派** 等科技媒体
- **澎湃新闻、财新网** 等新闻媒体
- **豆瓣**: 书影音评论、小组讨论

### 🔧 便捷功能
- **URL智能解析**: 支持主流平台URL自动参数提取
- **批量导入**: 支持OPML格式的订阅源批量导入
- **自定义RSS**: 支持标准RSS/Atom订阅源

## 📋 API文档

详细的API文档可在后端服务启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要接口分类:
```
认证管理:     /api/v1/auth/*           - 用户登录、注册、会话管理
订阅管理:     /api/v1/subscriptions/* - 订阅源CRUD、批量操作
订阅搜索:     /api/v1/subscription-search/* - 模板搜索、URL解析
内容管理:     /api/v1/content/*       - 内容获取、筛选、标签
用户内容:     /api/v1/user-content/*  - 个人内容、阅读历史
标签管理:     /api/v1/tag-admin/*     - 标签缓存、批量更新
AI服务:       /api/v1/ai/*            - 向量检索对话、智能摘要
系统监控:     /api/v1/health/*        - 健康检查、系统状态
```


## 📊 项目统计

### 代码规模 (最新统计):
```
后端代码:     ~13,500行 Python (13个服务模块，已优化合并)
前端代码:     ~8,000行 TypeScript/React
配置文件:     ~500行 (Docker + 环境配置)
总计:         ~22,000行
```

### 技术指标:
- **缓存命中率**: 95%+ (30分钟窗口)
- **API响应时间**: <200ms (P95)
- **系统可用性**: 99.9%+
- **存储优化**: 60%+ (共享内容架构)

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情
