# COSMIC 智能文档转换平台 — E-R 图

> **说明**: 本文档使用 Mermaid `erDiagram` 语法描述 COSMIC 平台完整数据模型。  
> **对应 DDL**: `docs/ddl.sql`（SQLite）

---

## 完整 E-R 图

```mermaid
erDiagram
    USERS ||--o{ PROJECTS          : "creates"
    USERS ||--o{ PROJECT_MEMBERS   : "joins"
    PROJECTS ||--o{ PROJECT_MEMBERS : "has"
    PROJECTS ||--o{ PROJECT_ITERATIONS : "has"
    PROJECTS ||--o{ DOCUMENTS       : "contains"
    PROJECTS ||--o{ AI_TASKS        : "triggers"
    PROJECTS ||--o{ OPERATION_LOGS  : "records"
    PROJECTS ||--o{ PROJECT_MEMORIES : "memorizes"
    PROJECT_ITERATIONS ||--o| DOCUMENTS : "requirement_doc"
    PROJECT_ITERATIONS ||--o| DOCUMENTS : "cosmic_doc"
    PROJECT_ITERATIONS ||--o| DOCUMENTS : "srs_doc"
    PROJECT_ITERATIONS ||--o| PROJECT_ITERATIONS : "previous"
    DOCUMENTS ||--o{ EDIT_RECORDS   : "tracked_by"
    DOCUMENTS ||--o{ AUDIT_RECORDS  : "audited_by"
    DOCUMENTS ||--o{ AI_TASKS       : "source_of"
    DOCUMENTS ||--o{ AI_TASKS       : "produces"
    USERS ||--o{ EDIT_RECORDS      : "operates"
    USERS ||--o{ AUDIT_RECORDS     : "submits"
    USERS ||--o{ AUDIT_RECORDS     : "reviews"
    USERS ||--o{ OPERATION_LOGS    : "performs"

    PROJECT_MEMORIES {
        INTEGER id PK "记忆ID"
        INTEGER project_id FK "所属项目"
        VARCHAR category "correction/rule/preference/example"
        VARCHAR key "关键词标签(用于检索匹配)"
        TEXT content "规则/偏好文本"
        VARCHAR source "system/human_edit/audit/manual"
        INTEGER hit_count "命中次数"
        DATETIME last_used_at "上次使用时间"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME created_at "创建时间"
    }

    USERS {
        INTEGER id PK "用户ID"
        VARCHAR username UK "用户名/工号"
        VARCHAR password_hash "bcrypt哈希"
        VARCHAR display_name "显示名"
        VARCHAR role "admin/reviewer/user (reviewer为全局审核员)"
        BOOLEAN is_active "激活状态"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME created_at "创建时间"
    }

    PROJECTS {
        INTEGER id PK "项目ID"
        VARCHAR name "项目名称"
        TEXT description "项目描述"
        TEXT context_json "静态业务背景知识(JSON, AI Prompt上下文)"
        INTEGER creator_id FK "创建者"
        INTEGER current_iteration_id FK "当前活跃迭代→project_iterations.id"
        VARCHAR status "草稿/转换中/审核中/已通过"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME created_at "创建时间"
        DATETIME updated_at "更新时间"
    }

    PROJECT_ITERATIONS {
        INTEGER id PK "迭代ID"
        INTEGER project_id FK "所属项目"
        VARCHAR name "迭代名称,如v1.0/v2.0"
        VARCHAR status "draft/converting/reviewing/approved"
        INTEGER requirement_doc_id FK "需求文档→documents.id"
        INTEGER cosmic_doc_id FK "COSMIC文档→documents.id"
        INTEGER srs_doc_id FK "SRS文档→documents.id"
        INTEGER previous_iteration_id FK "上一迭代→project_iterations.id"
        TEXT change_summary "本轮变更摘要"
        BOOLEAN is_current "是否当前活跃版本"
        DATETIME published_at "审核完成发布时间"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME created_at "创建时间"
        DATETIME updated_at "更新时间"
    }

    PROJECT_MEMBERS {
        INTEGER id PK "关联ID"
        INTEGER project_id FK "项目"
        INTEGER user_id FK "用户"
        VARCHAR role "admin/editor/viewer (reviewer为全局角色,不加入成员)"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME joined_at "加入时间"
    }

    DOCUMENTS {
        INTEGER id PK "文档ID"
        INTEGER project_id FK "所属项目"
        VARCHAR type "requirement/cosmic/srs"
        VARCHAR version "版本号"
        VARCHAR source "ai/人工上传/人工编辑"
        VARCHAR status "待处理/生成中/编辑中/审核中/已通过/已驳回"
        VARCHAR title "文档标题"
        VARCHAR original_filename "原始文件名"
        VARCHAR file_path "本地存储路径"
        TEXT content_json "结构化内容JSON"
        TEXT diff_stats "修改统计JSON"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME created_at "创建时间"
        DATETIME updated_at "更新时间"
    }

    EDIT_RECORDS {
        INTEGER id PK "记录ID"
        INTEGER document_id FK "文档"
        VARCHAR action "ai生成/人工编辑/采纳建议/创建/删除"
        VARCHAR target "目标章节"
        TEXT detail "详细描述"
        INTEGER delta "字符变化量(+N/-N)"
        INTEGER created_by FK "操作人(Null=系统)"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME created_at "操作时间"
    }

    AUDIT_RECORDS {
        INTEGER id PK "记录ID"
        INTEGER document_id FK "文档"
        VARCHAR version "被审核版本"
        INTEGER submitter_id FK "提交人"
        INTEGER reviewer_id FK "审核人"
        VARCHAR status "待审核/已通过/已驳回"
        TEXT comment "审核意见"
        TEXT scores "质量评分JSON"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME submitted_at "提交时间"
        DATETIME reviewed_at "审核时间"
    }

    AI_TASKS {
        INTEGER id PK "任务ID"
        VARCHAR task_id UK "UUID"
        INTEGER project_id FK "项目"
        INTEGER source_doc_id FK "源文档"
        VARCHAR target_type "cosmic/srs"
        VARCHAR status "排队中/处理中/已完成/失败/已取消"
        INTEGER step "当前步骤"
        VARCHAR step_name "步骤名称"
        TEXT message "进度/错误信息"
        INTEGER result_doc_id FK "结果文档"
        TEXT error "失败详情"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME created_at "创建时间"
        DATETIME updated_at "更新时间"
    }

    OPERATION_LOGS {
        INTEGER id PK "日志ID"
        INTEGER project_id FK "项目"
        INTEGER user_id FK "操作人(Null=系统)"
        VARCHAR action "操作类型"
        VARCHAR target_type "对象类型"
        INTEGER target_id "对象ID"
        TEXT detail "详情JSON"
        BOOLEAN is_deleted "软删除:0-未删,1-已删"
        DATETIME created_at "操作时间"
    }
```

