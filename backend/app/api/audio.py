"""API routes for audio file streaming."""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import mimetypes

from app.database import get_db
from app.services.triage import get_project_by_id

router = APIRouter(prefix="/audio", tags=["audio"])


@router.get("/preview/{project_id}")
async def check_audio_preview(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if an audio preview is available for a project.
    """
    project = await get_project_by_id(db, project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.audio_preview_path:
        return {"available": False, "path": None}
    
    path = Path(project.audio_preview_path)
    if not path.exists():
        return {"available": False, "path": None}
    
    return {"available": True, "path": str(path)}


@router.get("/stream/{project_id}")
async def stream_audio(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream audio file for a project.
    
    Supports range requests for seeking.
    """
    project = await get_project_by_id(db, project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.audio_preview_path:
        raise HTTPException(status_code=404, detail="No audio preview available")
    
    path = Path(project.audio_preview_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        if path.suffix.lower() in ('.wav', '.wave'):
            mime_type = 'audio/wav'
        elif path.suffix.lower() == '.mp3':
            mime_type = 'audio/mpeg'
        elif path.suffix.lower() in ('.aif', '.aiff'):
            mime_type = 'audio/aiff'
        else:
            mime_type = 'application/octet-stream'
    
    # Resolve to absolute path and verify it doesn't escape via symlinks/traversal
    resolved = path.resolve()
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="Audio file not found")

    # Verify resolved path is within the project's directory
    project_dir = Path(project.project_path).resolve()
    if not resolved.is_relative_to(project_dir):
        raise HTTPException(status_code=403, detail="Audio file path escapes project directory")

    return FileResponse(
        path=str(resolved),
        media_type=mime_type,
        filename=path.name
    )


@router.get("/waveform/{project_id}")
async def get_waveform_data(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get waveform data for visualization.
    
    This is a simplified endpoint - the actual waveform
    rendering is done client-side with Wavesurfer.js.
    """
    project = await get_project_by_id(db, project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not project.audio_preview_path:
        raise HTTPException(status_code=404, detail="No audio preview available")
    
    path = Path(project.audio_preview_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Return basic file info - actual waveform generation
    # is done client-side by Wavesurfer.js
    return {
        "project_id": project_id,
        "file_name": path.name,
        "file_size": path.stat().st_size,
        "stream_url": f"/api/audio/stream/{project_id}"
    }

