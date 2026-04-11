"""Phase 3: Hygiene tracking service."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, TriageStatus, HygieneStatus
from app.utils.xml_parser import validate_project_dependencies


async def get_projects_pending_harvest(db: AsyncSession) -> List[Project]:
    """
    Get all salvage projects that are pending harvest.
    
    These are projects marked as 'salvage' that haven't been
    processed yet (loops/presets extracted).
    """
    result = await db.execute(
        select(Project).where(
            Project.triage_status == TriageStatus.SALVAGE.value,
            Project.hygiene_status == HygieneStatus.PENDING.value
        ).order_by(Project.signal_score.desc())
    )
    return list(result.scalars().all())


async def get_projects_pending_hygiene(db: AsyncSession) -> List[Project]:
    """
    Get all must-finish projects pending hygiene work.
    
    These are projects marked as 'must_finish' that haven't had
    "Collect All and Save" performed yet.
    """
    result = await db.execute(
        select(Project).where(
            Project.triage_status == TriageStatus.MUST_FINISH.value,
            Project.hygiene_status == HygieneStatus.PENDING.value
        ).order_by(Project.signal_score.desc())
    )
    return list(result.scalars().all())


async def mark_as_harvested(
    db: AsyncSession,
    project_id: int
) -> Optional[Project]:
    """
    Mark a salvage project as harvested.
    
    This indicates the user has extracted all valuable
    loops/presets from the project.
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        return None
    
    if project.triage_status != TriageStatus.SALVAGE.value:
        raise ValueError("Only salvage projects can be marked as harvested")
    
    project.hygiene_status = HygieneStatus.HARVESTED.value
    await db.commit()
    await db.refresh(project)
    return project


async def mark_as_ready_for_migration(
    db: AsyncSession,
    project_id: int
) -> Optional[Project]:
    """
    Mark a must-finish project as ready for migration.
    
    This indicates the user has performed "Collect All and Save"
    and the project is self-contained.
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        return None
    
    if project.triage_status != TriageStatus.MUST_FINISH.value:
        raise ValueError("Only must-finish projects can be marked as ready for migration")

    # Validate that project dependencies are self-contained (Collect All and Save)
    dep_result = validate_project_dependencies(project.project_path)
    if not dep_result.get('valid', False):
        external_refs = dep_result.get('external_refs', [])
        if external_refs:
            raise ValueError(
                f"Project has {len(external_refs)} external dependencies. "
                f"Please run 'Collect All and Save' in Ableton first. "
                f"External refs: {', '.join(external_refs[:5])}"
            )

    project.hygiene_status = HygieneStatus.READY_FOR_MIGRATION.value
    await db.commit()
    await db.refresh(project)
    return project


async def get_hygiene_summary(db: AsyncSession) -> dict:
    """
    Get a summary of hygiene status across all projects.
    """
    salvage_pending = await get_projects_pending_harvest(db)
    hygiene_pending = await get_projects_pending_hygiene(db)
    
    return {
        'salvage_pending_count': len(salvage_pending),
        'hygiene_pending_count': len(hygiene_pending),
        'salvage_pending': [p.project_name for p in salvage_pending[:5]],
        'hygiene_pending': [p.project_name for p in hygiene_pending[:5]],
    }

