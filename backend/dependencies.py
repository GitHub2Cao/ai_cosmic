"""Shared dependencies / permission helpers."""

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import Project, ProjectMember, User
from routers.auth import get_current_user


def _can_access_project(session: Session, project_id: int, user: User) -> bool:
    """Check if user can access project (creator, member, or global reviewer)."""
    if user.role == "reviewer":
        return True
    project = session.exec(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)
    ).first()
    if not project:
        return False
    if project.creator_id == user.id:
        return True
    member = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
            ProjectMember.is_deleted == False,
        )
    ).first()
    return member is not None


def _is_project_admin(session: Session, project_id: int, user_id: int) -> bool:
    """Check if user is project admin or creator."""
    project = session.exec(
        select(Project).where(Project.id == project_id, Project.is_deleted == False)
    ).first()
    if not project:
        return False
    if project.creator_id == user_id:
        return True
    member = session.exec(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_deleted == False,
            ProjectMember.role == "admin",
        )
    ).first()
    return member is not None
