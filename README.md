# RSS智能订阅器

基于RSSHub和LLM的智能个人订阅器，提供智能内容筛选、摘要生成和个性化推荐功能。

## 项目简介

RSS智能订阅器是一个现代化的RSS聚合平台，旨在解决信息获取渠道多、筛选难、体验差的问题。通过集成RSSHub和大语言模型，为用户提供智能化的内容订阅和推荐服务。

### 核心功能

- **双模式订阅系统**
  - 精准订阅：按平台+用户/内容维度精确订阅
  - 主题聚合：跨平台关键词聚合订阅

- **智能内容处理**
  - 自动内容抓取和更新
  - 智能内容筛选和去重
  - AI摘要生成和分类
  - 个性化推荐

- **用户友好界面**
  - 现代化Web界面设计
  - 移动端适配
  - 直观的订阅配置
  - 丰富的内容展示

- **扩展性设计**
  - 模块化架构
  - 插件式平台支持
  - RESTful API
  - Docker容器化部署

## 技术架构

### 前端
- **框架**: Next.js 14 + React 18
- **样式**: Tailwind CSS
- **语言**: TypeScript
- **状态管理**: React Hooks
- **UI组件**: 自定义组件库

### 后端
- **框架**: FastAPI + Python 3.12
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy
- **任务调度**: APScheduler
- **缓存**: Redis
- **RSS解析**: feedparser

### 部署
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **CI/CD**: GitHub Actions
- **监控**: 日志和健康检查

## 支持平台

当前MVP版本支持以下平台：

- **哔哩哔哩**: 用户动态、用户视频、关键词搜索
- **微博**: 用户微博、关键词搜索
- **知乎**: 用户动态、话题内容
- **GitHub**: 仓库动态、用户活动
- **掘金**: 用户文章、标签内容

## 快速开始

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
poetry run python app/main.py
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

## 项目结构

```
RSS/
├── backend/                 # FastAPI后端服务
│   ├── app/                # 应用程序代码
│   │   ├── api/           # API路由
│   │   ├── core/          # 核心功能
│   │   ├── models/        # 数据模型
│   │   └── services/      # 业务逻辑
│   ├── tests/             # 测试文件
│   └── pyproject.toml     # Python依赖配置
├── frontend/               # Next.js前端应用
│   ├── src/               # 源代码
│   │   ├── app/          # App Router
│   │   ├── components/   # React组件
│   │   └── lib/          # 工具函数
│   └── package.json      # Node.js依赖配置
├── docs/                  # 项目文档
│   ├── meetings/         # 会议记录
│   ├── progress/         # 开发进展
│   └── requirements/     # 需求文档
├── docker-compose.yml    # Docker编排配置
└── README.md            # 项目说明
```

## API文档

详细的API文档可在后端服务启动后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

主要接口：
- 认证管理: `/api/v1/auth/*`
- 订阅管理: `/api/v1/subscriptions/*`
- 内容管理: `/api/v1/content/*`
- 系统监控: `/api/v1/health/*`

## 开发进展

当前版本：**v0.2** - 基础架构搭建

- [x] v0.1 - 需求分析和核心验证
- [x] v0.2 - 前后端项目初始化  
- [ ] v0.3 - 核心功能开发
- [ ] v0.4 - 用户体验优化
- [ ] v0.5 - 系统完善

详细进展请查看 [功能完成清单](docs/progress/feature-checklist.md)

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目地址: [GitHub Repository]
- 问题反馈: [Issues]
- 讨论区: [Discussions]

---

**RSS智能订阅器** - 让信息获取更智能、更高效！ 