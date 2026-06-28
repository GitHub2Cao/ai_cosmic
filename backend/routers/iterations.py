"""Iterations router — CRUD for project iterations."""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, text

from database import get_session
from dependencies import _can_access_project, _is_project_admin
from models import Document, Project, ProjectIteration, User
from routers.auth import get_current_user
from routers.documents import _doc_to_dict

router = APIRouter(tags=["iterations"])


# ------------------------------------------------------------------
# DTOs
# ------------------------------------------------------------------
from pydantic import BaseModel


class IterationCreate(BaseModel):
    name: Optional[str] = None
    change_summary: Optional[str] = None
    previous_iteration_id: Optional[int] = None


class IterationUpdate(BaseModel):
    name: Optional[str] = None
    change_summary: Optional[str] = None
    is_current: Optional[bool] = None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _next_version_name(session: Session, project_id: int) -> str:
    """Auto-generate next iteration name like v2.0, v3.0..."""
    existing = session.exec(
        select(ProjectIteration).where(
            ProjectIteration.project_id == project_id,
            ProjectIteration.is_deleted == False,
        )
    ).all()
    versions = []
    for i in existing:
        try:
            if i.name.startswith("v"):
                versions.append(float(i.name[1:]))
        except ValueError:
            pass
    next_v = max(versions) + 1.0 if versions else 1.0
    return f"v{int(next_v)}.0"


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("/projects/{project_id}/iterations")
def create_iteration(
    project_id: int,
    payload: IterationCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new iteration for a project. Auto sets is_current=True and resets others."""
    if not _can_access_project(session, project_id, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    project = session.exec(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Clear is_current for all other iterations in this project
    session.exec(
        text("UPDATE project_iterations SET is_current = 0 WHERE project_id = :pid").bindparams(pid=project_id)
    )

    name = payload.name.strip() if payload.name else _next_version_name(session, project_id)
    change_summary = payload.change_summary.strip() if payload.change_summary else None

    iteration = ProjectIteration(
        project_id=project_id,
        name=name,
        status="draft",
        previous_iteration_id=payload.previous_iteration_id,
        change_summary=change_summary,
        is_current=True,
    )
    session.add(iteration)
    session.commit()
    session.refresh(iteration)

    # Update project's current_iteration_id and status
    project.current_iteration_id = iteration.id
    project.status = iteration.status
    session.add(project)
    session.commit()

    return {
        "id": iteration.id,
        "project_id": iteration.project_id,
        "name": iteration.name,
        "status": iteration.status,
        "is_current": iteration.is_current,
        "previous_iteration_id": iteration.previous_iteration_id,
        "change_summary": iteration.change_summary,
        "created_at": iteration.created_at.isoformat() if iteration.created_at else None,
    }


@router.get("/projects/{project_id}/iterations")
def list_iterations(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List all iterations of a project."""
    if not _can_access_project(session, project_id, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    iterations = session.exec(
        select(ProjectIteration).where(
            ProjectIteration.project_id == project_id,
            ProjectIteration.is_deleted == False,
        )
    ).all()

    result = []
    for i in iterations:
        result.append({
            "id": i.id,
            "name": i.name,
            "status": i.status,
            "is_current": i.is_current,
            "previous_iteration_id": i.previous_iteration_id,
            "published_at": i.published_at.isoformat() if i.published_at else None,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        })

    return result


@router.get("/iterations/{iteration_id}")
def get_iteration(
    iteration_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get iteration detail with linked documents."""
    iteration = session.exec(
        select(ProjectIteration).where(
            ProjectIteration.id == iteration_id,
            ProjectIteration.is_deleted == False,
        )
    ).first()
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")

    if not _can_access_project(session, iteration.project_id, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": iteration.id,
        "project_id": iteration.project_id,
        "name": iteration.name,
        "status": iteration.status,
        "is_current": iteration.is_current,
        "change_summary": iteration.change_summary,
        "previous_iteration_id": iteration.previous_iteration_id,
        "published_at": iteration.published_at.isoformat() if iteration.published_at else None,
        "documents": {
            "requirement": _doc_to_dict(iteration.requirement_doc) if iteration.requirement_doc else None,
            "cosmic": _doc_to_dict(iteration.cosmic_doc) if iteration.cosmic_doc else None,
            "srs": _doc_to_dict(iteration.srs_doc) if iteration.srs_doc else None,
        },
        "created_at": iteration.created_at.isoformat() if iteration.created_at else None,
        "updated_at": iteration.updated_at.isoformat() if iteration.updated_at else None,
    }


@router.put("/iterations/{iteration_id}")
def update_iteration(
    iteration_id: int,
    payload: IterationUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update iteration name, change_summary, or switch is_current."""
    iteration = session.exec(
        select(ProjectIteration).where(
            ProjectIteration.id == iteration_id,
            ProjectIteration.is_deleted == False,
        )
    ).first()
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")

    if not _is_project_admin(session, iteration.project_id, current_user.id):
        raise HTTPException(status_code=403, detail="Admin permission required")

    if payload.name is not None:
        iteration.name = payload.name.strip()
    if payload.change_summary is not None:
        iteration.change_summary = payload.change_summary.strip()

    if payload.is_current is True:
        # Reset all other iterations to is_current=False
        session.exec(
            text("UPDATE project_iterations SET is_current = 0 WHERE project_id = :pid AND id != :iid")
            .bindparams(pid=iteration.project_id, iid=iteration.id)
        )
        iteration.is_current = True

        # Update project.current_iteration_id and status
        project = session.exec(
            select(Project).where(Project.id == iteration.project_id)
        ).first()
        if project:
            project.current_iteration_id = iteration.id
            project.status = iteration.status
            session.add(project)

    iteration.updated_at = datetime.utcnow()
    session.add(iteration)
    session.commit()
    session.refresh(iteration)

    return {
        "id": iteration.id,
        "name": iteration.name,
        "status": iteration.status,
        "is_current": iteration.is_current,
        "change_summary": iteration.change_summary,
        "updated_at": iteration.updated_at.isoformat() if iteration.updated_at else None,
    }


@router.delete("/iterations/{iteration_id}")
def delete_iteration(
    iteration_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete an iteration. If it was current, promote latest remaining or clear."""
    iteration = session.exec(
        select(ProjectIteration).where(
            ProjectIteration.id == iteration_id,
            ProjectIteration.is_deleted == False,
        )
    ).first()
    if not iteration:
        raise HTTPException(status_code=404, detail="Iteration not found")

    if not _is_project_admin(session, iteration.project_id, current_user.id):
        raise HTTPException(status_code=403, detail="Admin permission required")

    project_id = iteration.project_id
    was_current = iteration.is_current

    iteration.is_deleted = True
    iteration.is_current = False
    session.add(iteration)
    session.commit()

    if was_current:
        # Promote latest remaining iteration to current
        latest = session.exec(
            select(ProjectIteration).where(
                ProjectIteration.project_id == project_id,
                ProjectIteration.is_deleted == False,
            ).order_by(ProjectIteration.created_at.desc())
        ).first()

        project = session.exec(select(Project).where(Project.id == project_id)).first()
        if latest:
            latest.is_current = True
            session.add(latest)
            if project:
                project.current_iteration_id = latest.id
                project.status = latest.status
        else:
            if project:
                project.current_iteration_id = None
                project.status = "draft"
        session.commit()

    return {"message": "Iteration deleted"}
