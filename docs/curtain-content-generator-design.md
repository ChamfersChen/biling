# 通用产品文案生成器详细设计文档

- 版本：v2.0
- 日期：2026-04-23
- 状态：可开发
- 说明：本文档已完全去除窗帘专属约束，面向通用产品（家居、电商、消费品等）

## 1. 目标与范围

### 1.1 目标

在现有 Prompta（FastAPI + Vue3）项目中，新增一个「通用产品文案生成」模块，支持不同产品品类的一键批量文案生成、图片提示词生成和图片生成，并具备多租户与订阅配额能力。

### 1.2 范围

- 保留现有多租户能力（用户/部门隔离）
- 复用现有认证、社区、提示词管理框架
- 新增产品管理、文案生成、图片提示词、生图、配额控制

### 1.3 非范围（当前版本不做）

- 广告投放自动化
- CRM/订单系统打通
- 多平台自动发布

## 2. 架构设计

### 2.1 总体架构

```text
Vue3 Frontend (/product-content/*)
        |
        v
FastAPI Router (/api/product-content/*)
        |
        v
Service Layer (content/image/subscription)
        |
        +--> LLM API (DeepSeek/OpenAI)
        +--> Image API (DALL-E/兼容接口)
        +--> PostgreSQL
        +--> MinIO
```

### 2.2 分层约束

- Router：请求解析、鉴权、参数校验、响应封装
- Service：业务编排（配额检查、生成策略、记录落库）
- Repository：数据库 CRUD 与查询
- Storage：SQLAlchemy 模型定义

## 3. 数据库设计

### 3.1 新增表：products（通用产品表）

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    category VARCHAR(64) NOT NULL,
    name VARCHAR(128) NOT NULL,
    material VARCHAR(64),
    style VARCHAR(64),
    color VARCHAR(64),
    scene VARCHAR(128),
    selling_points JSONB DEFAULT '[]'::jsonb,
    target_audience VARCHAR(128),
    price_range VARCHAR(64),
    attributes JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_user_id ON products(user_id);
CREATE INDEX idx_products_department_id ON products(department_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_created_at ON products(created_at DESC);
```

### 3.2 新增表：product_content_generations（生成记录）

```sql
CREATE TABLE product_content_generations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    channel VARCHAR(32) NOT NULL DEFAULT 'xiaohongshu',
    tone_styles JSONB NOT NULL,
    result_items JSONB NOT NULL,
    exported INTEGER NOT NULL DEFAULT 0,
    favorited INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pcg_user_id ON product_content_generations(user_id);
CREATE INDEX idx_pcg_department_id ON product_content_generations(department_id);
CREATE INDEX idx_pcg_product_id ON product_content_generations(product_id);
CREATE INDEX idx_pcg_created_at ON product_content_generations(created_at DESC);
```

### 3.3 新增表：product_usage_daily（每日用量）

```sql
CREATE TABLE product_usage_daily (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    usage_date DATE NOT NULL,
    text_generate_count INTEGER NOT NULL DEFAULT 0,
    image_prompt_count INTEGER NOT NULL DEFAULT 0,
    image_generate_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_usage_user_date UNIQUE (user_id, usage_date)
);

CREATE INDEX idx_pud_user_id ON product_usage_daily(user_id);
CREATE INDEX idx_pud_department_id ON product_usage_daily(department_id);
CREATE INDEX idx_pud_usage_date ON product_usage_daily(usage_date DESC);
```

### 3.4 新增表：product_subscriptions（订阅）

```sql
CREATE TABLE product_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    tier VARCHAR(32) NOT NULL DEFAULT 'free',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_subscription_user UNIQUE (user_id)
);

