"""SQLModel entities — mirrors docs/ddl.sql exactly."""

from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


# ------------------------------------------------------------------
# 1. users
# ------------------------------------------------------------------
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=64)
    password_hash: str = Field(max_length=256)
    display_name: Optional[str] = Field(default=None, max_length=64)
    role: str = Field(default="user", max_length=20)  # admin / reviewer / user
    is_active: bool = Field(default=True)
    is_deleted: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    created_projects: List["Project"] = Relationship(back_populates="creator")
    memberships: List["ProjectMember"] = Relationship(back_populates="user")
    edit_records: List["EditRecord"] = Relationship(back_populates="operator")
    audit_submissions: List["AuditRecord"] = Relationship(
        back_populates="submitter", sa_relationship_kwargs={"foreign_keys": "AuditRecord.submitter_id"}
    )
    audit_reviews: List["AuditRecord"] = Relationship(
        back_populates="reviewer", sa_relationship_kwargs={"foreign_keys": "AuditRecord.reviewer_id"}
    )
    operation_logs: List["OperationLog"] = Relationship(back_populates="operator")


# ------------------------------------------------------------------
# 2. projects
# ------------------------------------------------------------------
class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=256)
    description: Optional[str] = Field(default=None)
    context_json: Optional[str] = Field(default=None)  # 项目静态业务背景知识（AI Prompt 上下文）
    creator_id: int = Field(foreign_key="users.id")
    current_iteration_id: Optional[int] = Field(default=None, foreign_key="project_iterations.id")
    status: str = Field(default="draft", max_length=32)
    is_deleted: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    creator: Optional[User] = Relationship(back_populates="created_projects")
    members: List["ProjectMember"] = Relationship(back_populates="project")
    documents: List["Document"] = Relationship(back_populates="project")
    ai_tasks: List["AITask"] = Relationship(back_populates="project")
    operation_logs: List["OperationLog"] = Relationship(back_populates="project")
    memories: List["ProjectMemory"] = Relationship(back_populates="project")
    iterations: List["ProjectIteration"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"foreign_keys": "ProjectIteration.project_id"}
    )
    current_iteration: Optional["ProjectIteration"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Project.current_iteration_id"}
    )


# ------------------------------------------------------------------
# 3. project_members
# ------------------------------------------------------------------
class ProjectMember(SQLModel, table=True):
    __tablename__ = "project_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    user_id: int = Field(foreign_key="users.id")
    role: str = Field(default="editor", max_length=32)  # admin / editor / reviewer / viewer
    is_deleted: bool = Field(default=False)
    joined_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[Project] = Relationship(back_populates="members")
    user: Optional[User] = Relationship(back_populates="memberships")


# ------------------------------------------------------------------
# 4. documents
# ------------------------------------------------------------------
class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    type: str = Field(max_length=32)  # requirement / cosmic / srs
    version: str = Field(default="v1.0", max_length=16)
    source: str = Field(default="manual_upload", max_length=32)  # ai / manual_upload / manual_edit
    status: str = Field(default="pending", max_length=32)
    title: Optional[str] = Field(default=None, max_length=256)
    original_filename: Optional[str] = Field(default=None, max_length=512)
    file_path: Optional[str] = Field(default=None, max_length=512)
    content_json: Optional[str] = Field(default=None)
    diff_stats: Optional[str] = Field(default=None)
    is_deleted: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[Project] = Relationship(back_populates="documents")
    edit_records: List["EditRecord"] = Relationship(back_populates="document")
    audit_records: List["AuditRecord"] = Relationship(back_populates="document")
    ai_tasks_source: List["AITask"] = Relationship(
        back_populates="source_doc",
        sa_relationship_kwargs={"foreign_keys": "AITask.source_doc_id"},
    )
    ai_tasks_result: List["AITask"] = Relationship(
        back_populates="result_doc",
        sa_relationship_kwargs={"foreign_keys": "AITask.result_doc_id"},
    )


# ------------------------------------------------------------------
# 5. edit_records
# ------------------------------------------------------------------
class EditRecord(SQLModel, table=True):
    __tablename__ = "edit_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id")
    action: str = Field(max_length=32)
    target: Optional[str] = Field(default=None, max_length=256)
    detail: Optional[str] = Field(default=None)
    delta: int = Field(default=0)
    is_deleted: bool = Field(default=False)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    document: Optional[Document] = Relationship(back_populates="edit_records")
    operator: Optional[User] = Relationship(back_populates="edit_records")


