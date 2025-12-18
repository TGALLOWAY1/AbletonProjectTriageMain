"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings, ensure_directories
from app.database import init_db, close_db
from app.api import scan, projects, audio, migration, studio, settings as settings_api
# Import models to ensure they're registered with SQLAlchemy
from app.models import Project, StudioProject, MigrationManifest, ScanPath

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Ableton Triage Assistant...")
    ensure_directories()
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="A macOS application for triaging, organizing, and managing Ableton Live projects",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(scan.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(audio.router, prefix="/api")
app.include_router(migration.router, prefix="/api")
app.include_router(studio.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


@app.get("/api/settings")
async def get_settings():
    """Get application settings."""
    return {
        "scan_paths": settings.default_scan_paths,
        "archive_destination": "",
        "curated_destination": "",
    }


# Serve frontend static files in production
# This will be used when the app is packaged
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


def run_dev_server():
    """Run the development server."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="debug" if settings.debug else "info"
    )


if __name__ == "__main__":
    run_dev_server()

