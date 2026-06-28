# COSMIC 智能文档转换平台 — 系统设计文档 (SDD)

> **版本**: v1.1
> **日期**: 2026-06-25
> **公司**: cgm股份（CGM）
> **定位**: 基于 Kimi AI 的文档智能转换平台技术实现方案

---

## 1. 设计约束与前提

### 1.1 运行环境

| 项目 | 规格 |
|------|------|
| **服务器** | Apple Mac Mini M2（8GB/16GB RAM） |
| **网络** | 公司内部局域网，需访问公网调用 Kimi API |
| **用户数** | 内部使用，预估并发 < 10 人 |
| **存储** | 本地 SSD，文档 + SQLite 数据库 |
| **运维人员** | 无专职开发人员，系统需极简部署与维护 |

### 1.2 核心约束

1. **零外部依赖**: 不购买云服务（服务器、数据库、对象存储均本地）
2. **零运维复杂度**: 不用 Docker、Kubernetes、消息队列
3. **AI 不本地**: Mac Mini M2 跑大模型吃力，统一调用 Kimi API
4. **单文件部署**: 理想状态下 `python main.py` 即可启动整个系统
5. **数据可备份**: SQLite + 文件目录可直接复制备份

---

## 2. 总体架构

### 2.1 架构图

```
┌───────────────────────────────────────────────────────────────────┐
│                       Mac Mini M2 (本地)                          │
│                                                                   │
│  ┌─────────────────────┐         ┌──────────────────────────┐    │
│  │   前端 (Vue 3 SPA)   │         │    后端 (FastAPI)         │    │
│  │   Vite Build         │ ←────→ │    Uvicorn ASGI           │    │
│  │   静态文件托管        │  HTTP   │    Python 3.11+           │    │
│  └─────────────────────┘         └───────────┬──────────────┘    │
│                                               │                   │
│                              ┌────────────────┼────────────────┐ │
│                              ↓                ↓                ↓ │
│                         ┌─────────┐    ┌──────────┐    ┌────────┐│
│                         │ SQLite  │    │ uploads/ │    │ Kimi   ││
│                         │ .db     │    │ 文件存储  │    │ API    ││
│                         └─────────┘    └──────────┘    └────────┘│
│                              ↑                                  │
│                              │                                  │
│                         ┌───────────────────────┐                │
│                         │   备份:定时复制      │                │
│                         │   .db + uploads/     │                │
│                         └───────────────────────┘                │
└───────────────────────────────────────────────────────────────────┘

外部依赖:
- Moonshot AI (Kimi) API: https://api.moonshot.cn
- 公司内网用户通过局域网 IP 访问 (如 http://192.168.x.x:8000)
```

### 2.2 技术栈明细

| 层级 | 技术选型 | 版本 | 说明 |
|------|----------|------|------|
| **前端框架** | Vue 3 | ^3.4 | Composition API，单文件组件 |
| **构建工具** | Vite | ^5.0 | 极速开发服务器，生产打包 |
| **CSS 框架** | Tailwind CSS | ^3.4 | 原子化 CSS，与 Vue 3 集成良好 |
| **UI 组件** | Headless UI + 自建 | - | 轻量级，无需引入 Element Plus 等重型库 |
| **HTTP 客户端** | Axios | ^1.6 | 后端 API 调用 |
| **路由** | Vue Router | ^4.2 | SPA 路由管理 |
| **状态管理** | Pinia | ^2.1 | 官方推荐，TypeScript 友好 |
| **后端框架** | FastAPI | ^0.109 | 高性能异步 API，自动生成 Swagger 文档 |
| **数据校验** | Pydantic | ^2.5 | 请求/响应模型定义 |
| **ORM** | SQLModel | ^0.0.14 | FastAPI 官方推荐，基于 SQLAlchemy |
| **数据库** | SQLite | 3.x | 内嵌式，零配置 |
| **文件处理** | python-docx, openpyxl | latest | Word/Excel 读写 |
| **AI SDK** | openai (兼容) | ^1.0 | Kimi API 兼容 OpenAI SDK 格式 |
| **ASGI 服务器** | Uvicorn | ^0.27 | 单进程单线程足够（可加 workers） |
| **进程守护** | launchd | - | macOS 原生服务管理，开机自启 |

---

## 3. 数据库设计