# ------------------------------------------------------------------
# 6. audit_records
# ------------------------------------------------------------------
class AuditRecord(SQLModel, table=True):
    __tablename__ = "audit_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id")
    version: str = Field(max_length=16)
    submitter_id: int = Field(foreign_key="users.id")
    reviewer_id: Optional[int] = Field(default=None, foreign_key="users.id")
    status: str = Field(default="pending", max_length=32)
    comment: Optional[str] = Field(default=None)
    scores: Optional[str] = Field(default=None)  # JSON string
    is_deleted: bool = Field(default=False)
    submitted_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = Field(default=None)

    # Relationships
    document: Optional[Document] = Relationship(back_populates="audit_records")
    submitter: Optional[User] = Relationship(
        back_populates="audit_submissions",
        sa_relationship_kwargs={"foreign_keys": "AuditRecord.submitter_id"},
    )
    reviewer: Optional[User] = Relationship(
        back_populates="audit_reviews",
        sa_relationship_kwargs={"foreign_keys": "AuditRecord.reviewer_id"},
    )


# ------------------------------------------------------------------
# 7. ai_tasks
# ------------------------------------------------------------------
class AITask(SQLModel, table=True):
    __tablename__ = "ai_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, unique=True, max_length=64)
    project_id: int = Field(foreign_key="projects.id")
    source_doc_id: int = Field(foreign_key="documents.id")
    target_type: str = Field(max_length=32)  # cosmic / srs
    status: str = Field(default="queued", max_length=32)
    step: Optional[int] = Field(default=None)
    step_name: Optional[str] = Field(default=None, max_length=64)
    message: Optional[str] = Field(default=None)
    result_doc_id: Optional[int] = Field(default=None, foreign_key="documents.id")
    error: Optional[str] = Field(default=None)
    is_deleted: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[Project] = Relationship(back_populates="ai_tasks")
    source_doc: Optional[Document] = Relationship(
        back_populates="ai_tasks_source",
        sa_relationship_kwargs={"foreign_keys": "AITask.source_doc_id"},
    )
    result_doc: Optional[Document] = Relationship(
        back_populates="ai_tasks_result",
        sa_relationship_kwargs={"foreign_keys": "AITask.result_doc_id"},
    )


# ------------------------------------------------------------------
# 8. operation_logs
# ------------------------------------------------------------------
class OperationLog(SQLModel, table=True):
    __tablename__ = "operation_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    action: str = Field(max_length=64)
    target_type: Optional[str] = Field(default=None, max_length=32)
    target_id: Optional[int] = Field(default=None)
    detail: Optional[str] = Field(default=None)
    is_deleted: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[Project] = Relationship(back_populates="operation_logs")
    operator: Optional[User] = Relationship(back_populates="operation_logs")


# ------------------------------------------------------------------
# 10. project_iterations (NEW v1.1)
# ------------------------------------------------------------------
class ProjectIteration(SQLModel, table=True):
    __tablename__ = "project_iterations"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    name: str = Field(max_length=64)  # 如 "v1.0""v2.0"
    status: str = Field(default="draft", max_length=32)  # draft/converting/reviewing/approved
    requirement_doc_id: Optional[int] = Field(default=None, foreign_key="documents.id")
    cosmic_doc_id: Optional[int] = Field(default=None, foreign_key="documents.id")
    srs_doc_id: Optional[int] = Field(default=None, foreign_key="documents.id")
    previous_iteration_id: Optional[int] = Field(default=None, foreign_key="project_iterations.id")
    change_summary: Optional[str] = Field(default=None)
    is_current: bool = Field(default=False)
    published_at: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[Project] = Relationship(
        back_populates="iterations",
        sa_relationship_kwargs={"foreign_keys": "ProjectIteration.project_id"}
    )
    requirement_doc: Optional[Document] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "ProjectIteration.requirement_doc_id"}
    )
    cosmic_doc: Optional[Document] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "ProjectIteration.cosmic_doc_id"}
    )
    srs_doc: Optional[Document] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "ProjectIteration.srs_doc_id"}
    )
    previous_iteration: Optional["ProjectIteration"] = Relationship(
        back_populates="next_iterations",
        sa_relationship_kwargs={"foreign_keys": "ProjectIteration.previous_iteration_id",
                                "remote_side": "ProjectIteration.id"}
    )
    next_iterations: List["ProjectIteration"] = Relationship(
        back_populates="previous_iteration",
        sa_relationship_kwargs={"foreign_keys": "ProjectIteration.previous_iteration_id"}
    )


# ------------------------------------------------------------------
# 9. project_memories
# ------------------------------------------------------------------
class ProjectMemory(SQLModel, table=True):
    __tablename__ = "project_memories"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id")
    category: str = Field(default="general", max_length=32)
    key: Optional[str] = Field(default=None, max_length=128)
    content: str
    source: str = Field(default="system", max_length=32)
    hit_count: int = Field(default=1)
    last_used_at: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    # Relationships
    project: Optional[Project] = Relationship(back_populates="memories")