---

## 关系说明

### 1. 用户与项目

| 关系 | 基数 | 业务含义 |
|------|------|----------|
| `USERS -- PROJECTS` | 1:N | 一个用户可以创建多个项目 |
| `USERS -- PROJECT_MEMBERS` | 1:N | 一个用户可以加入多个项目 |
| `PROJECTS -- PROJECT_MEMBERS` | 1:N | 一个项目可以拥有多个成员 |

### 2. 项目与迭代与文档

| 关系 | 基数 | 业务含义 |
|------|------|----------|
| `PROJECTS -- PROJECT_ITERATIONS` | 1:N | 一个项目拥有多个迭代版本（v1.0、v2.0...） |
| `PROJECT_ITERATIONS -- DOCUMENTS` | 1:1×3 | 一个迭代通过三个 FK 关联各自的需求/COSMIC/SRS 文档（反向引用，避免鸡生蛋） |
| `PROJECTS -- DOCUMENTS` | 1:N | 一个项目包含全部历史文档（DOCUMENTS 仍保留 project_id） |
| `DOCUMENTS -- EDIT_RECORDS` | 1:N | 一份文档拥有多条编辑记录（修改追踪） |
| `DOCUMENTS -- AUDIT_RECORDS` | 1:N | 一份文档经历多轮审核 |

