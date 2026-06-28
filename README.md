# COSMIC 智能文档转换平台

> 彩讯股份（RICHINFO, 300634）内部智能文档转换平台

## 项目简介

COSMIC 是一个基于大模型的智能文档转换平台，核心能力包括：

1. **需求文档 → COSMIC 文档**：使用大模型将自然语言需求文档转换为符合 ISO/IEC 19761 标准的 COSMIC 功能用户需求（FUR）文档
2. **COSMIC 文档 → 需求规格说明书（SRS）**：将 COSMIC 模型转换为 IEEE 830 标准 SRS

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Tailwind CSS + Vue Router 4 + Axios |
| 后端 | Python 3.11 + FastAPI + SQLModel + SQLite + Uvicorn |
| AI | Kimi API (OpenAI SDK 兼容格式) |
| 文档解析 | python-docx, openpyxl |

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 18+
- npm

### 启动方式

```bash
# 1. 克隆仓库
git clone <仓库地址>
cd ai_cosmic

# 2. 一键启动（自动安装依赖并启动前后端）
python main.py
```

启动后访问：
- 前端：`http://localhost:5173`
- 后端 API：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

### 默认账号

| 账号 | 密码 | 角色 |
|------|------|------|
| `admin` | `admin123` | 全局管理员 |

## 项目结构

```
ai_cosmic/
├── main.py                 # 统一启动入口（uvicorn + vite dev）
├── backend/
│   ├── main.py             # FastAPI 应用入口
│   ├── database.py         # SQLModel 引擎 + 数据库初始化
│   ├── models.py           # 9 张 SQLModel 数据表定义
│   ├── ddl.sql             # 建表语句 + 种子数据
│   ├── cosmic.db           # SQLite 运行时数据库（.gitignore 排除）
│   ├── requirements.txt    # Python 依赖
│   ├── routers/            # API 路由
│   │   ├── auth.py         # 认证（注册/登录/JWT）
│   │   ├── projects.py     # 项目 CRUD + 成员管理
│   │   ├── documents.py    # 文档上传/下载/管理
│   │   └── iterations.py   # 项目迭代管理
│   └── dependencies.py     # 共享依赖（权限校验等）
├── frontend/
│   ├── index.html          # 入口 HTML
│   ├── vite.config.js      # Vite 配置（proxy /api → localhost:8000）
│   ├── tailwind.config.js  # Tailwind 品牌色配置
│   ├── package.json        # Node 依赖
│   └── src/
│       ├── main.js         # Vue 3 + Vue Router
│       ├── App.vue         # 根组件
│       ├── style.css       # Tailwind + 品牌 CSS 变量
│       ├── views/          # 页面视图
│       │   ├── LoginView.vue
│       │   ├── DashboardView.vue
│       │   ├── ProjectsView.vue
│       │   ├── ProjectDetailView.vue
│       │   ├── DocumentEditorView.vue
│       │   └── AuditView.vue
│       ├── components/     # 共享组件
│       │   ├── TopNav.vue
│       │   └── DocCard.vue
│       ├── api/            # API 客户端
│       └── composables/    # Vue 组合式函数
└── docs/
    ├── cosmic_prd.md       # 产品需求文档
    ├── cosmic_sdd.md       # 系统详细设计文档
    ├── ddl.sql             # 数据库 DDL（SQLite）
    └── e-r.md              # E-R 图文档
```

## 数据库设计

共 9 张表，全部启用软删除 `is_deleted BOOLEAN NOT NULL DEFAULT 0`：

1. `users` — 用户表
2. `projects` — 项目表
3. `project_members` — 项目成员关联表
4. `documents` — 文档表（三文档体系：requirement / cosmic / srs）
5. `edit_records` — 编辑记录表（人工修改量追踪）
6. `audit_records` — 审核记录表
7. `ai_tasks` — AI 转换任务状态表
8. `operation_logs` — 操作日志表
9. `project_memories` — 项目级 AI 迭代记忆/偏好库
10. `project_iterations` — 项目迭代版本表（多版本架构）

## 角色体系

| 层级 | 字段 | 可选值 |
|------|------|--------|
| 全局 | `users.role` | admin / reviewer / user |
| 项目内 | `project_members.role` | admin / editor / viewer |

- `reviewer` 为全局角色，可跨项目查看所有项目，无需加入成员

## 开发规范

- 所有删除操作均为**软删除**（UPDATE `is_deleted=1`）
- API 统一前缀 `/api`
- 前端开发服务器代理 `/api` → `http://127.0.0.1:8000`
- 品牌主色：`#E5572A`（彩讯股份官网提取）
- 文档修改需同步更新四份文档：PRD / SDD / DDL / E-R

## 许可证

内部项目，仅供彩讯股份内部使用。
