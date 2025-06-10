# RSS智能订阅器

基于RSSHub和LLM的智能个人订阅器，提供智能内容筛选、摘要生成和个性化推荐功能。

## 项目简介

RSS智能订阅器是一个现代化的RSS聚合平台，旨在解决信息获取渠道多、筛选难、体验差的问题。通过集成RSSHub和大语言模型，为用户提供智能化的内容订阅和推荐服务。

### 核心功能

- **🔍 智能搜索订阅系统** ⭐ **NEW v0.5.0**
  - 统一搜索框：一键搜索所有支持的订阅模板
  - URL智能解析：支持微博、B站等平台URL自动参数提取
  - 关键词匹配：支持中文、英文、平台名称多维度搜索
  - 参数自动填充：URL解析后自动填充订阅参数

- **📋 模板化订阅配置** ⭐ **NEW v0.5.0**
  - JSON驱动配置：灵活的模板系统，易于扩展新平台
  - 参数验证系统：完整的输入校验和错误提示
  - 热重载支持：配置文件变更自动生效
  - 安全隔离：前端无法获取RSS源地址

- **🎯 双模式订阅系统**
  - 精准订阅：按平台+用户/内容维度精确订阅
  - 主题聚合：跨平台关键词聚合订阅

- **🤖 智能内容处理**
  - 自动内容抓取和更新
  - 智能内容筛选和去重
  - AI摘要生成和分类
  - 个性化推荐

- **💻 用户友好界面**
  - 现代化Web界面设计
  - 移动端适配
  - 直观的订阅配置
  - 丰富的内容展示

- **⚡ 扩展性设计**
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

当前v0.5.0版本支持以下平台：

### 🎬 哔哩哔哩 (Bilibili)
- 🎥 **UP主视频订阅**: 订阅指定UP主的最新视频投稿
- 📝 **UP主动态订阅**: 订阅指定UP主的动态和互动内容
- 🔗 **URL支持**: `https://space.bilibili.com/{uid}`

### 📱 微博 (Weibo)  
- 👤 **用户动态订阅**: 订阅指定用户的最新微博动态
- 🔍 **关键词搜索**: 搜索包含特定关键词的微博内容
- 🔗 **URL支持**: `https://weibo.com/u/{uid}`

### ⚡ 即刻 (Jike)
- 👤 **用户动态订阅**: 订阅指定用户的最新动态
- 🎯 **圈子动态订阅**: 订阅指定圈子的内容更新
- 🔗 **URL支持**: `https://web.okjike.com/u/{uid}`

### 🚀 即将支持 (v0.6.0+)
- **知乎**: 用户动态、话题内容、专栏文章
- **GitHub**: 仓库动态、用户活动、Release更新  
- **掘金**: 用户文章、标签内容、沸点动态
- **豆瓣**: 用户动态、小组讨论、影评书评

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
- **订阅搜索**: `/api/v1/subscription-search/*` ⭐ **NEW v0.5.0**
- 内容管理: `/api/v1/content/*`
- 系统监控: `/api/v1/health/*`

### v0.5.0 新增搜索API：
- `GET /search` - 模板搜索接口
- `POST /parse-url` - URL解析接口  
- `GET /platforms` - 支持平台列表
- `POST /validate-parameters` - 参数验证接口
- `GET /template/{id}` - 模板详情接口

## 开发进展

当前版本：**v0.5.0** - 搜索驱动架构完成 🚀

- [x] v0.1 - 需求分析和核心验证
- [x] v0.2 - 前后端项目初始化  
- [x] v0.3 - 核心功能开发
- [x] v0.4 - 基础订阅功能
- [x] **v0.5.0 - 搜索驱动架构** ⭐ **最新完成**
  - ✅ 统一搜索接口实现
  - ✅ URL智能解析系统
  - ✅ 模板化配置架构
  - ✅ 参数验证和错误处理
  - ✅ 完整API端点开发
- [ ] v0.6.0 - 前端搜索界面
- [ ] v0.7.0 - 用户体验优化
- [ ] v0.8.0 - 系统完善

详细进展请查看：
- [v0.5.0里程碑报告](docs/progress/milestone-v0.5.0.md)
- [功能完成清单](docs/progress/feature-checklist.md)
- [架构重构方案](docs/backend-refactor-plan.md)

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