### 3.1 ER 图

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    User      │       │   Project    │       │  Document    │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │◄───── │ id (PK)      │◄───── │ id (PK)      │
│ username     │   1:N │ name         │  1:N   │ project_id   │
│ password_hash│       │ creator_id   │       │ type         │
│ role         │       │ current_iter │       │ version      │
│ created_at   │       │ status       │       │ source       │
└──────────────┘       └──────┬───────┘       │ status       │
       ▲                      │               │ file_path    │
       │                      │ 1:N           │ content_json │
       │                      ↓               │ diff_stats   │
       │               ┌──────────────┐       │ created_at   │
       │               │ProjectIterat │       └──────────────┘
       │               ├──────────────┤              │
       │               │ id (PK)      │              │
       │               │ project_id   │◄─────────────┘
       │               │ name         │       (via FK refs)
       │               │ status       │       req/cos/srs
       │               │ req_doc_id   │
       │               │ cos_doc_id   │
       │               │ srs_doc_id   │
       │               │ prev_iter_id │
       │               │ is_current   │
       │               │ change_sum   │
       │               └──────────────┘
       │                      │
       │                      │
       │                      │ self-ref
       │                      ↓
       │               ┌──────────────┐
       │               │ AuditRecord  │
       │               ├──────────────┤
       │               │ ...          │
       │               └──────────────┘
       │
       │         ┌───────────────────────────┐
       │         │
       │    ┌────┴────┐                      ┌──────────────┐
       │    │ Project  │                      │ EditRecord   │
       │    │ Member   │                      ├─────────────┤
       │    ├─────────┤                      │ id (PK)     │
       └─── │ user_id │                      │ document_id │
            │ role    │                      │ action      │
            └─────────┘                      │ delta       │
                                             │ created_by  │
                                             │ created_at  │
                                             └─────────────┘
```

### 3.2 表结构定义

#### 3.2.1 `users` — 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | |
| username | VARCHAR(64) | NOT NULL, UNIQUE | 用户名/工号 |
| password_hash | VARCHAR(256) | NOT NULL | bcrypt 哈希 |
| display_name | VARCHAR(64) | | 显示名 |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'user' | `admin` / `user` |
| is_active | BOOLEAN | DEFAULT 1 | |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT 0 | 软删除: 0-未删除, 1-已删除 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |

#### 3.2.2 `projects` — 项目表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | |
| name | VARCHAR(256) | NOT NULL | 项目名称 |
| description | TEXT | | 项目描述 |
| context_json | TEXT | | 静态业务背景知识（JSON，AI Prompt 上下文） |
| creator_id | INTEGER | FK → users.id | 创建者 |
| current_iteration_id | INTEGER | FK → project_iterations.id, ON DELETE SET NULL | 当前活跃迭代 |
| status | VARCHAR(32) | DEFAULT 'draft' | `draft`/`converting`/`reviewing`/`approved`（自动同步自当前迭代） |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT 0 | 软删除: 0-未删除, 1-已删除 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |

#### 3.2.3 `project_iterations` — 项目迭代版本表（v1.1 新增）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | |
| project_id | INTEGER | NOT NULL, FK → projects.id, ON DELETE CASCADE | 所属项目 |
| name | VARCHAR(64) | NOT NULL | 迭代名称，如 `v1.0`、`v2.0` |
| status | VARCHAR(32) | DEFAULT 'draft' | `draft`/`converting`/`reviewing`/`approved` |
| requirement_doc_id | INTEGER | FK → documents.id, ON DELETE SET NULL | 该迭代的需求文档 |
| cosmic_doc_id | INTEGER | FK → documents.id, ON DELETE SET NULL | 该迭代的 COSMIC 文档 |
| srs_doc_id | INTEGER | FK → documents.id, ON DELETE SET NULL | 该迭代的 SRS 文档 |
| previous_iteration_id | INTEGER | FK → project_iterations.id, ON DELETE SET NULL | 上一迭代（溯源） |
| change_summary | TEXT | | 本轮变更摘要 |
| is_current | BOOLEAN | NOT NULL, DEFAULT 0 | 是否当前活跃版本 |
| published_at | DATETIME | | 审核完成发布时间 |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT 0 | 软删除 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |

#### 3.2.4 `project_members` — 项目成员关联表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | |
| project_id | INTEGER | FK → projects.id, ON DELETE CASCADE | |
| user_id | INTEGER | FK → users.id, ON DELETE CASCADE | |
| role | VARCHAR(32) | NOT NULL, DEFAULT 'editor' | `admin`/`editor`/`reviewer`/`viewer` |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT 0 | 软删除: 0-未删除, 1-已删除 |
| joined_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |

#### 3.2.4 `documents` — 文档表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | |
| project_id | INTEGER | FK → projects.id, ON DELETE CASCADE | |
| type | VARCHAR(32) | NOT NULL | `requirement` / `cosmic` / `srs` |
| version | VARCHAR(16) | DEFAULT 'v1.0' | 版本号 |
| source | VARCHAR(32) | DEFAULT 'manual' | `ai` / `manual_upload` / `manual_edit` |
| status | VARCHAR(32) | DEFAULT 'pending' | `pending`/`generating`/`editing`/`reviewing`/`approved`/`rejected` |
| title | VARCHAR(256) | | 文档标题 |
| original_filename | VARCHAR(512) | | 原始上传文件名 |
| file_path | VARCHAR(512) | | 本地存储相对路径 |
| content_json | TEXT | | 结构化内容（JSON 字符串，用于编辑器渲染）|
| diff_stats | TEXT | | 修改统计JSON |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT 0 | 软删除: 0-未删除, 1-已删除 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |

#### 3.2.5 `edit_records` — 编辑记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | |
| document_id | INTEGER | FK → documents.id | |
| action | VARCHAR(32) | NOT NULL | `ai_generate`/`human_edit`/`accept_suggestion`/`create`/`delete` |
| target | VARCHAR(256) | | 目标章节/段落 |
| detail | TEXT | | 详细描述 |
| delta | INTEGER | DEFAULT 0 | 字符变化量（+N / -N）|
| created_by | INTEGER | FK → users.id | 操作人（NULL=系统/AI）|
| is_deleted | BOOLEAN | NOT NULL, DEFAULT 0 | 软删除: 0-未删除, 1-已删除 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |

#### 3.2.6 `audit_records` — 审核记录表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | |
| document_id | INTEGER | FK → documents.id | |
| version | VARCHAR(16) | | 被审核的版本 |
| submitter_id | INTEGER | FK → users.id | 提交人 |
| reviewer_id | INTEGER | FK → users.id | 审核人 |
| status | VARCHAR(32) | DEFAULT 'pending' | `pending`/`approved`/`rejected` |
| comment | TEXT | | 审核意见 |
| scores | TEXT | | JSON: `{completeness, accuracy, consistency, compliance}` |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT 0 | 软删除: 0-未删除, 1-已删除 |
| submitted_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |
| reviewed_at | DATETIME | | |

#### 3.2.7 `project_memories` — 项目级 AI 迭代记忆/偏好库

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTOINCREMENT | |
| project_id | INTEGER | FK → projects.id, ON DELETE CASCADE | 所属项目 |
| category | VARCHAR(32) | NOT NULL, DEFAULT 'general' | `correction`(修正) / `rule`(规则) / `preference`(偏好) / `example`(案例) |
| key | VARCHAR(128) | | 关键词标签，用于检索匹配 |
| content | TEXT | NOT NULL | 记忆的具体规则/偏好文本 |
| source | VARCHAR(32) | NOT NULL, DEFAULT 'system' | `system`(自动提炼) / `human_edit`(编辑触发) / `audit`(审核触发) / `manual`(手动添加) |
| hit_count | INTEGER | NOT NULL, DEFAULT 1 | 被检索命中次数 |
| last_used_at | DATETIME | | 上次使用时间 |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT 0 | 软删除 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | |

---

## 4. API 设计

### 4.1 接口概览

| 分组 | 前缀 | 说明 |
|------|------|------|
| **认证** | `/api/auth` | 登录、登出、获取当前用户 |
| **用户** | `/api/users` | 用户 CRUD（管理员） |
| **项目** | `/api/projects` | 项目 CRUD、成员管理 |
| **迭代** | `/api/projects/{id}/iterations` + `/api/iterations/{id}` | 迭代版本 CRUD、切换当前版本 |
| **文档** | `/api/documents` | 文档 CRUD、上传下载、转换 |
| **编辑** | `/api/edits` | 编辑历史、保存内容 |
| **审核** | `/api/audits` | 审核提交、通过/驳回、列表 |
| **AI** | `/api/ai` | 触发转换、获取进度 |

### 4.2 核心接口定义

#### 4.2.1 认证接口

```python
# POST /api/auth/login
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# GET /api/auth/me
class UserOut(BaseModel):
    id: int
    username: str
    display_name: str | None
    role: str
