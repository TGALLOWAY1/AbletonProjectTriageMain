"""Migration database models."""

from datetime import datetime
from typing import Optional, List
import enum

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, ConfigDict

from app.database import Base


class MigrationStatus(str, enum.Enum):
    """Migration manifest status."""
    PENDING = "pending"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


class MigrationManifest(Base):
    """Migration manifest database model."""
    
    __tablename__ = "migration_manifests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manifest_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    execution_date: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=MigrationStatus.PENDING.value,
        nullable=False
    )


# Pydantic schemas

class MigrationOperation(BaseModel):
    """Schema for a single migration operation."""
    source: str
    destination: str
    type: str  # 'archive' or 'curated'
    status: str = "pending"  # 'pending', 'completed', 'failed'
    error: Optional[str] = None


class MigrationPlan(BaseModel):
    """Schema for migration plan preview."""
    timestamp: str
    operations: List[MigrationOperation]
    archive_destination: str
    curated_destination: str


class MigrationManifestResponse(BaseModel):
    """Schema for migration manifest API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    manifest_path: str
    execution_date: datetime
    status: str


class MigrationPreviewRequest(BaseModel):
    """Schema for migration preview request."""
    archive_destination: str
    curated_destination: str


class MigrationExecuteRequest(BaseModel):
    """Schema for migration execution request."""
    archive_destination: str
    curated_destination: str
    manifest_path: Optional[str] = None


class MigrationRollbackRequest(BaseModel):
    """Schema for migration rollback request."""
    manifest_id: int