CREATE INDEX idx_ps_user_id ON product_subscriptions(user_id);
CREATE INDEX idx_ps_tier ON product_subscriptions(tier);
CREATE INDEX idx_ps_status ON product_subscriptions(status);
```

## 4. 后端详细设计

### 4.1 路由设计

新增文件：`server/routers/product_content_router.py`

路由前缀：`/api/product-content`

- `POST /generate`：生成文案 + 图片提示词
- `POST /generate-image`：根据提示词生成图片
- `GET /products`：分页查询产品
- `POST /products`：新增产品
- `PUT /products/{id}`：更新产品
- `DELETE /products/{id}`：删除产品
- `GET /generations`：分页查询生成记录
- `GET /quota`：获取配额
- `GET /subscription`：获取订阅状态

鉴权：全部使用`Depends(get_required_user)`。

### 4.2 Service 设计

新增文件：`src/services/product_content_service.py`

核心职责：

- 输入校验与默认值补全
- 配额检查与扣减
- Prompt 组装与模型调用
- 结果结构化与修复
- 生成记录与用量落库

关键方法：

- `generate_contents(user, payload)`
- `check_and_consume_quota(user_id, op_type)`
- `build_product_prompt(payload)`
- `persist_generation(...)`

新增文件：`src/services/product_image_service.py`

关键方法：

- `generate_image_from_prompt(user, prompt, size, style)`
- `upload_image_to_minio(...)`

### 4.3 Repository 设计

新增文件：`src/repositories/product_content_repository.py`

职责：

- `products` CRUD
- `product_content_generations` 创建与查询
- `product_usage_daily` upsert
- `product_subscriptions` 查询与更新

### 4.4 模型设计

新增文件：`src/storage/postgres/models_product_content.py`

模型：

- `Product`
- `ProductContentGeneration`
- `ProductUsageDaily`
- `ProductSubscription`

并在 PostgreSQL manager 初始化流程中注册 metadata。

## 5. 前端详细设计

### 5.1 路由与页面

新增路由：

- `/product-content`：模块首页
- `/product-content/generate`：主生成页
- `/product-content/history`：历史记录
- `/product-content/subscription`：订阅信息

新增页面文件：

- `web/src/views/product-content/ProductContentHomeView.vue`
- `web/src/views/product-content/ProductContentGenerateView.vue`
- `web/src/views/product-content/ProductContentHistoryView.vue`
- `web/src/views/product-content/ProductContentSubscriptionView.vue`

### 5.2 组件

新增组件：

- `ProductForm.vue`：产品信息表单
- `GenerationResult.vue`：生成结果容器
- `TextCard.vue`：文案卡片
- `ImagePromptCard.vue`：图片提示词与生图操作
- `QuotaBadge.vue`：配额提示

### 5.3 状态与接口

新增：

- `web/src/stores/productContent.js`
- `web/src/apis/product_content_api.js`

状态建议：

- `products`
- `generations`
- `currentQuota`
- `subscription`
- `isGenerating`

## 6. Prompt 与生成策略

新增文件：`src/utils/product_prompts.py`

### 6.1 输入参数

- 产品名称
- 产品类目
- 材质/风格/颜色/场景
- 卖点（selling_points）
- 目标人群（target_audience）
- 目标平台（默认小红书，可扩展抖音/淘宝）
- 风格集合（种草、促销、场景、测评、故事）
- 生成条数

### 6.2 输出规范（JSON）

```json
[
  {
    "style": "种草安利",
    "title": "...",
    "content": "...",
    "hashtags": ["#家居", "#好物"],
    "image_prompt": "..."
  }
]
```

### 6.3 质量策略

- 每条文案语气和开场不同，降低同质化
- 字数控制在 150-300 字，按风格可微调
- 避免违规导向和夸大承诺

## 7. 订阅与配额策略

档位：

- `free`：¥0，日5次，月50次
- `pro`：¥29/月，日50次，月1500次
- `enterprise`：¥99/月，无限

配额消耗规则：

- 一次文案生成请求：`text_generate_count + 1`
- 单条图片提示词生成：`image_prompt_count + 1`（默认计入）
- 单次图片生成：`image_generate_count + 1`

超限处理：

- 返回 403 + `QUOTA_EXCEEDED`
- 附带剩余额度与升级提示

## 8. API 合约（关键）

### 8.1 POST `/api/product-content/generate`

请求：

```json
{
  "product": {
    "category": "home_decor",
    "name": "现代简约地毯",
    "material": "涤纶",
    "style": "现代简约",
    "color": "灰白",
    "scene": "客厅",
    "selling_points": ["防滑", "易清洁"],
    "target_audience": "年轻家庭",
    "attributes": {"尺寸": "160x230cm"}
  },
  "count": 10,
  "styles": ["种草安利", "促销优惠", "场景描写"],
  "channel": "xiaohongshu"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "generation_id": 101,
    "product_id": 22,
    "items": [
      {
        "style": "种草安利",
        "title": "客厅氛围感提升",
        "content": "...",
        "hashtags": ["#家居", "#客厅改造"],
        "image_prompt": "..."
      }
    ],
    "quota": {
      "tier": "pro",
      "daily_remaining": 45,
      "monthly_remaining": 1490
    }
  }
}
```

### 8.2 POST `/api/product-content/generate-image`

请求：

```json
{
  "prompt": "A modern living room with minimalist gray and white carpet...",
  "size": "1024x1024",
  "style": "natural"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "image_url": "https://.../product-content/xxx.png"
  }
}
```

## 9. 多租户与安全设计

- 所有查询默认带`user_id`过滤
- 可选附加`department_id`一致性检查
- 禁止跨用户读写 products / generations / usage / subscription
- 生图接口增加速率限制

建议：

- 复用现有登录限流策略
- 增加生成接口调用日志（操作日志 + 错误日志）

## 10. 与现有模块复用点

- 认证：`server/utils/auth_middleware.py`
- 社区：复用现有模板发布与内容分发能力
- Prompt 管理：生成结果可回存提示词节点
- MinIO：复用上传链路

## 11. 实施计划（可执行）

### 11.1 第一阶段（后端基础，2-3 天）

- 新建`models_product_content.py`
- 新建`product_content_repository.py`
- 新建`product_content_service.py`
- 新建`product_content_router.py`
- 注册路由

### 11.2 第二阶段（前端主流程，2-3 天）

- 新建`product_content_api.js`与`productContent.js`
- 新建`ProductContentGenerateView.vue`与核心组件
- 完成生成、复制、导出

### 11.3 第三阶段（订阅+生图，2-3 天）

- 配额逻辑与订阅展示
- 接入图片生成 API
- 生图结果上传 MinIO 并回写记录

### 11.4 第四阶段（联动与打磨，1-2 天）

- 社区内容联动与筛选体验优化
- 错误态、空态、移动端适配
- 回归测试

## 12. 测试设计

### 12.1 单元测试

- 配额计算正确性
- 超限分支错误码
- Prompt 渲染参数校验

### 12.2 集成测试

- 登录 -> 生成 -> 历史查询
- 免费用户超限 -> 升级后恢复
- 生图失败重试与提示

### 12.3 回归测试

- 现有 Prompt 管理不受影响
- 现有社区与 Prompt 管理功能正常

## 13. 风险与应对

- 模型返回非 JSON：增加 JSON 修复与兜底
- 生图成本超预期：限制生图能力给 Pro/Enterprise
- 文案同质化：持续优化模板与风格词库
- 类目扩展冲突：通过`products.category`和`attributes`扩展

## 14. 交付物清单

- 详细设计文档（本文件）
- 后端新增模块（router/service/repository/models/prompts）
- 前端新增页面与组件
- API 合约说明
- 基础测试用例