### 3. AI 转换任务

| 关系 | 基数 | 业务含义 |
|------|------|----------|
| `PROJECTS -- AI_TASKS` | 1:N | 一个项目可触发多次转换任务 |
| `DOCUMENTS -- AI_TASKS` | 1:2 | 一份文档既是任务的**源文档**(source)，也可能是**结果文档**(result) |

### 4. 操作日志

| 关系 | 基数 | 业务含义 |
|------|------|----------|
| `PROJECTS -- OPERATION_LOGS` | 1:N | 记录项目内的所有业务操作 |
| `USERS -- OPERATION_LOGS` | 1:N | 记录用户发起的操作 |

### 5. 迭代记忆

| 关系 | 基数 | 业务含义 |
|------|------|----------|
| `PROJECTS -- PROJECT_MEMORIES` | 1:N | 一个项目可积累多条 AI 迭代修正记忆（随版本迭代增长） |

**记忆数据来源**：
- **自动提炼**：用户保存编辑器内容时，系统对比 AI 原始输出与修改后差异，调用 LLM 提炼规则
- **审核触发**：审核驳回时，审核意见自动提炼为记忆条目
- **手动添加**：用户在「项目设置 > AI 偏好」中手动编写硬规则

---

## 核心约束检查清单

| 约束 | 实现位置 | 说明 |
|------|----------|------|
| 每个项目最多每种类型一份当前文档 | 应用层 | `documents(project_id, type)` 由业务代码保证唯一性 |
| 项目创建者自动成为管理员 | 应用层 | 创建项目时同步插入 `project_members` 记录，role=`admin` |
| 审核员不可审核自己提交的文档 | 应用层 | `submitter_id != reviewer_id` 在提交审核时校验 |
| 一个项目仅有一个当前迭代 | 应用层 | `is_current=1` 在项目范围内唯一，通过 `UPDATE` 重置其他迭代的 `is_current=0` |
| 项目状态自动同步自当前迭代 | 应用层 | `projects.status` 由 `current_iteration.status` 驱动，不直接修改 |
| 软删除（保留历史） | **数据库+应用层** | 所有表均有 `is_deleted` 字段，查询时默认过滤 `is_deleted=0`；删除操作实为 UPDATE `is_deleted=1` |

---

## 索引速查

| 索引名 | 表 | 字段 | 用途 |
|--------|-----|------|------|
| `idx_users_username` | users | username | 登录查询 |
| `idx_projects_creator` | projects | creator_id | 我创建的项目列表 |
| `idx_projects_status` | projects | status | 按状态筛选 |
| `idx_projects_current` | projects | current_iteration_id | 当前迭代查询 |
| `idx_pmembers_project` | project_members | project_id | 项目成员列表 |
| `idx_iter_project` | project_iterations | project_id | 项目迭代列表 |
| `idx_iter_current` | project_iterations | is_current | 查找当前迭代 |
| `idx_iter_status` | project_iterations | status | 按迭代状态筛选 |
| `idx_iter_previous` | project_iterations | previous_iteration_id | 迭代溯源 |
| `idx_docs_project` | documents | project_id | 项目文档列表 |
| `idx_docs_type` | documents | type | 按类型筛选 |
| `idx_edit_doc` | edit_records | document_id | 文档编辑历史 |
| `idx_audit_doc` | audit_records | document_id | 文档审核历史 |
| `idx_aitask_task_id` | ai_tasks | task_id | 任务状态查询 |
| `idx_oplog_project` | operation_logs | project_id | 项目操作日志 |
| `idx_memo_project` | project_memories | project_id | 项目记忆列表 |
| `idx_memo_key` | project_memories | key | 关键词检索记忆 |
| `idx_memo_category` | project_memories | category | 按类别筛选记忆 |