```

使用 JWT（`python-jose` + `passlib`）做无状态认证，token 有效期 7 天（内部系统无需频繁登录）。

#### 4.2.2 项目接口

```python
# POST /api/projects
class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    context_json: str | None = None

# GET /api/projects
# Query: page=1, page_size=20, search=""
class ProjectList(BaseModel):
    total: int
    items: list[ProjectOut]

# GET /api/projects/{id}
class ProjectOut(BaseModel):
    id: int
    name: str
    description: str | None
    context_json: str | None
    creator: UserOut
    status: str                     # 自动同步自 current_iteration.status
    members: list[MemberOut]
    documents: list[DocumentOut]    # 项目级全部文档（兼容旧接口）
    current_iteration: IterationOut | None   # 当前活跃迭代（含三文档）
    iterations: list[IterationSummaryOut]    # 所有迭代摘要列表
    created_at: datetime
    updated_at: datetime

# POST /api/projects/{id}/members
class MemberInvite(BaseModel):
    username: str                   # 工号/用户名
    role: str = "editor"            # admin/editor/reviewer/viewer

# DELETE /api/projects/{id}/members/{user_id}
```

#### 4.2.3 迭代接口（v1.1 新增）

```python
# POST /api/projects/{project_id}/iterations
class IterationCreate(BaseModel):
    name: str | None = None         # 默认自动生成 v{N}.0
    change_summary: str | None = None
    previous_iteration_id: int | None = None

