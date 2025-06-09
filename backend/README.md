# RSS智能订阅器后端服务

基于FastAPI的RSS聚合和智能订阅平台后端服务。

## 项目简介

RSS智能订阅器后端提供RESTful API接口，支持：
- 用户认证和管理
- RSS订阅配置和管理
- 内容抓取和存储
- 智能内容筛选和推荐
- 定时任务调度

## 技术栈

- **Python**: 3.12+
- **Web框架**: FastAPI
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy
- **任务调度**: APScheduler
- **RSS解析**: feedparser
- **日志**: loguru
- **代码质量**: black, isort, flake8, mypy

## 快速开始

### 1. 环境准备

确保已安装 Python 3.12+ 和 Poetry：

```bash
# 检查Python版本
python --version

# 安装Poetry（如果未安装）
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. 安装依赖

```bash
# 进入后端目录
cd backend

# 安装项目依赖
poetry install

# 激活虚拟环境
poetry shell
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
vim .env
```

### 4. 启动开发服务器

```bash
# 直接运行
python app/main.py

# 或使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问：
- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## API文档

### 认证相关
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/me` - 获取用户信息

### 订阅管理
- `POST /api/v1/subscriptions/` - 创建订阅
- `GET /api/v1/subscriptions/` - 获取订阅列表
- `GET /api/v1/subscriptions/{id}` - 获取订阅详情
- `PUT /api/v1/subscriptions/{id}` - 更新订阅
- `DELETE /api/v1/subscriptions/{id}` - 删除订阅

### 内容管理
- `GET /api/v1/content/` - 获取内容列表
- `GET /api/v1/content/{id}` - 获取内容详情
- `POST /api/v1/content/{id}/favorite` - 收藏内容
- `DELETE /api/v1/content/{id}/favorite` - 取消收藏
- `GET /api/v1/content/search/` - 搜索内容

### 系统监控
- `GET /api/v1/health/` - 基础健康检查
- `GET /api/v1/health/detailed` - 详细健康检查

## 开发工具

### 代码格式化
```bash
# 格式化代码
black app/
isort app/

# 检查代码质量
flake8 app/
mypy app/
```

### 运行测试
```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 预提交钩子
```bash
# 安装预提交钩子
pre-commit install

# 手动运行检查
pre-commit run --all-files
```

## 项目结构

```
backend/
├── app/                    # 应用程序代码
│   ├── api/               # API路由
│   │   └── api_v1/       # API v1版本
│   │       ├── api.py    # 主路由文件
│   │       └── endpoints/ # 各功能端点
│   ├── core/             # 核心功能
│   │   └── config.py     # 配置管理
│   ├── db/               # 数据库相关
│   ├── models/           # 数据模型
│   ├── services/         # 业务逻辑服务
│   ├── utils/            # 工具函数
│   └── main.py           # 应用入口
├── tests/                # 测试文件
├── pyproject.toml        # Poetry配置
├── env.example           # 环境变量示例
└── README.md            # 项目文档
```

## 部署

### Docker部署
```bash
# 构建镜像
docker build -t rss-backend .

# 运行容器
docker run -p 8000:8000 rss-backend
```

### 生产环境
```bash
# 安装生产依赖
poetry install --no-dev

# 使用Gunicorn部署
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 许可证

MIT License 