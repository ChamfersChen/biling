# Biling（笔灵）: AI让文案随心而生

> 围绕产品文案生成、提示词管理与社区协作的统一工作台。

## 核心特性

- **产品文案生成**：填写产品信息，选择风格和渠道，一键生成适配多平台的营销文案；支持参考图片上传，辅助 AI 生图。
- **提示词管理**：集中管理 Prompt，支持变量模板（`{{variable}}`），可快速创建「产品文案模板」并与文案生成工作流无缝联动。
- **数据看板**：集中展示账户余量、历史用量、今日产出及近 7 天使用趋势图表。
- **订阅中心**：按月升级配额，支持 Stripe 在线支付和兑换码充值；配额用尽时自动引导升级。
- **社区**：浏览和分享精选提示词，支持收藏、分类筛选、评分和 Fork 复用。
- **多租户**：支持用户/部门隔离的鉴权体系。

## 技术栈

| 层面 | 技术选型 |
|------|----------|
| 后端 | Python 3.12+, FastAPI, SQLAlchemy (async), PostgreSQL |
| 前端 | Vue 3, Pinia, Vue Router, Ant Design Vue, ECharts |
| 存储 | PostgreSQL, MinIO (图片/文件) |
| 支付 | Stripe |
| 模型 | 多 LLM 提供商接入（SiliconFlow, OpenAI, 等） |

## 快速开始

### 前置依赖

- Python 3.12+
- Node.js 18+
- pnpm
- PostgreSQL
- MinIO（可选，用于图片上传）

### 1. 克隆代码

```shell
git clone https://github.com/ChamfersChen/biling.git
cd biling
```

### 2. 配置环境变量

```shell
cp .env.template .env
```

关键配置项：

| 变量 | 说明 | 必填 |
|------|------|------|
| `POSTGRES_URL` | PostgreSQL 连接字符串 | 是 |
| `SILICONFLOW_API_KEY` | 硅基流动 API Key（推荐） | 是 |
| `MINIO_URI` | MinIO 地址 | 图片上传时需要 |
| `MINIO_ACCESS_KEY` | MinIO Access Key | 同上 |
| `MINIO_SECRET_KEY` | MinIO Secret Key | 同上 |
| `STRIPE_SECRET_KEY` | Stripe Secret Key | 订阅支付时需要 |
| `STRIPE_WEBHOOK_SECRET` | Stripe Webhook Secret | 订阅支付时需要 |

### 3. 启动后端

```shell
# 创建虚拟环境
uv init
uv sync
source ./.venv/bin/activate  # Linux/Mac
# 或
.\.venv\Scripts\activate.bat  # Windows

# 启动服务
uv run --no-dev uvicorn server.main:app --host 0.0.0.0 --port 15050
```

### 4. 启动前端

```shell
cd web
pnpm install
pnpm run dev
```

### 5. 访问页面

前端默认运行在 `http://localhost:15173`，后端 API 在 `http://localhost:15050`。

## 项目结构

```
biling/
├── server/              # FastAPI 后端
│   ├── main.py          # 应用入口
│   ├── routers/         # API 路由模块
│   └── utils/           # 中间件、鉴权
├── src/                 # 核心业务逻辑
│   ├── config/          # 配置管理
│   ├── models/          # LLM 调用封装
│   ├── repositories/    # 数据访问层
│   ├── services/        # 业务服务层
│   ├── storage/         # PostgreSQL/MinIO 存储
│   └── utils/           # 工具函数
├── web/                 # Vue 3 前端
│   └── src/
│       ├── views/       # 页面组件
│       ├── components/  # 通用组件
│       ├── stores/      # Pinia 状态管理
│       ├── apis/        # API 调用封装
│       └── router/      # 路由配置
├── pyproject.toml       # Python 依赖
└── README.md
```

## 界面导航

```
侧边栏
├── 数据看板     → /product-content/dashboard
├── 产品文案     → /product-content/generate
├── 提示词管理   → /extensions/prompts
├── ──────────
├── 社区         → /community
└── GitHub / 用户信息
```

## 订阅方案

| 档位 | 月限额 | 价格 |
|------|--------|------|
| Free | 150 次 | 免费 |
| Pro | 1,500 次 | ¥29/月 |
| Max | 无限 | ¥79/月 |

## API Key 调用 Prompt

1. 进入「系统设置 → API Key」创建密钥
2. `GET` 请求：`http://localhost:15050/api/open/prompts/{external_id}`
3. Header：`x-api-key: {API Key}`
4. `external_id` 可在提示词管理界面选中文件复制

## 开发

```shell
# 后端开发
uv run --no-dev uvicorn server.main:app --reload --host 0.0.0.0 --port 15050

# 前端开发
cd web && pnpm run dev

# 前端构建
cd web && pnpm build
```

## License

MIT
