-- COSMIC 智能文档转换平台 — 数据库 DDL (SQLite)
-- 版本: v1.1
-- 日期: 2026-06-25
-- 公司: 彩讯股份（RICHINFO，股票代码: 300634）

-- =====================================================
-- 性能优化 PRAGMA（在连接后执行）
-- =====================================================
-- PRAGMA journal_mode = WAL;
-- PRAGMA synchronous = NORMAL;
-- PRAGMA cache_size = -64000;       -- 64MB 页缓存
-- PRAGMA foreign_keys = ON;         -- 启用外键约束
-- PRAGMA temp_store = MEMORY;

-- =====================================================
-- 1. users — 用户表
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      VARCHAR(64)  NOT NULL UNIQUE,          -- 用户名/工号
    password_hash VARCHAR(256) NOT NULL,                  -- bcrypt 哈希（成本因子 12）
    display_name  VARCHAR(64),                            -- 显示名
    role          VARCHAR(20)  NOT NULL DEFAULT 'user',   -- admin / reviewer / user
    is_active     BOOLEAN      NOT NULL DEFAULT 1,
    is_deleted    BOOLEAN      NOT NULL DEFAULT 0,          -- 软删除 0-未删除，1-已删除
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- =====================================================
-- 2. projects — 项目表
-- =====================================================
CREATE TABLE IF NOT EXISTS projects (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    name                 VARCHAR(256) NOT NULL,                   -- 项目名称
    description          TEXT,                                     -- 项目描述
    context_json         TEXT,                                    -- 静态业务背景知识（AI Prompt 上下文，JSON 格式：领域、术语表、功能用户等）
    creator_id           INTEGER      NOT NULL,
    current_iteration_id INTEGER,                                 -- 当前活跃迭代 FK → project_iterations.id
    status               VARCHAR(32)  NOT NULL DEFAULT 'draft',   -- draft / converting / reviewing / approved
    is_deleted           BOOLEAN      NOT NULL DEFAULT 0,         -- 软删除 0-未删除，1-已删除
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (current_iteration_id) REFERENCES project_iterations(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_creator   ON projects(creator_id);
CREATE INDEX IF NOT EXISTS idx_projects_status    ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_current   ON projects(current_iteration_id);
CREATE INDEX IF NOT EXISTS idx_projects_created   ON projects(created_at);

-- =====================================================
-- 3. project_members — 项目成员关联表（N:M 拆分为 1:N）
-- =====================================================
CREATE TABLE IF NOT EXISTS project_members (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER     NOT NULL,
    user_id    INTEGER     NOT NULL,
    role       VARCHAR(32) NOT NULL DEFAULT 'editor',  -- admin / editor / viewer  （reviewer 为全局系统角色，不加入项目成员）
    is_deleted BOOLEAN     NOT NULL DEFAULT 0,         -- 软删除 0-未删除，1-已删除
    joined_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,

    UNIQUE (project_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_pmembers_project ON project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_pmembers_user    ON project_members(user_id);

-- =====================================================
-- 4. documents — 文档表（三文档体系：requirement / cosmic / srs）
-- =====================================================
CREATE TABLE IF NOT EXISTS documents (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id        INTEGER      NOT NULL,
    type              VARCHAR(32)  NOT NULL,            -- requirement / cosmic / srs
    version           VARCHAR(16)  NOT NULL DEFAULT 'v1.0',
    source            VARCHAR(32)  NOT NULL DEFAULT 'manual_upload',  -- ai / manual_upload / manual_edit
    status            VARCHAR(32)  NOT NULL DEFAULT 'pending',        -- pending / generating / editing / reviewing / approved / rejected
    title             VARCHAR(256),                                    -- 文档标题
    original_filename VARCHAR(512),                                    -- 原始上传文件名
    file_path         VARCHAR(512),                                    -- 本地存储相对路径（指向 uploads/ 目录）
    content_json      TEXT,                                            -- 结构化内容（JSON 字符串，用于编辑器渲染）
    diff_stats        TEXT,                                            -- 修改统计 JSON
    is_deleted        BOOLEAN      NOT NULL DEFAULT 0,                 -- 软删除 0-未删除，1-已删除
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,

    -- 每个项目每种类型理论上只应有一份当前版本（业务层保证，不强制 UNIQUE 以便留档）
    CHECK (type IN ('requirement', 'cosmic', 'srs')),
    CHECK (source IN ('ai', 'manual_upload', 'manual_edit')),
    CHECK (status IN ('pending', 'generating', 'editing', 'reviewing', 'approved', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_docs_project  ON documents(project_id);
CREATE INDEX IF NOT EXISTS idx_docs_type     ON documents(type);
CREATE INDEX IF NOT EXISTS idx_docs_status   ON documents(status);
CREATE INDEX IF NOT EXISTS idx_docs_created  ON documents(created_at);

-- =====================================================
-- 5. edit_records — 编辑记录表（修改追踪核心）
-- =====================================================
CREATE TABLE IF NOT EXISTS edit_records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  INTEGER      NOT NULL,
    action       VARCHAR(32)  NOT NULL,                  -- ai_generate / human_edit / accept_suggestion / create / delete
    target       VARCHAR(256),                            -- 目标章节/段落描述
    detail       TEXT,                                    -- 详细描述（JSON 或纯文本）
    delta        INTEGER     NOT NULL DEFAULT 0,        -- 字符变化量（+N / -N）
    is_deleted   BOOLEAN     NOT NULL DEFAULT 0,        -- 软删除 0-未删除，1-已删除
    created_by   INTEGER,                                 -- 操作人 user_id（NULL 表示系统/AI 操作）
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by)  REFERENCES users(id)    ON DELETE SET NULL,

    CHECK (action IN ('ai_generate', 'human_edit', 'accept_suggestion', 'create', 'delete'))
);

CREATE INDEX IF NOT EXISTS idx_edit_doc    ON edit_records(document_id);
CREATE INDEX IF NOT EXISTS idx_edit_user   ON edit_records(created_by);
CREATE INDEX IF NOT EXISTS idx_edit_action ON edit_records(action);
CREATE INDEX IF NOT EXISTS idx_edit_time   ON edit_records(created_at);

-- =====================================================
-- 6. audit_records — 审核记录表
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  INTEGER     NOT NULL,
    version      VARCHAR(16) NOT NULL,                   -- 被审核的文档版本号
    submitter_id INTEGER     NOT NULL,                   -- 提交人
    reviewer_id  INTEGER,                                -- 审核人（NULL 表示尚未分配/审核中）
    status       VARCHAR(32) NOT NULL DEFAULT 'pending', -- pending / approved / rejected
    comment      TEXT,                                   -- 审核意见
    scores       TEXT,                                   -- JSON：{ completeness, accuracy, consistency, compliance }
    is_deleted   BOOLEAN     NOT NULL DEFAULT 0,         -- 软删除 0-未删除，1-已删除
    submitted_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at  DATETIME,                               -- 审核完成时间

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (submitter_id) REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id)  REFERENCES users(id)   ON DELETE SET NULL,

    CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_audit_doc       ON audit_records(document_id);
CREATE INDEX IF NOT EXISTS idx_audit_submitter ON audit_records(submitter_id);
CREATE INDEX IF NOT EXISTS idx_audit_reviewer  ON audit_records(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_audit_status    ON audit_records(status);
CREATE INDEX IF NOT EXISTS idx_audit_time      ON audit_records(submitted_at);

-- =====================================================
-- 7. ai_tasks — AI 转换任务状态表（持久化后台任务，可选）
-- =====================================================
-- 说明：
--   SDD 中任务状态默认保存在内存字典中（_tasks），
--   如果希望重启后不丢失队列任务，可启用此表。
--   FastAPI 启动时扫描 status='queued'/'processing' 的记录并恢复执行。
-- =====================================================
CREATE TABLE IF NOT EXISTS ai_tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id      VARCHAR(64) NOT NULL UNIQUE,            -- UUID 格式任务 ID
    project_id   INTEGER     NOT NULL,
    source_doc_id INTEGER    NOT NULL,                   -- 源文档 ID
    target_type  VARCHAR(32) NOT NULL,                   -- cosmic / srs（转换目标类型）
    status       VARCHAR(32) NOT NULL DEFAULT 'queued',  -- queued / processing / completed / failed / cancelled
    step         INTEGER,                                -- 当前步骤编号（1-5 或 1-3）
    step_name    VARCHAR(64),                            -- 当前步骤名称
    message      TEXT,                                   -- 进度描述/错误信息
    result_doc_id INTEGER,                               -- 转换完成后生成的文档 ID
    error        TEXT,                                   -- 失败原因（JSON 或文本）
    is_deleted   BOOLEAN      NOT NULL DEFAULT 0,        -- 软删除 0-未删除，1-已删除
    created_at   DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id)   REFERENCES projects(id)  ON DELETE CASCADE,
    FOREIGN KEY (source_doc_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (result_doc_id) REFERENCES documents(id) ON DELETE SET NULL,

    CHECK (target_type IN ('cosmic', 'srs')),
    CHECK (status IN ('queued', 'processing', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_aitask_task_id  ON ai_tasks(task_id);
CREATE INDEX IF NOT EXISTS idx_aitask_project  ON ai_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_aitask_status   ON ai_tasks(status);

-- =====================================================
-- 8. operation_logs — 操作日志表（项目级审计）
-- =====================================================
-- 说明：
--   记录用户在项目中的关键操作，用于三文档卡片下方的"操作日志"面板展示。
--   与 edit_records 的区别：edit_records 聚焦文档内容编辑，operation_logs 聚焦业务动作。
-- =====================================================
CREATE TABLE IF NOT EXISTS operation_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER      NOT NULL,
    user_id     INTEGER,                                  -- 操作人（NULL 表示系统/AI）
    action      VARCHAR(64)  NOT NULL,                    -- upload_requirement / trigger_cosmic / trigger_srs / submit_audit / approve / reject / add_member / remove_member / edit_project
    target_type VARCHAR(32),                              -- document / project / member / system
    target_id   INTEGER,                                  -- 目标对象 ID
    detail      TEXT,                                     -- 详细内容（JSON）
    is_deleted  BOOLEAN     NOT NULL DEFAULT 0,           -- 软删除 0-未删除，1-已删除
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_oplog_project ON operation_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_oplog_user    ON operation_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_oplog_action  ON operation_logs(action);
CREATE INDEX IF NOT EXISTS idx_oplog_time    ON operation_logs(created_at);

-- =====================================================
-- 9. project_memories — 项目级 AI 迭代记忆/偏好库
-- =====================================================
-- 说明：
--   记录该项目在多次 AI 转换迭代中积累的人工修正偏好和领域计数规则。
--   每次用户人工编辑 COSMIC/SRS 文档并保存后，系统自动对比 AI 原始输出
--   与修改后的差异，提炼为记忆条目存入本表。
--   下一轮 AI 生成时，根据当前步骤关键词检索相关记忆注入 Prompt，
--   避免重复踩坑，提升迭代准确率。
--
--   与 projects.context_json 的区别：
--     - context_json：项目静态背景知识（领域、功能用户、术语表），全量注入
--     - project_memories：动态修正偏好，按需检索，支持衰减淘汰
-- =====================================================
CREATE TABLE IF NOT EXISTS project_memories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id   INTEGER      NOT NULL,                  -- 所属项目
    category     VARCHAR(32)  NOT NULL DEFAULT 'general',
                                                          -- correction(用户修正) / rule(手动规则) / preference(风格偏好) / example(案例参考)
    key          VARCHAR(128),                            -- 关键词标签，用于检索匹配（如"功能过程拆分"、"数据移动类型"）
    content      TEXT         NOT NULL,                   -- 记忆的具体规则/偏好文本（AI 生成时遵循）
    source       VARCHAR(32)  NOT NULL DEFAULT 'system',  -- system(自动提炼) / human_edit(用户编辑触发) / audit(审核驳回触发) / manual(用户手动添加)
    hit_count    INTEGER      NOT NULL DEFAULT 1,         -- 被检索命中次数，用于排序和衰减淘汰
    last_used_at DATETIME,                                -- 上次被检索使用的时间
    is_deleted   BOOLEAN      NOT NULL DEFAULT 0,         -- 软删除 0-未删除，1-已删除
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,

    CHECK (category IN ('correction', 'rule', 'preference', 'example', 'general')),
    CHECK (source IN ('system', 'human_edit', 'audit', 'manual'))
);

CREATE INDEX IF NOT EXISTS idx_memo_project  ON project_memories(project_id);
CREATE INDEX IF NOT EXISTS idx_memo_key      ON project_memories(key);
CREATE INDEX IF NOT EXISTS idx_memo_category ON project_memories(category);

-- =====================================================
-- 10. project_iterations — 项目迭代版本表（NEW v1.1）
-- =====================================================
-- 说明：
--   支持一个项目下多个独立迭代（v1.0, v2.0...）。
--   每个迭代独立拥有一组三文档（需求/COSMIC/SRS）。
--   新建迭代从零开始，不携带上一轮文档。
--   迭代通过三个 FK 反向指向 documents 表（避免上传先于创建的鸡生蛋问题）。
-- =====================================================
CREATE TABLE IF NOT EXISTS project_iterations (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id           INTEGER     NOT NULL,
    name                 VARCHAR(64) NOT NULL,               -- 迭代名称，如 "v1.0"、"v2.0"
    status               VARCHAR(32) NOT NULL DEFAULT 'draft', -- draft / converting / reviewing / approved
    requirement_doc_id   INTEGER,                              -- 该迭代的需求文档 FK
    cosmic_doc_id        INTEGER,                              -- 该迭代的 COSMIC 文档 FK
    srs_doc_id           INTEGER,                              -- 该迭代的 SRS 文档 FK
    previous_iteration_id INTEGER,                             -- 指向上一版本，方便溯源
    change_summary       TEXT,                                 -- 本轮变更摘要
    is_current           BOOLEAN   NOT NULL DEFAULT 0,         -- 是否当前活跃版本（项目主页默认展示）
    published_at         DATETIME,                             -- 审核完成后标记发布时间
    is_deleted           BOOLEAN   NOT NULL DEFAULT 0,         -- 软删除 0-未删除，1-已删除
    created_at           DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (requirement_doc_id)  REFERENCES documents(id) ON DELETE SET NULL,
    FOREIGN KEY (cosmic_doc_id)       REFERENCES documents(id) ON DELETE SET NULL,
    FOREIGN KEY (srs_doc_id)          REFERENCES documents(id) ON DELETE SET NULL,
    FOREIGN KEY (previous_iteration_id) REFERENCES project_iterations(id) ON DELETE SET NULL,

    CHECK (status IN ('draft', 'converting', 'reviewing', 'approved'))
);

CREATE INDEX IF NOT EXISTS idx_iter_project    ON project_iterations(project_id);
CREATE INDEX IF NOT EXISTS idx_iter_current    ON project_iterations(is_current);
CREATE INDEX IF NOT EXISTS idx_iter_previous   ON project_iterations(previous_iteration_id);
CREATE INDEX IF NOT EXISTS idx_iter_status     ON project_iterations(status);
CREATE INDEX IF NOT EXISTS idx_iter_created    ON project_iterations(created_at);

-- =====================================================
-- 种子数据：创建默认管理员账户
-- =====================================================
-- 密码: admin123（bcrypt 哈希，仅供首次登录使用，上线后务必修改）
-- 可使用 Python 生成: passlib.hash.bcrypt.using(rounds=12).hash("admin123")
INSERT INTO users (username, password_hash, display_name, role, is_active)
VALUES (
    'admin',
    '$2b$12$yKY6dv.9JApwTtSpmhK03.f1xMl.7CLKZ5ZNzijEwVQLg39a2FHe.',
    '系统管理员',
    'admin',
    1
) ON CONFLICT(username) DO NOTHING;

-- =====================================================
-- DDL 结束
-- =====================================================
