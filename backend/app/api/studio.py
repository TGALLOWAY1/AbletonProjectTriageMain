"""API routes for Phase 5: Studio Manager."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.studio import (
    get_studio_projects,
    get_studio_project_by_id,
    update_production_tags,
    update_genre,
    update_priority,
    update_notes,
    reorder_projects,
    auto_populate_studio,
)
from app.models.project import StudioProjectResponse, ProjectResponse

router = APIRouter(prefix="/studio", tags=["studio"])


class TagsUpdateRequest(BaseModel):
    """Request body for updating production tags."""
    tags: List[str]


class GenreUpdateRequest(BaseModel):
    """Request body for updating genre."""
    genre: str


class PriorityUpdateRequest(BaseModel):
    """Request body for updating priority order."""
    priority_order: int


class NotesUpdateRequest(BaseModel):
    """Request body for updating notes."""
    notes: str


class ReorderRequest(BaseModel):
    """Request body for reordering projects."""
    project_ids: List[int]


def project_to_response(project) -> ProjectResponse:
    """Convert a Project model to ProjectResponse."""
    return ProjectResponse(
        id=project.id,
        project_path=project.project_path,
        project_name=project.project_name,
        key_signature=project.key_signature,
        bpm=project.bpm,
        signal_score=project.signal_score,
        triage_status=project.triage_status,
        hygiene_status=project.hygiene_status,
        cluster_id=project.cluster_id,
        time_spent_days=project.time_spent_days,
        diamond_tier_keywords=project.diamond_tier_keywords,
        gold_tier_keywords=project.gold_tier_keywords,
        audio_preview_path=project.audio_preview_path,
        backup_count=project.backup_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def studio_project_to_response(sp) -> StudioProjectResponse:
    """Convert a StudioProject model to StudioProjectResponse."""
    return StudioProjectResponse(
        id=sp.id,
        project_id=sp.project_id,
        project=project_to_response(sp.project),
        genre=sp.genre,
        production_tags=sp.production_tags,
        priority_order=sp.priority_order,
        notes=sp.notes,
    )


@router.get("/projects", response_model=List[StudioProjectResponse])
async def list_studio_projects(db: AsyncSession = Depends(get_db)):
    """Get all studio projects ordered by priority."""
    projects = await get_studio_projects(db)
    return [studio_project_to_response(sp) for sp in projects]


@router.get("/projects/{studio_project_id}", response_model=StudioProjectResponse)
async def get_studio_project(
    studio_project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a single studio project by ID."""
    sp = await get_studio_project_by_id(db, studio_project_id)
    
    if not sp:
        raise HTTPException(status_code=404, detail="Studio project not found")
    
    return studio_project_to_response(sp)


@router.put("/projects/{studio_project_id}/tags", response_model=StudioProjectResponse)
async def update_project_tags(
    studio_project_id: int,
    request: TagsUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update production tags for a studio project."""
    sp = await update_production_tags(db, studio_project_id, request.tags)
    
    if not sp:
        raise HTTPException(status_code=404, detail="Studio project not found")
    
    return studio_project_to_response(sp)


@router.put("/projects/{studio_project_id}/genre", response_model=StudioProjectResponse)
async def update_project_genre(
    studio_project_id: int,
    request: GenreUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update genre for a studio project."""
    sp = await update_genre(db, studio_project_id, request.genre)
    
    if not sp:
        raise HTTPException(status_code=404, detail="Studio project not found")
    
    return studio_project_to_response(sp)


@router.put("/projects/{studio_project_id}/priority", response_model=StudioProjectResponse)
async def update_project_priority(
    studio_project_id: int,
    request: PriorityUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update priority order for a studio project."""
    sp = await update_priority(db, studio_project_id, request.priority_order)
    
    if not sp:
        raise HTTPException(status_code=404, detail="Studio project not found")
    
    return studio_project_to_response(sp)


@router.put("/projects/{studio_project_id}/notes", response_model=StudioProjectResponse)
async def update_project_notes(
    studio_project_id: int,
    request: NotesUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update notes for a studio project."""
    sp = await update_notes(db, studio_project_id, request.notes)
    
    if not sp:
        raise HTTPException(status_code=404, detail="Studio project not found")
    
    return studio_project_to_response(sp)


@router.post("/projects/reorder", response_model=List[StudioProjectResponse])
async def reorder_studio_projects(
    request: ReorderRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reorder studio projects.
    
    Pass a list of project IDs in the desired order.
    """
    projects = await reorder_projects(db, request.project_ids)
    return [studio_project_to_response(sp) for sp in projects]


@router.post("/populate")
async def populate_studio(db: AsyncSession = Depends(get_db)):
    """
    Auto-populate studio with must-finish projects.
    
    Creates studio entries for any must-finish projects
    that don't already have them.
    """
    created = await auto_populate_studio(db)
    return {"message": f"Created {created} studio projects"}

