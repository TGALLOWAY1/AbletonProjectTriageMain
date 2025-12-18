"""Phase 5: Studio Manager service."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import (
    Project, StudioProject, TriageStatus, HygieneStatus
)


async def get_studio_projects(db: AsyncSession) -> List[StudioProject]:
    """
    Get all studio projects ordered by priority.
    """
    result = await db.execute(
        select(StudioProject)
        .options(selectinload(StudioProject.project))
        .order_by(StudioProject.priority_order)
    )
    return list(result.scalars().all())


async def get_studio_project_by_id(
    db: AsyncSession, 
    studio_project_id: int
) -> Optional[StudioProject]:
    """Get a single studio project by ID."""
    result = await db.execute(
        select(StudioProject)
        .options(selectinload(StudioProject.project))
        .where(StudioProject.id == studio_project_id)
    )
    return result.scalar_one_or_none()


async def create_studio_project(
    db: AsyncSession,
    project_id: int,
    genre: str = "Other"
) -> StudioProject:
    """
    Create a studio project from an existing project.
    
    Called when a project is migrated to the curated folder.
    """
    # Get max priority order
    result = await db.execute(
        select(StudioProject.priority_order)
        .order_by(StudioProject.priority_order.desc())
        .limit(1)
    )
    max_priority = result.scalar() or 0
    
    studio_project = StudioProject(
        project_id=project_id,
        genre=genre,
        priority_order=max_priority + 1,
    )
    
    db.add(studio_project)
    await db.commit()
    await db.refresh(studio_project)
    
    # Load relationship
    result = await db.execute(
        select(StudioProject)
        .options(selectinload(StudioProject.project))
        .where(StudioProject.id == studio_project.id)
    )
    return result.scalar_one()


async def update_production_tags(
    db: AsyncSession,
    studio_project_id: int,
    tags: List[str]
) -> Optional[StudioProject]:
    """Update production tags for a studio project."""
    result = await db.execute(
        select(StudioProject)
        .options(selectinload(StudioProject.project))
        .where(StudioProject.id == studio_project_id)
    )
    studio_project = result.scalar_one_or_none()
    
    if not studio_project:
        return None
    
    studio_project.production_tags = tags
    await db.commit()
    await db.refresh(studio_project)
    return studio_project


async def update_genre(
    db: AsyncSession,
    studio_project_id: int,
    genre: str
) -> Optional[StudioProject]:
    """Update genre for a studio project."""
    result = await db.execute(
        select(StudioProject)
        .options(selectinload(StudioProject.project))
        .where(StudioProject.id == studio_project_id)
    )
    studio_project = result.scalar_one_or_none()
    
    if not studio_project:
        return None
    
    studio_project.genre = genre
    await db.commit()
    await db.refresh(studio_project)
    return studio_project


async def update_priority(
    db: AsyncSession,
    studio_project_id: int,
    priority_order: int
) -> Optional[StudioProject]:
    """Update priority order for a studio project."""
    result = await db.execute(
        select(StudioProject)
        .options(selectinload(StudioProject.project))
        .where(StudioProject.id == studio_project_id)
    )
    studio_project = result.scalar_one_or_none()
    
    if not studio_project:
        return None
    
    studio_project.priority_order = priority_order
    await db.commit()
    await db.refresh(studio_project)
    return studio_project


async def update_notes(
    db: AsyncSession,
    studio_project_id: int,
    notes: str
) -> Optional[StudioProject]:
    """Update notes for a studio project."""
    result = await db.execute(
        select(StudioProject)
        .options(selectinload(StudioProject.project))
        .where(StudioProject.id == studio_project_id)
    )
    studio_project = result.scalar_one_or_none()
    
    if not studio_project:
        return None
    
    studio_project.notes = notes
    await db.commit()
    await db.refresh(studio_project)
    return studio_project


async def reorder_projects(
    db: AsyncSession,
    project_ids: List[int]
) -> List[StudioProject]:
    """
    Reorder studio projects based on the provided ID list.
    
    Args:
        db: Database session
        project_ids: List of studio project IDs in desired order
        
    Returns:
        Updated list of studio projects
    """
    for index, project_id in enumerate(project_ids):
        result = await db.execute(
            select(StudioProject).where(StudioProject.id == project_id)
        )
        studio_project = result.scalar_one_or_none()
        
        if studio_project:
            studio_project.priority_order = index
    
    await db.commit()
    return await get_studio_projects(db)


async def auto_populate_studio(db: AsyncSession) -> int:
    """
    Auto-populate studio with must-finish projects that don't have studio entries.
    
    Returns:
        Number of studio projects created
    """
    # Get must-finish projects without studio entries
    result = await db.execute(
        select(Project).where(
            Project.triage_status == TriageStatus.MUST_FINISH.value,
            ~Project.id.in_(
                select(StudioProject.project_id)
            )
        )
    )
    projects = list(result.scalars().all())
    
    created = 0
    for project in projects:
        await create_studio_project(db, project.id)
        created += 1
    
    return created

