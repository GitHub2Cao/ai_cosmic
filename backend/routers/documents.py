"""Documents router — upload / download / manage."""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from database import get_session
from dependencies import _can_access_project, _is_project_admin
from models import Document, Project, ProjectIteration
from routers.auth import get_current_user

router = APIRouter(tags=["documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _project_upload_dir(project_id: int, iteration_id: Optional[int] = None) -> str:
    if iteration_id:
        d = os.path.join(UPLOAD_DIR, str(project_id), str(iteration_id))
    else:
        d = os.path.join(UPLOAD_DIR, str(project_id))
    os.makedirs(d, exist_ok=True)
    return d


# ------------------------------------------------------------------
# DTOs / schemas
# ------------------------------------------------------------------
def _doc_to_dict(doc: Document) -> dict:
    return {
        "id": doc.id,
        "project_id": doc.project_id,
        "type": doc.type,
        "version": doc.version,
        "source": doc.source,
        "status": doc.status,
        "title": doc.title,
        "original_filename": doc.original_filename,
        "file_path": doc.file_path,
        "content_json": doc.content_json,
        "diff_stats": doc.diff_stats,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("/projects/{project_id}/documents")
def upload_document(
    project_id: int,
    type: str = Form(...),  # requirement / cosmic / srs
    file: UploadFile = File(...),
    iteration_id: Optional[int] = Form(None),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
):
    """Upload a document to a project. Only requirement docs can be manually uploaded in Phase 3.
    If iteration_id is provided, links the document to that iteration."""
    if not _can_access_project(session, project_id, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    if type not in ("requirement", "cosmic", "srs"):
        raise HTTPException(status_code=400, detail="Invalid document type")

    # Phase 3: only requirement docs support manual upload; cosmic/srs are AI-generated later
    if type != "requirement":
        raise HTTPException(status_code=400, detail="Only requirement documents can be uploaded manually")

    # Validate iteration if provided
    iteration = None
    if iteration_id is not None:
        iteration = session.exec(
            select(ProjectIteration).where(
                ProjectIteration.id == iteration_id,
                ProjectIteration.project_id == project_id,
                ProjectIteration.is_deleted == False,
            )
        ).first()
        if not iteration:
            raise HTTPException(status_code=404, detail="Iteration not found")

    # Save file
    project_dir = _project_upload_dir(project_id, iteration_id)
    safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    file_path = os.path.join(project_dir, safe_name)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    document = Document(
        project_id=project_id,
        type=type,
        version="v1.0",
        source="manual_upload",
        status="pending",
        title=file.filename,
        original_filename=file.filename,
        file_path=file_path,
    )
    session.add(document)
    session.commit()
    session.refresh(document)

    # Link to iteration if specified
    if iteration is not None:
        if type == "requirement":
            iteration.requirement_doc_id = document.id
        elif type == "cosmic":
            iteration.cosmic_doc_id = document.id
        elif type == "srs":
            iteration.srs_doc_id = document.id
        # Sync project.current_iteration_id if this iteration is current
        if iteration.is_current:
            project = session.exec(select(Project).where(Project.id == project_id)).first()
            if project and project.current_iteration_id != iteration.id:
                project.current_iteration_id = iteration.id
                session.add(project)
        session.add(iteration)
        session.commit()

    return _doc_to_dict(document)


@router.get("/projects/{project_id}/documents")
def list_documents(
    project_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
):
    """List all non-deleted documents in a project."""
    if not _can_access_project(session, project_id, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    docs = session.exec(
        select(Document).where(
            Document.project_id == project_id,
            Document.is_deleted == False,
        )
    ).all()

    return [_doc_to_dict(d) for d in docs]


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
):
    """Download the original file of a document."""
    doc = session.exec(
        select(Document).where(Document.id == document_id, Document.is_deleted == False)
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not _can_access_project(session, doc.project_id, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    if not doc.file_path or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        doc.file_path,
        filename=doc.original_filename or os.path.basename(doc.file_path),
        media_type="application/octet-stream",
    )


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
):
    """Soft-delete a document. Admin only."""
    doc = session.exec(
        select(Document).where(Document.id == document_id, Document.is_deleted == False)
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not _is_project_admin(session, doc.project_id, current_user.id):
        raise HTTPException(status_code=403, detail="Admin permission required")

    doc.is_deleted = True
    doc.updated_at = datetime.utcnow()
    session.add(doc)
    session.commit()

    return {"message": "Document deleted"}
