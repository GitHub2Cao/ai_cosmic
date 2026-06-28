"""Projects router — CRUD + member management."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func

from database import get_session
from dependencies import _can_access_project, _is_project_admin
from models import Document, Project, ProjectIteration, ProjectMember, User
from routers.auth import get_current_user

router = APIRouter(tags=["projects"])


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _member_count(session: Session, project_id: int) -> int:
    return session.exec(
        select(func.count(ProjectMember.id)).where(
            ProjectMember.project_id == project_id,
            ProjectMember.is_deleted == False,
        )
    ).one()


# ------------------------------------------------------------------
# DTOs
# ------------------------------------------------------------------
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    context_json: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    context_json: Optional[str] = None


class MemberAdd(BaseModel):
    username: str
    role: str = "editor"


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.get("")
def list_projects(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all projects that current user can access."""
    if current_user.role == "reviewer":
        # Global reviewer sees all non-deleted projects
        projects = session.exec(
            select(Project).where(Project.is_deleted == False)
        ).all()
    else:
        # Get project IDs where user is a member (including as creator)
        member_subquery = (
            select(ProjectMember.project_id)
            .where(
                ProjectMember.user_id == current_user.id,
                ProjectMember.is_deleted == False,
            )
        )
        project_ids = session.exec(member_subquery).all()

        # Also include projects they created
        created = session.exec(
            select(Project.id).where(
                Project.creator_id == current_user.id,
                Project.is_deleted == False,
            )
        ).all()

        all_ids = list(set(list(project_ids) + list(created)))

        if not all_ids:
            return []

        projects = session.exec(
            select(Project).where(Project.id.in_(all_ids), Project.is_deleted == False)
        ).all()

    result = []
    for p in projects:
        creator = session.exec(select(User).where(User.id == p.creator_id)).first()
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "status": p.status,
            "creator": {
                "id": creator.id if creator else None,
                "username": creator.username if creator else None,
                "display_name": creator.display_name if creator else None,
            },
            "member_count": _member_count(session, p.id),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })

    return result


@router.post("")
def create_project(
    payload: ProjectCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a project, auto-add creator as admin, and create v1.0 iteration."""
    project = Project(
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        context_json=payload.context_json.strip() if payload.context_json else None,
        creator_id=current_user.id,
        status="draft",
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    # Auto-add creator as admin member
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="admin",
    )
    session.add(member)
    session.commit()

    # Create v1.0 iteration
    iteration = ProjectIteration(
        project_id=project.id,
        name="v1.0",
        status="draft",
        is_current=True,
    )
    session.add(iteration)
    session.commit()
    session.refresh(iteration)

    # Link current_iteration_id
    project.current_iteration_id = iteration.id
    session.add(project)
    session.commit()

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "context_json": project.context_json,
        "status": project.status,
        "creator_id": project.creator_id,
        "current_iteration_id": project.current_iteration_id,
        "created_at": project.created_at.isoformat() if project.created_at else None,
    }


@router.get("/{project_id}")
def get_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get project detail with members list."""
    project = session.exec(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check access: global reviewer, admin, or any member
    if not _can_access_project(session, project_id, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    creator = session.exec(select(User).where(User.id == project.creator_id)).first()

    members = session.exec(
        select(ProjectMember, User)
        .join(User, ProjectMember.user_id == User.id)
        .where(
            ProjectMember.project_id == project_id,
            ProjectMember.is_deleted == False,
            User.is_deleted == False,
        )
    ).all()

    docs = session.exec(
        select(Document).where(
            Document.project_id == project_id,
            Document.is_deleted == False,
        )
    ).all()

    # Load iterations
    iterations = session.exec(
        select(ProjectIteration).where(
            ProjectIteration.project_id == project_id,
            ProjectIteration.is_deleted == False,
        )
    ).all()

    current_iteration = None
    if project.current_iteration_id:
        current_iter = session.exec(
            select(ProjectIteration).where(
                ProjectIteration.id == project.current_iteration_id,
                ProjectIteration.is_deleted == False,
            )
        ).first()
        if current_iter:
            current_iteration = {
                "id": current_iter.id,
                "name": current_iter.name,
                "status": current_iter.status,
                "is_current": current_iter.is_current,
                "published_at": current_iter.published_at.isoformat() if current_iter.published_at else None,
                "documents": {
                    "requirement": _doc_to_dict(current_iter.requirement_doc) if current_iter.requirement_doc else None,
                    "cosmic": _doc_to_dict(current_iter.cosmic_doc) if current_iter.cosmic_doc else None,
                    "srs": _doc_to_dict(current_iter.srs_doc) if current_iter.srs_doc else None,
                },
            }

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "context_json": project.context_json,
        "status": project.status,
        "creator": {
            "id": creator.id if creator else None,
            "username": creator.username if creator else None,
            "display_name": creator.display_name if creator else None,
        },
        "members": [
            {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "role": pm.role,
                "joined_at": pm.joined_at.isoformat() if pm.joined_at else None,
                "project_member_id": pm.id,
            }
            for pm, user in members
        ],
        "documents": [
            {
                "id": d.id,
                "type": d.type,
                "version": d.version,
                "source": d.source,
                "status": d.status,
                "title": d.title,
                "original_filename": d.original_filename,
                "file_path": d.file_path,
                "content_json": d.content_json,
                "diff_stats": d.diff_stats,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            }
            for d in docs
        ],
        "current_iteration": current_iteration,
        "iterations": [
            {
                "id": i.id,
                "name": i.name,
                "status": i.status,
                "is_current": i.is_current,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in iterations
        ],
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.put("/{project_id}")
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update project name/description. Admin only."""
    if not _is_project_admin(session, project_id, current_user.id):
        raise HTTPException(status_code=403, detail="Admin permission required")

    project = session.exec(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if payload.name is not None:
        project.name = payload.name.strip()
    if payload.description is not None:
        project.description = payload.description.strip() if payload.description else None
    if payload.context_json is not None:
        project.context_json = payload.context_json.strip() if payload.context_json else None
    project.updated_at = datetime.utcnow()

    session.add(project)
    session.commit()
    session.refresh(project)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "context_json": project.context_json,
        "status": project.status,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete project. Admin only."""
    if not _is_project_admin(session, project_id, current_user.id):
        raise HTTPException(status_code=403, detail="Admin permission required")

    project = session.exec(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.is_deleted = True
    session.add(project)
    session.commit()

    return {"message": "Project deleted"}


@router.post("/{project_id}/members")
def add_member(
    project_id: int,
    payload: MemberAdd,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Add a member to project. Admin only."""
    if not _is_project_admin(session, project_id, current_user.id):
        raise HTTPException(status_code=403, detail="Admin permission required")

    user = session.exec(
        select(User).where(
            User.username == payload.username.strip(),
            User.is_deleted == False,
        )
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
            ProjectMember.is_deleted == False,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member")

    member = ProjectMember(
        project_id=project_id,
        user_id=user.id,
        role=payload.role,
    )
    session.add(member)
    session.commit()
    session.refresh(member)

    return {
        "id": member.id,
        "user_id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "role": member.role,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
    }


@router.delete("/{project_id}/members/{user_id}")
def remove_member(
    project_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Remove a member from project. Admin only."""
    if not _is_project_admin(session, project_id, current_user.id):
        raise HTTPException(status_code=403, detail="Admin permission required")

    member = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_deleted == False,
        )
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.is_deleted = True
    session.add(member)
    session.commit()

    return {"message": "Member removed"}