# Response: 新建迭代，自动设置 is_current=True，旧迭代 is_current=False

# GET /api/projects/{project_id}/iterations
class IterationSummaryOut(BaseModel):
    id: int
    name: str
    status: str
    is_current: bool
    previous_iteration_id: int | None
    published_at: datetime | None
    created_at: datetime

# GET /api/iterations/{iteration_id}
class IterationOut(BaseModel):
    id: int
    project_id: int
    name: str
    status: str
    is_current: bool
    change_summary: str | None
    previous_iteration_id: int | None
    published_at: datetime | None
    documents: dict[str, DocumentOut | None]   # {"requirement": ..., "cosmic": ..., "srs": ...}
    created_at: datetime
    updated_at: datetime

# PUT /api/iterations/{iteration_id}
class IterationUpdate(BaseModel):
    name: str | None = None
    change_summary: str | None = None
    is_current: bool | None = None   # 设为 True 时自动切换项目 current_iteration_id

# DELETE /api/iterations/{iteration_id}
# 软删除；若删除的是当前迭代，自动将剩余最新迭代设为 current
```

#### 4.2.5 文档接口

```python
# POST /api/projects/{project_id}/documents
# Content-Type: multipart/form-data
# Fields: project_id, type (requirement/cosmic/srs), file, iteration_id (可选)

# GET /api/projects/{project_id}/documents
# Query: iteration_id (可选) — 如有则仅返回该迭代关联的文档

# GET /api/documents/{id}
class DocumentOut(BaseModel):
    id: int
    project_id: int
    type: str
    version: str
    source: str
    status: str
    title: str | None
    original_filename: str
    file_path: str
    content_json: dict | None  # 解析后的结构化内容
    diff_stats: DiffStats | None
    edit_history: list[EditRecordOut]
    audit_records: list[AuditRecordOut]
    created_at: datetime
    updated_at: datetime

# GET /api/documents/{id}/download
# 返回文件流 (StreamingResponse)

# POST /api/documents/{id}/content
# 保存编辑器中的结构化内容
class ContentSave(BaseModel):
    content_json: dict
    diff_stats: DiffStats

class DiffStats(BaseModel):
    total_chars: int
    ai_chars: int
    human_added: int
    human_deleted: int
    modified_blocks: int
```

#### 4.2.4 AI 转换接口

```python
# POST /api/ai/convert-to-cosmic
class ConvertRequest(BaseModel):
    project_id: int
    requirement_doc_id: int  # 源需求文档

# Response: { "task_id": str, "status": "queued" }

# POST /api/ai/convert-to-srs
class ConvertToSRSRequest(BaseModel):
    project_id: int
    cosmic_doc_id: int

# GET /api/ai/tasks/{task_id}
class TaskStatus(BaseModel):
    task_id: str
    status: str  # queued / processing / completed / failed
    step: int | None  # 当前步骤 1-5
    step_name: str | None
    message: str | None
    result_doc_id: int | None
    error: str | None
    created_at: datetime
    updated_at: datetime

# POST /api/ai/tasks/{task_id}/cancel
```

转换任务在后端使用 Python `asyncio.create_task()` 后台执行，无需 Celery。任务状态保持在内存字典中（内部系统重启概率低，如需持久化可写入 SQLite）。

#### 4.2.5 审核接口

```python
# POST /api/audits/submit
class AuditSubmit(BaseModel):
    document_id: int
    version: str
    comment: str | None = None

# GET /api/audits
# Query: status=pending/approved/rejected, page=1, page_size=20

# POST /api/audits/{id}/review
class AuditReview(BaseModel):
    status: str  # approved / rejected
    comment: str
    scores: Scores | None = None

class Scores(BaseModel):
    completeness: int  # 0-100
    accuracy: int
    consistency: int
    compliance: int
```

---

## 5. AI 集成设计（Kimi）

### 5.1 SDK 选型

Kimi API 完全兼容 OpenAI SDK 格式，使用 `openai` Python 包即可：

```python
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key="sk-xxx",           # Kimi API Key
    base_url="https://api.moonshot.cn/v1"
)
```

### 5.2 Prompt 工程架构

将复杂转换拆分为**多步骤调用**，降低单次 Prompt 的复杂度：

#### 步骤 1: 需求文档 → COSMIC（5 步流水线）

```
[步骤 1/5] 提取功能用户
Prompt: "请从以下需求文档中提取所有功能用户（Functional Users），
        按 COSMIC ISO 19761 标准分类..."

[步骤 2/5] 识别功能过程
Prompt: "基于以下需求文档和已识别的功能用户 {users}，
        列出所有功能过程（Functional Processes）..."

[步骤 3/5] 识别触发事件
Prompt: "为每个功能过程识别触发事件（Trigger Events）..."

[步骤 4/5] 分析数据移动
Prompt: "分析每个功能过程的数据移动（Entry/Exit/Read/Write），
        标注 CFP 值..."

