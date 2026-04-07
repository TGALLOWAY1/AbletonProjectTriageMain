"""Phase 4: Migration service for file operations."""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, TriageStatus, HygieneStatus
from app.models.migration import (
    MigrationManifest, MigrationStatus,
    MigrationOperation, MigrationPlan
)
from app.config import settings
from app.utils.xml_parser import validate_project_dependencies

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    manifest_path: str
    operations_completed: int
    operations_failed: int
    errors: List[str]


class MigrationService:
    """
    Service for Phase 4: Grand Migration.
    
    Handles safe file operations with rollback capability,
    manifest generation, and dependency validation.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_migration_plan(
        self,
        archive_destination: str,
        curated_destination: str,
        genre: str = "Other"
    ) -> MigrationPlan:
        """
        Generate a migration plan (dry-run preview).
        
        Args:
            archive_destination: Path for trash/harvested projects
            curated_destination: Path for must-finish projects
            genre: Genre subfolder for curated projects
            
        Returns:
            MigrationPlan with all planned operations
        """
        operations = []
        
        # Get all projects ready for archive (trash + harvested salvage)
        trash_projects = await self._get_archive_projects()
        
        # Get all must-finish projects ready for migration
        curated_projects = await self._get_curated_projects()
        
        # Generate archive operations
        date_folder = datetime.now().strftime("%Y-%m-%d")
        archive_base = Path(archive_destination).expanduser() / date_folder
        
        for project in trash_projects:
            project_dir = Path(project.project_path).parent
            dest = archive_base / project_dir.name
            
            operations.append(MigrationOperation(
                source=str(project_dir),
                destination=str(dest),
                type="archive",
                status="pending"
            ))
        
        # Generate curated operations
        curated_base = Path(curated_destination).expanduser() / genre
        
        for project in curated_projects:
            project_dir = Path(project.project_path).parent
            dest = curated_base / project_dir.name
            
            operations.append(MigrationOperation(
                source=str(project_dir),
                destination=str(dest),
                type="curated",
                status="pending"
            ))
        
        return MigrationPlan(
            timestamp=datetime.now().isoformat(),
            operations=operations,
            archive_destination=str(archive_base),
            curated_destination=str(curated_base)
        )
    
    async def _get_archive_projects(self) -> List[Project]:
        """Get projects that should be archived."""
        result = await self.db.execute(
            select(Project).where(
                (Project.triage_status == TriageStatus.TRASH.value) |
                (
                    (Project.triage_status == TriageStatus.SALVAGE.value) &
                    (Project.hygiene_status == HygieneStatus.HARVESTED.value)
                )
            )
        )
        return list(result.scalars().all())
    
    async def _get_curated_projects(self) -> List[Project]:
        """Get projects that should be moved to curated folder."""
        result = await self.db.execute(
            select(Project).where(
                Project.triage_status == TriageStatus.MUST_FINISH.value,
                Project.hygiene_status == HygieneStatus.READY_FOR_MIGRATION.value
            )
        )
        return list(result.scalars().all())
    
    async def validate_project(self, project_id: int) -> Dict[str, Any]:
        """
        Validate that a project is safe to migrate.
        
        Checks for external file dependencies.
        """
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return {'valid': False, 'error': 'Project not found', 'external_refs': []}
        
        return validate_project_dependencies(project.project_path)
    
    async def execute_migration(
        self,
        plan: MigrationPlan,
        manifest_path: Optional[str] = None
    ) -> MigrationResult:
        """
        Execute a migration plan.
        
        Args:
            plan: The migration plan to execute
            manifest_path: Path to save the manifest (optional)
            
        Returns:
            MigrationResult with status and any errors
        """
        errors = []
        completed = 0
        failed = 0
        
        # Generate manifest path if not provided
        if not manifest_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            manifest_path = str(settings.manifests_dir / f"migration_{timestamp}.json")
        
        # Ensure manifest directory exists
        Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Update plan operations as we go
        updated_operations = []
        
        archive_root = Path(plan.archive_destination).resolve()
        curated_root = Path(plan.curated_destination).resolve()

        for op in plan.operations:
            try:
                source = Path(op.source)
                destination = Path(op.destination)

                # Validate destination is within the expected target directory
                resolved_dest = destination.resolve()
                if not (str(resolved_dest).startswith(str(archive_root))
                        or str(resolved_dest).startswith(str(curated_root))):
                    updated_operations.append(MigrationOperation(
                        source=op.source,
                        destination=op.destination,
                        type=op.type,
                        status="failed",
                        error="Destination path escapes allowed directories"
                    ))
                    failed += 1
                    errors.append(f"Path validation failed: {destination}")
                    continue

                # Create destination parent directory
                destination.parent.mkdir(parents=True, exist_ok=True)

                # Perform the move
                if source.exists():
                    shutil.move(str(source), str(destination))
                    
                    updated_operations.append(MigrationOperation(
                        source=op.source,
                        destination=op.destination,
                        type=op.type,
                        status="completed"
                    ))
                    completed += 1
                    
                    logger.info(f"Moved: {source} -> {destination}")
                else:
                    updated_operations.append(MigrationOperation(
                        source=op.source,
                        destination=op.destination,
                        type=op.type,
                        status="failed",
                        error="Source not found"
                    ))
                    failed += 1
                    errors.append(f"Source not found: {source}")
                    
            except Exception as e:
                updated_operations.append(MigrationOperation(
                    source=op.source,
                    destination=op.destination,
                    type=op.type,
                    status="failed",
                    error=str(e)
                ))
                failed += 1
                errors.append(f"Failed to move {op.source}: {e}")
                logger.error(f"Migration error: {e}")
        
        # Save manifest
        manifest_data = {
            'timestamp': plan.timestamp,
            'executed_at': datetime.now().isoformat(),
            'archive_destination': plan.archive_destination,
            'curated_destination': plan.curated_destination,
            'operations': [asdict(op) if hasattr(op, '__dataclass_fields__') 
                          else op.model_dump() for op in updated_operations],
            'summary': {
                'completed': completed,
                'failed': failed,
            }
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        # Save to database
        manifest_record = MigrationManifest(
            manifest_path=manifest_path,
            status=MigrationStatus.COMPLETED.value if failed == 0 else MigrationStatus.PENDING.value
        )
        self.db.add(manifest_record)
        await self.db.commit()
        
        return MigrationResult(
            success=failed == 0,
            manifest_path=manifest_path,
            operations_completed=completed,
            operations_failed=failed,
            errors=errors
        )
    
    async def rollback_migration(self, manifest_id: int) -> MigrationResult:
        """
        Rollback a migration using its manifest.
        
        Args:
            manifest_id: ID of the migration manifest to rollback
            
        Returns:
            MigrationResult with rollback status
        """
        result = await self.db.execute(
            select(MigrationManifest).where(MigrationManifest.id == manifest_id)
        )
        manifest_record = result.scalar_one_or_none()
        
        if not manifest_record:
            return MigrationResult(
                success=False,
                manifest_path="",
                operations_completed=0,
                operations_failed=0,
                errors=["Manifest not found"]
            )
        
        # Load manifest file
        try:
            with open(manifest_record.manifest_path, 'r') as f:
                manifest_data = json.load(f)
        except Exception as e:
            return MigrationResult(
                success=False,
                manifest_path=manifest_record.manifest_path,
                operations_completed=0,
                operations_failed=0,
                errors=[f"Failed to load manifest: {e}"]
            )
        
        errors = []
        completed = 0
        failed = 0
        
        # Reverse the operations
        for op in manifest_data.get('operations', []):
            if op.get('status') != 'completed':
                continue
            
            try:
                source = Path(op['destination'])  # Now the source
                destination = Path(op['source'])  # Original location
                
                if source.exists():
                    # Ensure original parent exists
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(source), str(destination))
                    completed += 1
                    logger.info(f"Rolled back: {source} -> {destination}")
                else:
                    failed += 1
                    errors.append(f"Cannot rollback - not found: {source}")
                    
            except Exception as e:
                failed += 1
                errors.append(f"Rollback failed: {e}")
                logger.error(f"Rollback error: {e}")
        
        # Update manifest status
        manifest_record.status = MigrationStatus.ROLLED_BACK.value
        await self.db.commit()
        
        # Save rollback log
        rollback_path = settings.rollback_dir / f"rollback_{manifest_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        rollback_data = {
            'original_manifest': manifest_record.manifest_path,
            'rollback_time': datetime.now().isoformat(),
            'completed': completed,
            'failed': failed,
            'errors': errors,
        }
        
        with open(rollback_path, 'w') as f:
            json.dump(rollback_data, f, indent=2)
        
        return MigrationResult(
            success=failed == 0,
            manifest_path=str(rollback_path),
            operations_completed=completed,
            operations_failed=failed,
            errors=errors
        )
    
    async def get_migration_history(self) -> List[MigrationManifest]:
        """Get all migration manifests."""
        result = await self.db.execute(
            select(MigrationManifest).order_by(MigrationManifest.execution_date.desc())
        )
        return list(result.scalars().all())
    
    async def cleanup_empty_folders(self, paths: List[str]) -> int:
        """
        Remove empty folders after migration.
        
        Args:
            paths: List of directory paths to check
            
        Returns:
            Number of folders removed
        """
        removed = 0
        
        for path_str in paths:
            path = Path(path_str)
            if not path.exists():
                continue
            
            # Walk bottom-up to remove empty directories
            for dirpath, dirnames, filenames in os.walk(str(path), topdown=False):
                if not dirnames and not filenames:
                    try:
                        os.rmdir(dirpath)
                        removed += 1
                        logger.info(f"Removed empty folder: {dirpath}")
                    except Exception as e:
                        logger.warning(f"Could not remove folder {dirpath}: {e}")
        
        return removed

