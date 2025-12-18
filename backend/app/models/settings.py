"""Settings and user preferences database models."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, ConfigDict

from app.database import Base


class ScanPath(Base):
    """Stored scan path for user convenience."""
    
    __tablename__ = "scan_paths"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False
    )


# Pydantic schemas

class ScanPathResponse(BaseModel):
    """Schema for scan path API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    path: str
    created_at: datetime


class ScanPathCreate(BaseModel):
    """Schema for creating a scan path."""
    path: str


class ScanPathsListResponse(BaseModel):
    """Schema for list of scan paths."""
    paths: list[ScanPathResponse]