[步骤 5/5] 汇总生成
Prompt: "将以上分析汇总为标准的 COSMIC FUR 表格格式（Markdown），
        包含：功能过程、触发事件、功能用户、数据移动列表、CFP总计..."
```

#### 步骤 2: COSMIC → SRS（3 步流水线）

```
[步骤 1/3] 转换功能需求
Prompt: "将以下 COSMIC 功能过程转换为 IEEE 830 标准的功能需求描述章节..."

[步骤 2/3] 推导接口与数据
Prompt: "根据数据移动分析，推导系统接口需求和数据需求..."

[步骤 3/3] 生成完整 SRS
Prompt: "生成完整的 SRS 文档，包含：引言、总体描述、详细需求（功能/接口/数据）、
        非功能需求、验收标准..."
```

#### 步骤 3: 迭代记忆注入（project_memories）

在每个步骤的 Prompt 组装阶段，系统会从 `project_memories` 表中检索与当前步骤相关的历史修正偏好，注入 Prompt 头部：

```python
async def build_cosmic_prompt(step: int, project_id: int, doc_text: str):
    # 1. 检索相关记忆（关键词匹配 + 命中次数排序）
    step_keywords = {
        1: ["功能用户", "Functional User", "系统边界"],
        2: ["功能过程", "Functional Process", "拆分", "合并"],
        3: ["触发事件", "Trigger Event"],
        4: ["数据移动", "Data Movement", "Entry", "Exit", "Read", "Write", "CFP"],
        5: ["汇总", "表格", "总计"],
    }
    memories = retrieve_memories(project_id, keywords=step_keywords[step], limit=8)
    
    # 2. 组装三层 Prompt
    prompt = f"""
【系统规则：COSMIC ISO 19761 计数规则】
{cosmic_rules}

【项目静态上下文】
{project_context.domain} / {project_context.system_name}
功能用户：{...}

【⚠️ 本项目迭代修正偏好】
{format_memories(memories)}

【需求文档内容】
{doc_text}

【任务】步骤 {step}/5...
"""
    return prompt
```

记忆的**自动提炼流程**：当用户对 AI 生成的 COSMIC 文档做人工编辑并保存后，系统对比 AI 原始输出与用户修改后的差异，调用 Kimi 提炼出一条可执行的规则，存入 `project_memories`。具体实现逻辑见 §5.5 Prompt Memory Extractor。

### 5.3 结构化输出

使用 Kimi 的 JSON Mode 强制返回结构化数据：

```python
response = await client.chat.completions.create(
    model="moonshot-v1-128k",
    messages=[
        {"role": "system", "content": "你是一个 COSMIC 功能规模度量专家..."},
        {"role": "user", "content": prompt}
    ],
    response_format={"type": "json_object"},  # 强制 JSON 输出
    temperature=0.2,  # 低温度，减少创造性，增加确定性
)

cosmic_data = json.loads(response.choices[0].message.content)
# 预期结构: {"functional_users": [...], "processes": [...], "total_cfp": N}
```

### 5.4 Token 与成本估算

| 文档规模 | 预估 Token | 单次转换成本（按 128k 模型）|
|----------|------------|----------------------------|
| 小型（< 5000 字） | 10K-20K | ~0.1-0.2 元 |
| 中型（5000-20000 字） | 20K-50K | ~0.2-0.5 元 |
| 大型（20000-50000 字） | 50K-120K | ~0.5-1.2 元 |

提示优化策略：
- 先用 `moonshot-v1-8k` 做小文档测试（更便宜）
- 超长文档（> 5 万字）使用 `moonshot-v1-128k`
- 开启 Prompt 缓存（如果 Kimi 支持）降低重复调用成本

### 5.5 后台任务执行

```python
import asyncio
from typing import Dict

# 内存中的任务状态存储
_tasks: Dict[str, dict] = {}

async def run_cosmic_conversion(task_id: str, doc_id: int):
    """在后台执行 COSMIC 转换"""
    _tasks[task_id] = {"status": "processing", "step": 1}

    try:
        # 1. 读取需求文档
        doc = await get_document(doc_id)
        text = await extract_text_from_docx(doc.file_path)

        # 2. 步骤 1-5 流水线
        for step_num, step_name in enumerate(STEPS, 1):
            _tasks[task_id].update({"step": step_num, "step_name": step_name})
            result = await call_kimi(step_prompt, text)
            # ... 累加结果

        # 3. 生成 Excel
        excel_path = generate_cosmic_excel(result)

        # 4. 创建文档记录
        new_doc = await create_document(type="cosmic", file_path=excel_path, ...)
        _tasks[task_id].update({"status": "completed", "result_doc_id": new_doc.id})

    except Exception as e:
        _tasks[task_id].update({"status": "failed", "error": str(e)})

