"""API routes for project management."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.triage import (
    get_projects,
    get_project_by_id,
    update_triage_status,
    update_hygiene_status,
    get_project_stats,
)
from app.models.project import ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


class TriageUpdateRequest(BaseModel):
    """Request body for updating triage status."""
    status: str


class HygieneUpdateRequest(BaseModel):
    """Request body for updating hygiene status."""
    status: str


class ProjectStatsResponse(BaseModel):
    """Response schema for project statistics."""
    total: int
    untriaged: int
    trash: int
    salvage: int
    must_finish: int
    pending_harvest: int
    ready_for_migration: int
    average_score: float


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    triage_status: Optional[str] = Query(None, description="Filter by triage status"),
    hygiene_status: Optional[str] = Query(None, description="Filter by hygiene status"),
    min_score: Optional[int] = Query(None, description="Minimum signal score"),
    max_score: Optional[int] = Query(None, description="Maximum signal score"),
    search: Optional[str] = Query(None, description="Search term"),
    sort_by: str = Query("signal_score", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(100, description="Maximum results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all projects with optional filtering and sorting.
    """
    projects = await get_projects(
        db,
        triage_status=triage_status,
        hygiene_status=hygiene_status,
        min_score=min_score,
        max_score=max_score,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit * 2,  # Get more to account for deduplication
        offset=offset
    )
    
    # Deduplicate by cluster_id - keep only best project from each cluster
    from collections import defaultdict
    clusters = defaultdict(list)
    
    for p in projects:
        cluster_id = p.cluster_id or p.project_name.lower()
        clusters[cluster_id].append(p)
    
    # Select best project from each cluster
    deduplicated = []
    for cluster_projects in clusters.values():
        if len(cluster_projects) > 1:
            # Select best: highest score, most backups, longest time
            best = max(cluster_projects, key=lambda p: (
                p.signal_score,
                p.backup_count,
                p.time_spent_days or 0,
                1 if p.audio_preview_path else 0,
            ))
            deduplicated.append(best)
        else:
            deduplicated.append(cluster_projects[0])
    
    # Re-sort and limit
    deduplicated.sort(
        key=lambda p: getattr(p, sort_by, p.signal_score),
        reverse=(sort_order == "desc")
    )
    deduplicated = deduplicated[:limit]
    
    return [
        ProjectResponse(
            id=p.id,
            project_path=p.project_path,
            project_name=p.project_name,
            key_signature=p.key_signature,
            bpm=p.bpm,
            signal_score=p.signal_score,
            triage_status=p.triage_status,
            hygiene_status=p.hygiene_status,
            cluster_id=p.cluster_id,
            time_spent_days=p.time_spent_days,
            diamond_tier_keywords=p.diamond_tier_keywords,
            gold_tier_keywords=p.gold_tier_keywords,
            audio_preview_path=p.audio_preview_path,
            backup_count=p.backup_count,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in deduplicated
    ]


@router.get("/stats", response_model=ProjectStatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get project statistics."""
    stats = await get_project_stats(db)
    return ProjectStatsResponse(**stats)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a single project by ID."""
    project = await get_project_by_id(db, project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
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


@router.put("/{project_id}/triage", response_model=ProjectResponse)
async def update_project_triage(
    project_id: int,
    request: TriageUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update the triage status of a project."""
    try:
        project = await update_triage_status(db, project_id, request.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
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


@router.put("/{project_id}/hygiene", response_model=ProjectResponse)
async def update_project_hygiene(
    project_id: int,
    request: HygieneUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update the hygiene status of a project."""
    try:
        project = await update_hygiene_status(db, project_id, request.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
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


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a project from the database."""
    from sqlalchemy import delete
    from app.models.project import Project
    
    result = await db.execute(
        delete(Project).where(Project.id == project_id)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.commit()
    return {"message": "Project deleted"}

