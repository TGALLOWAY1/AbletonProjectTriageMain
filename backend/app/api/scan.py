"""API routes for Phase 1: Deep Scan."""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session_maker
from app.services.scanner import (
    Scanner, ScannedProject, ScanProgress, ScanError,
    update_cluster_scores, deduplicate_clusters
)
from app.models.project import Project, ProjectResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["scan"])

# Global scanner instance for tracking progress
_scanner: Scanner = Scanner()
_scan_results: List[ScannedProject] = []


class ScanRequest(BaseModel):
    """Request body for starting a scan."""
    paths: List[str]


class ScanProgressResponse(BaseModel):
    """Response schema for scan progress."""
    status: str
    current_path: str | None
    files_scanned: int
    projects_found: int
    errors: List[dict]
    started_at: str | None
    completed_at: str | None


async def run_scan(paths: List[str]):
    """Background task to run the scan.

    Creates its own DB session since background tasks outlive the
    request-scoped session from Depends(get_db).
    """
    global _scanner, _scan_results
    _scan_results = []

    # Use the global scanner instance (which was just created fresh)
    scanner = _scanner

    try:
        async for project in scanner.scan_directories(paths):
            _scan_results.append(project)

        # Update cluster scores
        _scan_results = update_cluster_scores(_scan_results)

        # Deduplicate clusters - keep only best project from each cluster
        _scan_results = deduplicate_clusters(_scan_results)

        # Create a fresh DB session for the background task
        async with async_session_maker() as db:
            # Save to database
            for scanned in _scan_results:
                # Construct the full path to the champion .als file
                # scanned.project_path is now the folder path
                champion_file_path = os.path.join(scanned.project_path, scanned.champion_file)

                # Check if project already exists (by folder path)
                existing = await db.execute(
                    Project.__table__.select().where(
                        Project.project_path == scanned.project_path
                    )
                )
                if existing.first():
                    continue

                project = Project(
                    project_path=scanned.project_path,  # Store folder path
                    project_name=scanned.project_name,
                    key_signature=scanned.key_signature,
                    bpm=scanned.bpm,
                    signal_score=scanned.signal_score,
                    cluster_id=scanned.cluster_id,
                    time_spent_days=scanned.time_spent_days,
                    backup_count=scanned.backup_count,
                    audio_preview_path=scanned.audio_preview_path,
                )
                project.diamond_tier_keywords = scanned.diamond_tier_keywords
                project.gold_tier_keywords = scanned.gold_tier_keywords

                db.add(project)

            await db.commit()
    except Exception as e:
        # Ensure scanner status is set to error if scan fails
        logger.error(f"Scan failed with error: {e}", exc_info=True)
        scanner.progress.status = "error"
        from datetime import datetime
        scanner.progress.errors.append(
            ScanError(
                path="",
                error=str(e),
                timestamp=datetime.now().isoformat()
            )
        )
        # Don't re-raise - let the scan complete with error status


@router.post("/start")
async def start_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a new scan operation.

    This runs in the background and progress can be tracked
    via the /status endpoint.
    """
    global _scanner, _scan_results

    # Only prevent starting if a scan is actively running
    if _scanner.progress.status == "scanning":
        raise HTTPException(
            status_code=409,
            detail="A scan is already in progress"
        )

    # Always create a fresh scanner instance for a new scan
    _scanner = Scanner()
    _scan_results = []

    background_tasks.add_task(run_scan, request.paths)

    return {"message": "Scan started", "paths": request.paths}


@router.get("/status", response_model=ScanProgressResponse)
async def get_scan_status():
    """Get the current scan progress."""
    progress = _scanner.progress
    return ScanProgressResponse(
        status=progress.status,
        current_path=progress.current_path,
        files_scanned=progress.files_scanned,
        projects_found=progress.projects_found,
        errors=[{
            "path": e.path,
            "error": e.error,
            "timestamp": e.timestamp
        } for e in progress.errors],
        started_at=progress.started_at,
        completed_at=progress.completed_at
    )


@router.post("/cancel")
async def cancel_scan():
    """Cancel the current scan operation."""
    global _scanner
    
    if _scanner.progress.status != "scanning":
        raise HTTPException(
            status_code=400,
            detail="No scan in progress"
        )
    
    _scanner.cancel()
    return {"message": "Scan cancellation requested"}


@router.post("/reset")
async def reset_scan():
    """Reset the scanner state to allow starting a new scan."""
    global _scanner, _scan_results
    
    _scanner = Scanner()
    _scan_results = []
    
    return {"message": "Scanner state reset"}


@router.get("/results")
async def get_scan_results(db: AsyncSession = Depends(get_db)):
    """
    Get the results of the last scan.
    
    Returns projects from the database.
    """
    from app.services.triage import get_projects
    
    projects = await get_projects(db, sort_by="signal_score", sort_order="desc")
    
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
        for p in projects
    ]

