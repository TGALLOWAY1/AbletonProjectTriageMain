"""API routes for Phase 4: Migration."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.migration import MigrationService
from app.services.studio import auto_populate_studio
from app.services.triage import get_project_stats
from app.models.migration import (
    MigrationPreviewRequest,
    MigrationExecuteRequest,
    MigrationRollbackRequest,
    MigrationPlan,
    MigrationManifestResponse,
    MigrationOperation,
)

router = APIRouter(prefix="/migration", tags=["migration"])


class MigrationPlanResponse(BaseModel):
    """Response schema for migration plan."""
    timestamp: str
    operations: List[dict]
    archive_destination: str
    curated_destination: str


class DependencyValidationResponse(BaseModel):
    """Response schema for dependency validation."""
    valid: bool
    external_refs: List[str]
    total_refs: int = 0
    error: str | None = None


@router.post("/preview", response_model=MigrationPlanResponse)
async def preview_migration(
    request: MigrationPreviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a migration plan preview (dry-run).

    This shows what operations would be performed without
    actually moving any files.
    """
    # Phase prerequisite: ensure projects have been scanned and triaged
    stats = await get_project_stats(db)
    if stats['total'] == 0:
        raise HTTPException(
            status_code=400,
            detail="No projects found. Complete Phase 1 (scan) first."
        )
    if stats['total'] == stats['untriaged']:
        raise HTTPException(
            status_code=400,
            detail="All projects are untriaged. Complete Phase 2 (triage) first."
        )

    service = MigrationService(db)
    try:
        plan = await service.generate_migration_plan(
            archive_destination=request.archive_destination,
            curated_destination=request.curated_destination
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return MigrationPlanResponse(
        timestamp=plan.timestamp,
        operations=[op.model_dump() for op in plan.operations],
        archive_destination=plan.archive_destination,
        curated_destination=plan.curated_destination
    )


@router.post("/execute")
async def execute_migration(
    request: MigrationExecuteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a migration plan.

    This actually moves files and creates a manifest for rollback.
    Validates project dependencies before executing.
    """
    service = MigrationService(db)

    # Generate the plan using the user-provided destinations
    try:
        plan = await service.generate_migration_plan(
            archive_destination=request.archive_destination,
            curated_destination=request.curated_destination
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Validate dependencies for curated (must-finish) projects before executing
    curated_projects = await service._get_curated_projects()
    dependency_errors = []
    for project in curated_projects:
        validation = await service.validate_project(project.id)
        if not validation.get('valid', False):
            dependency_errors.append(
                f"{project.project_name}: {validation.get('error', 'has external dependencies')}"
            )

    if dependency_errors:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Projects have unresolved dependencies",
                "errors": dependency_errors,
            }
        )

    result = await service.execute_migration(plan, request.manifest_path)

    if not result.success:
        return {
            "message": "Migration completed with errors",
            "manifest_id": result.manifest_id,
            "completed": result.operations_completed,
            "failed": result.operations_failed,
            "errors": result.errors
        }

    # Auto-populate studio with migrated must-finish projects
    studio_created = await auto_populate_studio(db)

    return {
        "message": "Migration completed successfully",
        "manifest_id": result.manifest_id,
        "manifest_path": result.manifest_path,
        "completed": result.operations_completed,
        "studio_projects_created": studio_created
    }


@router.post("/rollback")
async def rollback_migration(
    request: MigrationRollbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Rollback a previous migration using its manifest.
    """
    service = MigrationService(db)
    result = await service.rollback_migration(request.manifest_id)
    
    if not result.success:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Rollback failed",
                "errors": result.errors
            }
        )
    
    return {
        "message": "Rollback completed",
        "restored": result.operations_completed,
        "failed": result.operations_failed
    }


@router.get("/history", response_model=List[MigrationManifestResponse])
async def get_migration_history(db: AsyncSession = Depends(get_db)):
    """Get all migration manifests."""
    service = MigrationService(db)
    manifests = await service.get_migration_history()
    
    return [
        MigrationManifestResponse(
            id=m.id,
            manifest_path=m.manifest_path,
            execution_date=m.execution_date,
            status=m.status
        )
        for m in manifests
    ]


@router.get("/validate/{project_id}", response_model=DependencyValidationResponse)
async def validate_project_dependencies(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate that a project is self-contained and safe to migrate.
    
    Checks for external file dependencies (samples, presets, etc.)
    that are not contained within the project folder.
    """
    service = MigrationService(db)
    result = await service.validate_project(project_id)
    
    return DependencyValidationResponse(
        valid=result.get('valid', False),
        external_refs=result.get('external_refs', []),
        total_refs=result.get('total_refs', 0),
        error=result.get('error')
    )

