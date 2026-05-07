# 头条后端项目 (Toutiao Backend)

一个基于 **FastAPI** 构建的新闻资讯后端服务，提供用户认证、新闻浏览、收藏管理和浏览历史等核心功能。

## 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| **框架** | [FastAPI](https://fastapi.tiangolo.com/) (0.136+) | 高性能异步 Web 框架 |
| **服务器** | [Uvicorn](https://www.uvicorn.org/) (0.46+) | ASGI 服务器 |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) (2.0+) | 异步 ORM 框架 |
| **数据库** | [MySQL](https://www.mysql.com/) + [aiomysql](https://github.com/aio-libs/aiomysql) | 异步数据库驱动 |
| **缓存** | [Redis](https://redis.io/) + [redis-py](https://github.com/redis/redis-py) | 异步缓存 |
| **数据校验** | [Pydantic](https://docs.pydantic.dev/) (2.x) | 请求/响应数据模型校验 |
| **密码加密** | [PassLib](https://passlib.readthedocs.io/) + [bcrypt](https://github.com/pyca/bcrypt/) | 密码哈希存储 |
| **开发语言** | Python 3.12+ | — |

## 软件架构

架构图源文件位于 `assets/architecture.excalidraw`，可在 [Excalidraw](https://excalidraw.com) 中打开查看完整矢量图。

```
┌─────────────────────────────────────┐
│        客户端 (Mobile / Web)         │
└─────────────────┬───────────────────┘
                  │ HTTP
                  ▼
┌─────────────────────────────────────┐
│     FastAPI 入口 (main.py)          │
│     ┌─ CORS 中间件 ─┐               │
└─────────────────┬───────────────────┘
                  │
      ┌──────────┼──────────┬──────────┐
      ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│/api/news │ │/api/user │ │/api/fav. │ │/api/hist.│
└──────────┘ └──────────┘ └──────────┘ └──────────┘
      └──────────┬──────────┬──────────┘
                 │ 请求校验
                 ▼
┌─────────────────────────────────────┐
│   Schema 层 (Pydantic 校验)         │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────┐ ┌──────────────────┐
│   CRUD 层 (数据处理)    │◄────► Redis 缓存层  │
└─────────────────┬───────┘ └──────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  ORM 模型层 (SQLAlchemy 2.0)       │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│  MySQL 数据库 (aiomysql)            │
│  user | news | favorite | history   │
└─────────────────────────────────────┘

工具层 (Utils):
  auth       - Token 认证
  security   - 密码加密 (bcrypt)
  response   - 统一响应格式
  exception  - 全局异常处理
```

### 核心设计要点

- **异步全链路**: 基于 `async/await`，从 FastAPI → SQLAlchemy → aiomysql 全异步处理
- **Redis 缓存**: 新闻分类、列表、详情、浏览量均做了缓存，降低数据库压力
- **Token 认证**: 基于 UUID 的用户令牌，7 天过期，通过 `Authorization` 头传递
- **统一响应格式**: 所有接口返回 `{ code, message, data }` 结构
- **全局异常处理**: 覆盖 HTTPException、数据完整性错误、SQL 错误、未捕获异常

## 快速开始

### 环境要求

- Python 3.12+
- MySQL 8.0+
- Redis 6.0+

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd toutiao_backend
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install fastapi uvicorn sqlalchemy aiomysql pymysql redis passlib bcrypt pydantic
```

### 4. 配置数据库

确保本地 MySQL 和 Redis 服务已启动。

#### MySQL 配置

创建数据库：

```sql
CREATE DATABASE news_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

数据库连接配置在 `config/db_config.py`，默认值：

```python
ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/news_app?charset=utf8mb4"
```

> 如需修改用户名、密码或主机地址，请编辑此文件。

#### Redis 配置

Redis 连接配置在 `config/cache_conf.py`，默认值：

```python
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
```

### 5. 初始化数据库表

```bash
python -c "
import asyncio
from sqlalchemy import text
from config.db_config import async_engine
from models.users import Base as UserBase
from models.news import Base as NewsBase
from models.favorite import Base as FavBase
from models.history import Base as HistBase

async def init():
    async with async_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
        await conn.run_sync(NewsBase.metadata.create_all)
        await conn.run_sync(FavBase.metadata.create_all)
        await conn.run_sync(HistBase.metadata.create_all)
    print('数据库表创建完成')

asyncio.run(init())
"
```

### 6. 插入测试数据

```sql
-- 插入新闻分类
INSERT INTO news_category (id, name, sort_order, created_at, updated_at) VALUES
(1, '推荐', 1, NOW(), NOW()),
(2, '科技', 2, NOW(), NOW()),
(3, '体育', 3, NOW(), NOW()),
(4, '娱乐', 4, NOW(), NOW());
```

### 7. 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问：

- API 文档（Swagger UI）: http://localhost:8000/docs
- 替代文档（ReDoc）: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/

## API 接口一览

### 用户模块 `/api/user`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/user/register` | 用户注册 | 否 |
| POST | `/api/user/login` | 用户登录 | 否 |
| GET | `/api/user/info` | 获取用户信息 | 是 |
| PUT | `/api/user/update` | 修改用户信息 | 是 |
| PUT | `/api/user/password` | 修改密码 | 是 |

### 新闻模块 `/api/news`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/news/categories` | 获取新闻分类 | 否 |
| GET | `/api/news/list` | 获取新闻列表（分页） | 否 |
| GET | `/api/news/detail` | 获取新闻详情+相关推荐 | 否 |

### 收藏模块 `/api/favorite`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/favorite/check` | 检查收藏状态 | 是 |
| POST | `/api/favorite/add` | 添加收藏 | 是 |
| DELETE | `/api/favorite/remove` | 取消收藏 | 是 |
| GET | `/api/favorite/list` | 获取收藏列表 | 是 |
| DELETE | `/api/favorite/clear` | 清空收藏 | 是 |

### 历史模块 `/api/history`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/history/add` | 添加浏览记录 | 是 |
| GET | `/api/history/list` | 获取浏览历史 | 是 |
| DELETE | `/api/history/delete/{id}` | 删除单条记录 | 是 |
| DELETE | `/api/history/clear` | 清空历史记录 | 是 |

## 项目结构

```
toutiao_backend/
├── main.py                 # 应用入口，FastAPI 实例
├── config/
│   ├── db_config.py        # MySQL 数据库异步连接配置
│   └── cache_conf.py       # Redis 缓存连接配置
├── models/
│   ├── users.py            # 用户 & 令牌 ORM 模型
│   ├── news.py             # 新闻 & 分类 ORM 模型
│   ├── favorite.py         # 收藏 ORM 模型
│   └── history.py          # 浏览历史 ORM 模型
├── schemas/
│   ├── Base.py             # 基础 Pydantic 模型
│   ├── users.py            # 用户请求/响应模型
│   ├── news.py             # 新闻请求/响应模型
│   ├── favorite.py         # 收藏请求/响应模型
│   └── history.py          # 历史请求/响应模型
├── routers/
│   ├── users.py            # 用户路由
│   ├── news.py             # 新闻路由
│   ├── favorite.py         # 收藏路由
│   └── history.py          # 历史路由
├── crud/
│   ├── users.py            # 用户 CRUD
│   ├── news.py             # 新闻 CRUD（无缓存）
│   ├── news_cache.py       # 新闻 CRUD（带缓存）
│   ├── favorite.py         # 收藏 CRUD
│   └── history.py          # 历史 CRUD
├── cache/
│   └── news_cache.py       # 缓存 Key 定义与操作
├── utils/
│   ├── auth.py             # Token 认证依赖
│   ├── security.py         # 密码加密与验证
│   ├── response.py         # 统一响应格式
│   ├── exception.py        # 异常处理定义
│   └── exception_handlers.py # 全局异常注册
└── assets/
    └── architecture.excalidraw  # 架构图源文件
```
