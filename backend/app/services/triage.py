"""Phase 2: Triage service for project status management."""

from typing import List, Optional
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import (
    Project, TriageStatus, HygieneStatus,
    ProjectResponse
)


async def get_projects(
    db: AsyncSession,
    triage_status: Optional[str] = None,
    hygiene_status: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    search: Optional[str] = None,
    sort_by: str = "signal_score",
    sort_order: str = "desc",
    limit: int = 100,
    offset: int = 0
) -> List[Project]:
    """
    Get projects with optional filtering and sorting.
    
    Args:
        db: Database session
        triage_status: Filter by triage status
        hygiene_status: Filter by hygiene status
        min_score: Minimum signal score
        max_score: Maximum signal score
        search: Search term for project name/path
        sort_by: Field to sort by
        sort_order: 'asc' or 'desc'
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        List of matching projects
    """
    query = select(Project)
    
    # Apply filters
    if triage_status and triage_status != 'all':
        query = query.where(Project.triage_status == triage_status)
    
    if hygiene_status and hygiene_status != 'all':
        query = query.where(Project.hygiene_status == hygiene_status)
    
    if min_score is not None:
        query = query.where(Project.signal_score >= min_score)
    
    if max_score is not None:
        query = query.where(Project.signal_score <= max_score)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Project.project_name.ilike(search_pattern),
                Project.project_path.ilike(search_pattern)
            )
        )
    
    # Apply sorting
    sort_column = getattr(Project, sort_by, Project.signal_score)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_project_by_id(db: AsyncSession, project_id: int) -> Optional[Project]:
    """Get a single project by ID."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


async def update_triage_status(
    db: AsyncSession,
    project_id: int,
    status: str
) -> Optional[Project]:
    """
    Update the triage status of a project.
    
    Args:
        db: Database session
        project_id: Project ID
        status: New triage status
        
    Returns:
        Updated project or None if not found
    """
    project = await get_project_by_id(db, project_id)
    if not project:
        return None
    
    # Validate status
    if status not in [s.value for s in TriageStatus]:
        raise ValueError(f"Invalid triage status: {status}")
    
    project.triage_status = status
    
    # Reset hygiene status if changing to a new triage status
    if status != TriageStatus.MUST_FINISH.value:
        project.hygiene_status = HygieneStatus.PENDING.value
    
    await db.commit()
    await db.refresh(project)
    return project


async def update_hygiene_status(
    db: AsyncSession,
    project_id: int,
    status: str
) -> Optional[Project]:
    """
    Update the hygiene status of a project.
    
    Args:
        db: Database session
        project_id: Project ID
        status: New hygiene status
        
    Returns:
        Updated project or None if not found
    """
    project = await get_project_by_id(db, project_id)
    if not project:
        return None
    
    # Validate status
    if status not in [s.value for s in HygieneStatus]:
        raise ValueError(f"Invalid hygiene status: {status}")
    
    project.hygiene_status = status
    await db.commit()
    await db.refresh(project)
    return project


async def get_project_stats(db: AsyncSession) -> dict:
    """
    Get statistics about all projects.
    
    Returns:
        Dictionary with project statistics
    """
    # Total count
    total_result = await db.execute(
        select(func.count(Project.id))
    )
    total = total_result.scalar() or 0
    
    # Count by triage status
    untriaged = await _count_by_status(db, 'triage_status', TriageStatus.UNTRIAGED.value)
    trash = await _count_by_status(db, 'triage_status', TriageStatus.TRASH.value)
    salvage = await _count_by_status(db, 'triage_status', TriageStatus.SALVAGE.value)
    must_finish = await _count_by_status(db, 'triage_status', TriageStatus.MUST_FINISH.value)
    
    # Count by hygiene status
    pending_harvest_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.triage_status == TriageStatus.SALVAGE.value,
            Project.hygiene_status == HygieneStatus.PENDING.value
        )
    )
    pending_harvest = pending_harvest_result.scalar() or 0
    
    ready_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.hygiene_status == HygieneStatus.READY_FOR_MIGRATION.value
        )
    )
    ready_for_migration = ready_result.scalar() or 0
    
    # Average score
    avg_result = await db.execute(
        select(func.avg(Project.signal_score))
    )
    average_score = avg_result.scalar() or 0
    
    return {
        'total': total,
        'untriaged': untriaged,
        'trash': trash,
        'salvage': salvage,
        'must_finish': must_finish,
        'pending_harvest': pending_harvest,
        'ready_for_migration': ready_for_migration,
        'average_score': float(average_score),
    }


async def _count_by_status(
    db: AsyncSession, 
    status_field: str, 
    status_value: str
) -> int:
    """Helper to count projects by a status field."""
    column = getattr(Project, status_field)
    result = await db.execute(
        select(func.count(Project.id)).where(column == status_value)
    )
    return result.scalar() or 0