# API 接口中触发后台任务
@app.post("/api/ai/convert-to-cosmic")
async def convert_to_cosmic(req: ConvertRequest):
    task_id = str(uuid.uuid4())
    asyncio.create_task(run_cosmic_conversion(task_id, req.requirement_doc_id))
    return {"task_id": task_id, "status": "queued"}
```

---

## 6. 前端架构

### 6.1 目录结构

```
frontend/
├── public/                  # 静态资源
│   └── favicon.ico
├── src/
│   ├── api/                 # API 调用封装 (axios)
│   │   ├── client.ts        # axios 实例 + 拦截器
│   │   ├── auth.ts
│   │   ├── projects.ts
│   │   ├── documents.ts
│   │   ├── ai.ts
│   │   └── audits.ts
│   ├── components/          # 通用组件
│   │   ├── AppNavbar.vue    # 顶部导航（工作台/项目管理/审核中心）
│   │   ├── AppSidebar.vue   # 侧边栏（如有需要）
│   │   ├── StatCard.vue     # 统计卡片
│   │   ├── DocStatusDot.vue # 三文档状态圆点
│   │   ├── UserAvatar.vue   # 用户头像（姓名字母+渐变背景）
│   │   └── ProjectPipeline.vue  # 转换流程可视化（文→表→规→审）
│   ├── views/               # 页面（与 PRD 5 个页面对应）
│   │   ├── LoginView.vue        # 登录页
│   │   ├── DashboardView.vue    # 工作台
│   │   ├── ProjectsView.vue     # 项目管理（列表+详情）
│   │   ├── EditorView.vue       # 文档编辑器
│   │   └── AuditView.vue        # 审核中心
│   ├── composables/         # 组合式函数
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts
│   │   └── useTasks.ts      # AI 任务轮询
│   ├── stores/              # Pinia 状态管理
│   │   ├── auth.ts
│   │   ├── project.ts
│   │   └── task.ts
│   ├── router/              # Vue Router
│   │   └── index.ts
│   ├── types/               # TypeScript 类型
│   │   └── index.ts
│   ├── App.vue
│   └── main.ts
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── package.json
```

### 6.2 路由设计

```typescript
const routes = [
  { path: '/login', name: 'Login', component: LoginView, meta: { public: true } },

  // 需认证的路由
  {
    path: '/',
    component: LayoutWithNav,  // 包含顶部导航的通用布局
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'Dashboard', component: DashboardView },
      { path: 'projects', name: 'Projects', component: ProjectsView },
      { path: 'projects/:id', name: 'ProjectDetail', component: ProjectsView },
      { path: 'editor/:docId', name: 'Editor', component: EditorView },
      { path: 'audit', name: 'Audit', component: AuditView },
    ]
  }
]
```

### 6.3 关键组件设计

#### EditorView.vue（文档编辑器 — 三栏布局）

```vue
<template>
  <div class="flex h-screen">
    <!-- 左栏：大纲 -->
    <aside class="w-64 border-r border-gray-200 overflow-y-auto">
      <OutlineTree :content="document.content_json" @jump="scrollToSection" />
    </aside>

    <!-- 中栏：编辑区 -->
    <main class="flex-1 flex flex-col min-w-0">
      <!-- 工具栏 -->
      <EditorToolbar
        @save="handleSave"
        @undo="handleUndo"
        @ai-assist="showAiSuggestion"
        @submit-audit="submitAudit"
      />
      <!-- 可编辑区域 -->
      <div class="flex-1 overflow-y-auto p-8 bg-white">
        <EditableDocument
          v-model="document.content_json"
          :blocks="blocks"
          @change="trackChanges"
        />
      </div>
    </main>

    <!-- 右栏：统计 -->
    <aside class="w-72 border-l border-gray-200 overflow-y-auto p-4">
      <DiffStatsCard :stats="diffStats" />
      <SessionTimer :start-time="sessionStart" />
      <EditHistory :records="editHistory" />
    </aside>
  </div>
