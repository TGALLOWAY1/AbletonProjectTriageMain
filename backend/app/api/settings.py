"""API routes for user settings and preferences."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.settings import ScanPath, ScanPathResponse, ScanPathCreate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/scan-paths", response_model=List[ScanPathResponse])
async def get_scan_paths(db: AsyncSession = Depends(get_db)):
    """Get all saved scan paths."""
    result = await db.execute(select(ScanPath).order_by(ScanPath.created_at.desc()))
    paths = result.scalars().all()
    
    return [
        ScanPathResponse(
            id=p.id,
            path=p.path,
            created_at=p.created_at
        )
        for p in paths
    ]


@router.post("/scan-paths", response_model=ScanPathResponse)
async def add_scan_path(
    request: ScanPathCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a new scan path."""
    # Check if path already exists
    result = await db.execute(
        select(ScanPath).where(ScanPath.path == request.path)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return ScanPathResponse(
            id=existing.id,
            path=existing.path,
            created_at=existing.created_at
        )
    
    scan_path = ScanPath(path=request.path)
    db.add(scan_path)
    await db.commit()
    await db.refresh(scan_path)
    
    return ScanPathResponse(
        id=scan_path.id,
        path=scan_path.path,
        created_at=scan_path.created_at
    )


@router.delete("/scan-paths/{path_id}")
async def delete_scan_path(
    path_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a scan path."""
    result = await db.execute(
        delete(ScanPath).where(ScanPath.id == path_id)
    )
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Scan path not found")
    
    await db.commit()
    return {"message": "Scan path deleted"}


@router.delete("/scan-paths")
async def delete_scan_path_by_path(
    path: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a scan path by path string."""
    result = await db.execute(
        delete(ScanPath).where(ScanPath.path == path)
    )
    
    await db.commit()
    return {"message": "Scan path deleted", "deleted": result.rowcount > 0}






