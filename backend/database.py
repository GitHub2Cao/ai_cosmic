"""Database engine and session management."""

import os
from pathlib import Path

from sqlmodel import SQLModel, create_engine, Session, select, text

DB_PATH = Path(__file__).with_name("cosmic.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("COSMIC_ENV") == "dev",
    connect_args={"check_same_thread": False},
)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    """Execute DDL script to create tables."""
    ddl_path = Path(__file__).with_name("ddl.sql")
    if not ddl_path.exists():
        raise FileNotFoundError(f"DDL file not found: {ddl_path}")

    with open(ddl_path, "r", encoding="utf-8") as f:
        ddl = f.read()

    # Split by semicolon and execute each non-empty, non-comment statement
    for stmt in ddl.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        # Skip pure comment blocks
        lines = [l for l in stmt.splitlines() if l.strip() and not l.strip().startswith("--")]
        if not lines:
            continue
        with Session(engine) as session:
            try:
                session.exec(text(stmt))
                session.commit()
            except Exception as e:
                err = str(e).lower()
                if "already exists" in err or "duplicate column" in err or "no such column" in err:
                    print(f"[DB] DDL skip: {str(e)[:120]}")
                    session.rollback()
                else:
                    raise

    # Ensure schema additions for existing tables (SQLite ALTER TABLE)
    with Session(engine) as session:
        if _table_exists(session, "projects") and not _column_exists(session, "projects", "current_iteration_id"):
            session.exec(text("ALTER TABLE projects ADD COLUMN current_iteration_id INTEGER"))
            session.commit()
            print("[DB] Added column projects.current_iteration_id")

    # ---- v1.0 → v1.1 数据迁移（project_iterations） ----
    _migrate_v1_to_v1_1()

    print(f"[DB] Initialized at {DB_PATH}")


def _table_exists(session, table_name):
    result = session.exec(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
    ).bindparams(name=table_name)).first()
    return result is not None


def _column_exists(session, table_name, column_name):
    result = session.exec(text(
        f"PRAGMA table_info({table_name})"
    )).all()
    for col in result:
        if col[1] == column_name:
            return True
    return False


def _migrate_v1_to_v1_1():
    """一次性迁移：为没有迭代的旧项目自动生成 v1.0 迭代。"""
    from models import Project, Document, ProjectIteration  # noqa: delay import

    with Session(engine) as session:
        # 如果 project_iterations 表还未创建（首次运行 v1.1 DDL），直接返回
        if not _table_exists(session, "project_iterations"):
            return

        # 为所有没有迭代的项目创建 v1.0 迭代
        projects = session.exec(
            text("SELECT id, status, creator_id FROM projects WHERE is_deleted = 0")
        ).all()

        for row in projects:
            project_id, status, creator_id = row
            # 检查是否已有迭代
            existing = session.exec(
                text("SELECT id FROM project_iterations WHERE project_id = :pid AND is_deleted = 0")
                .bindparams(pid=project_id)
            ).first()
            if existing:
                continue

            # 查找该项目下的三文档
            docs = session.exec(
                text(
                    "SELECT id, type FROM documents WHERE project_id = :pid AND is_deleted = 0"
                ).bindparams(pid=project_id)
            ).all()
            doc_map = {d[1]: d[0] for d in docs}

            # 创建默认迭代
            iter_name = "v1.0"
            result = session.exec(
                text(
                    """
                    INSERT INTO project_iterations
                    (project_id, name, status, requirement_doc_id, cosmic_doc_id, srs_doc_id, is_current, created_at, updated_at)
                    VALUES (:pid, :name, :status, :req_id, :cos_id, :srs_id, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """
                ).bindparams(
                    pid=project_id,
                    name=iter_name,
                    status=status if status else "draft",
                    req_id=doc_map.get("requirement"),
                    cos_id=doc_map.get("cosmic"),
                    srs_id=doc_map.get("srs"),
                )
            )
            session.commit()

            # 获取刚插入的迭代 ID
            new_iter = session.exec(
                text(
                    "SELECT id FROM project_iterations WHERE project_id = :pid AND name = :name AND is_current = 1"
                ).bindparams(pid=project_id, name=iter_name)
            ).first()

            if new_iter:
                # 更新 projects.current_iteration_id
                session.exec(
                    text(
                        "UPDATE projects SET current_iteration_id = :iid WHERE id = :pid"
                    ).bindparams(iid=new_iter[0], pid=project_id)
                )
                session.commit()

        print("[DB] Migration v1.0 → v1.1 completed")