</template>
```

### 6.4 状态管理设计

```typescript
// stores/project.ts (Pinia)
export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)

  const fetchProjects = async (params?: { search?: string; page?: number }) => {
    const res = await api.projects.list(params)
    projects.value = res.items
  }

  const fetchProjectDetail = async (id: number) => {
    currentProject.value = await api.projects.get(id)
  }

  const updateDocumentStatus = (type: DocType, status: string) => {
    if (currentProject.value?.documents[type]) {
      currentProject.value.documents[type]!.status = status
    }
  }

  return { projects, currentProject, fetchProjects, fetchProjectDetail, updateDocumentStatus }
})
```

---

## 7. 文件存储设计

### 7.1 存储目录结构

```
backend/
├── uploads/                  # 所有上传/生成文件
│   ├── 2026/
│   │   ├── 06/
│   │   │   ├── 24/
│   │   │   │   ├── req_ xxxxxx_电商平台需求分析.docx    # 需求文档
│   │   │   │   ├── cosmic_ xxxxxx_电商平台需求分析.xlsx # COSMIC 文档
│   │   │   │   └── srs_ xxxxxx_电商平台需求分析.docx    # SRS 文档
│   │   │   └── 25/
│   │   │       └── ...
│   └── temp/                 # 临时文件（转换中间产物）
│       └── task_xxxxxx/
│           ├── step1_result.json
│           ├── step2_result.json
│           └── final.xlsx
├── cosmic.db                 # SQLite 数据库
├── main.py                   # 入口文件
└── ...
```

### 7.2 文件命名规则

```python
def generate_filename(doc_type: str, project_name: str, ext: str) -> str:
    """生成存储文件名"""
    prefix = {"requirement": "req", "cosmic": "cosmic", "srs": "srs"}[doc_type]
    date_str = datetime.now().strftime("%Y%m%d")
    rand = secrets.token_hex(4)
    safe_name = re.sub(r'[^\w一-鿿]+', '_', project_name)[:30]
    return f"{prefix}_{date_str}_{rand}_{safe_name}.{ext}"
```

### 7.3 文件服务

FastAPI 直接提供静态文件下载：

```python
from fastapi import FileResponse

@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: int, db: Session = Depends(get_db)):
    doc = get_document(db, doc_id)
    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,  # 用户看到的原始文件名
        media_type="application/octet-stream"
    )

# 前端 build 产物也由 FastAPI 托管
app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")
```

---

## 8. 部署方案

### 8.1 目录结构（部署时）

```
/opt/cosmic/                 # 部署根目录（可自定义）
├── backend/
│   ├── venv/                # Python 虚拟环境
│   ├── app/                 # 源码
│   ├── uploads/             # 文件存储
│   ├── cosmic.db            # 数据库
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   └── dist/                # Vue build 产物
└── scripts/
    ├── start.sh             # 启动脚本
    ├── backup.sh            # 备份脚本
    └── install.sh           # 首次安装脚本
```

### 8.2 首次安装脚本 (`scripts/install.sh`)

```bash
#!/bin/bash
set -e

echo "=== COSMIC 平台安装脚本 ==="

# 1. 安装 Homebrew（如无）
if ! command -v brew &> /dev/null; then
    echo "安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 2. 安装 Python 3.11
brew install python@3.11

# 3. 安装 Node.js (for build)
brew install node

# 4. 创建虚拟环境
cd backend
python3.11 -m venv venv
source venv/bin/activate

# 5. 安装 Python 依赖
pip install -r requirements.txt

# 6. 初始化数据库
cd app
python init_db.py

echo "=== 安装完成 ==="
echo "启动命令: ./scripts/start.sh"
```

### 8.3 启动脚本 (`scripts/start.sh`)

```bash
#!/bin/bash
cd backend
source venv/bin/activate

# 环境变量
export KIMI_API_KEY="sk-xxx"
export SECRET_KEY="$(openssl rand -hex 32)"
export UPLOAD_DIR="/opt/cosmic/backend/uploads"

# 启动
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info
```

### 8.4 macOS launchd 开机自启

创建 `~/Library/LaunchAgents/com.richinfo.cosmic.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" ...>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.richinfo.cosmic</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/opt/cosmic/scripts/start.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/opt/cosmic</string>
    <key>StandardOutPath</key>
    <string>/opt/cosmic/logs/cosmic.out.log</string>
    <key>StandardErrorPath</key>
    <string>/opt/cosmic/logs/cosmic.err.log</string>
</dict>
</plist>
```

加载命令：
```bash
launchctl load ~/Library/LaunchAgents/com.richinfo.cosmic.plist
launchctl start com.richinfo.cosmic
```

### 8.5 备份脚本 (`scripts/backup.sh`)

```bash
#!/bin/bash
BACKUP_DIR="/Volumes/ExternalDrive/cosmic-backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# 1. 备份数据库
cp /opt/cosmic/backend/cosmic.db "$BACKUP_DIR/cosmic_$DATE.db"

# 2. 备份文件
rsync -av /opt/cosmic/backend/uploads/ "$BACKUP_DIR/uploads_$DATE/"

# 3. 保留最近 30 份
ls -t "$BACKUP_DIR"/*.db | tail -n +31 | xargs rm -f

echo "备份完成: $DATE"
```

建议配置 `crontab -e`：
```
# 每天凌晨 3 点备份
0 3 * * * /opt/cosmic/scripts/backup.sh >> /opt/cosmic/logs/backup.log 2>&1
```

---

## 9. 安全设计

### 9.1 认证与授权

- **密码存储**: `passlib[bcrypt]` 哈希，成本因子 12
- **JWT 认证**: `python-jose` HS256 签名，有效期 7 天
- **路由守卫**: FastAPI Dependencies 检查 `user.role`
- **项目权限**: 中间件检查当前用户是否在项目成员列表中

### 9.2 文件安全

- 上传文件校验 MIME 类型（仅允许 `.docx`, `.xlsx`, `.pdf`, `.txt`）
- 文件路径使用 UUID + 日期目录，防止遍历攻击
- 不执行任何用户上传文件的内容

### 9.3 API 安全

- CORS 配置为仅允许内部网段（如 `192.168.1.*`）
- 所有写入接口需认证（`Depends(get_current_user)`）
- 速率限制：下载用 `slowapi` 限制单 IP 每秒 10 次请求

### 9.4 密钥管理

敏感配置通过环境变量注入，不写入代码：

```bash
# .env 文件（不提交到 git）
KIMI_API_KEY=sk-xxx
SECRET_KEY=xxx
DATABASE_URL=sqlite:///./cosmic.db
```

---

## 10. 性能考量

### 10.1 SQLite 性能优化

| 优化项 | 配置 | 说明 |
|--------|------|------|
| WAL 模式 | `PRAGMA journal_mode=WAL;` | 读写并发提升 10 倍 |
| 同步模式 | `PRAGMA synchronous=NORMAL;` | 性能与安全的平衡 |
| 缓存大小 | `PRAGMA cache_size=-64000;` | 64MB 页缓存 |
| 索引 | `CREATE INDEX` | 外键字段、查询字段建立索引 |

### 10.2 AI 调用优化

- **连接池**: `httpx.AsyncClient` 复用 HTTP 连接
- **并发控制**: 使用 `asyncio.Semaphore(3)` 限制同时 3 个 Kimi 请求
- **超时设置**: 单次调用 120 秒超时，长文档转换整体 600 秒超时
- **结果缓存**: 相同文档内容 MD5 哈希的转换结果缓存 1 小时

### 10.3 前端性能

- Vite build 开启代码分割（路由级 lazy loading）
- 编辑器大文档使用虚拟滚动（长列表优化）
- 图片/文件使用 HTTP 缓存头

---

## 11. 开发计划与里程碑

| 阶段 | 时长 | 交付物 | 关键技术点 |
|------|------|--------|------------|
| **Phase 1: 骨架** | 1-2 天 | 可运行的前后端 | FastAPI + Vue 3 路由打通，SQLite 连接 |
| **Phase 2: 文件管理** | 2-3 天 | 项目+文档 CRUD | 文件上传下载，三文档关联 |
| **Phase 3: AI 转换** | 3-5 天 | 需求→COSMIC→SRS | Kimi API 集成，Prompt 工程，Excel/Word 生成 |
| **Phase 4: 编辑器** | 2-3 天 | 带追踪的编辑器 | contenteditable，diff 统计，历史记录 |
| **Phase 5: 审核** | 2 天 | 审核工作流 | 审核状态机，评论，质量评分 |
| **Phase 6: 成员与日志** | 2 天 | 完整协作功能 | 成员邀请，操作日志 UI |
| **Phase 7: 部署** | 1-2 天 | 生产环境就绪 | launchd，备份脚本，内网访问配置 |

### 最小可运行版本 (MVP)

完成 Phase 1-3 即可内部试用：
- 用户能创建项目、上传需求文档
- 点击"AI 转 COSMIC"，等待几分钟后拿到 Excel
- 再点击"AI 转 SRS"，拿到 Word
- 可以下载两个文档

---

## 12. 风险与应对

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|----------|
| Kimi API 余额不足 | 中 | 高 | 监控余额，设置告警阈值；备用方案切换至阿里云通义千问 |
| Mac Mini 硬盘故障 | 低 | 高 | 每日自动备份到 NAS/外接硬盘 |
| 超长文档超出 Kimi 上下文 | 中 | 中 | 实现分块处理策略：按章节拆分→逐章转换→合并结果 |
| AI 生成质量不稳定 | 高 | 中 | 保留人工编辑入口为核心功能；Prompt 持续迭代优化 |
| 单点故障（无热备） | 高 | 中 | 接受风险（内部系统）；备份策略确保数据可恢复 |
| 网络隔离无法调用 API | 低 | 高 | 部署本地模型（ollama + qwen2.5），质量降级但可用 |

---

## 13. 附录

### Appendix A: 完整依赖清单

**requirements.txt**

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlmodel==0.0.14
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
openai==1.10.0
python-docx==1.1.0
openpyxl==3.1.2
httpx==0.26.0
aiofiles==23.2.1
python-dotenv==1.0.0
```

**package.json (前端)**

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0",
    "vue-tsc": "^1.8.0"
  }
}
```

### Appendix B: 开发环境启动命令

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev          # http://localhost:5173
```

### Appendix C: 生产构建命令

```bash
# 1. 构建前端
cd frontend
npm run build        # 生成 dist/ 目录

# 2. 确保 dist 在 FastAPI 静态文件路径中
# 3. 启动后端（已包含前端静态服务）
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

---

**文档结束**
