"""Project database models."""

from datetime import datetime
from typing import Optional, List
import json

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, 
    Enum as SQLEnum, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pydantic import BaseModel, ConfigDict
import enum

from app.database import Base


class TriageStatus(str, enum.Enum):
    """Project triage status."""
    UNTRIAGED = "untriaged"
    TRASH = "trash"
    SALVAGE = "salvage"
    MUST_FINISH = "must_finish"


class HygieneStatus(str, enum.Enum):
    """Project hygiene status."""
    PENDING = "pending"
    HARVESTED = "harvested"
    READY_FOR_MIGRATION = "ready_for_migration"


class Project(Base):
    """Ableton project database model."""
    
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    project_name: Mapped[str] = mapped_column(String(256), nullable=False)
    
    # Metadata extracted from filename
    key_signature: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    bpm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Signal scoring
    signal_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status tracking
    triage_status: Mapped[str] = mapped_column(
        String(32), 
        default=TriageStatus.UNTRIAGED.value,
        nullable=False
    )
    hygiene_status: Mapped[str] = mapped_column(
        String(32), 
        default=HygieneStatus.PENDING.value,
        nullable=False
    )
    
    # Version clustering
    cluster_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    
    # Time analysis
    time_spent_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Keywords (stored as JSON strings)
    _diamond_tier_keywords: Mapped[str] = mapped_column(
        "diamond_tier_keywords", 
        Text, 
        default="[]"
    )
    _gold_tier_keywords: Mapped[str] = mapped_column(
        "gold_tier_keywords", 
        Text, 
        default="[]"
    )
    
    # Audio preview
    audio_preview_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    # Backup analysis
    backup_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationship to studio project
    studio_project: Mapped[Optional["StudioProject"]] = relationship(
        "StudioProject",
        back_populates="project",
        uselist=False
    )
    
    @property
    def diamond_tier_keywords(self) -> List[str]:
        """Get diamond tier keywords as list."""
        return json.loads(self._diamond_tier_keywords)
    
    @diamond_tier_keywords.setter
    def diamond_tier_keywords(self, value: List[str]):
        """Set diamond tier keywords from list."""
        self._diamond_tier_keywords = json.dumps(value)
    
    @property
    def gold_tier_keywords(self) -> List[str]:
        """Get gold tier keywords as list."""
        return json.loads(self._gold_tier_keywords)
    
    @gold_tier_keywords.setter
    def gold_tier_keywords(self, value: List[str]):
        """Set gold tier keywords from list."""
        self._gold_tier_keywords = json.dumps(value)


class StudioProject(Base):
    """Studio manager project model for Phase 5."""
    
    __tablename__ = "studio_projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    genre: Mapped[str] = mapped_column(String(64), default="Other")
    _production_tags: Mapped[str] = mapped_column(
        "production_tags",
        Text,
        default="[]"
    )
    priority_order: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship
    project: Mapped["Project"] = relationship("Project", back_populates="studio_project")
    
    @property
    def production_tags(self) -> List[str]:
        """Get production tags as list."""
        return json.loads(self._production_tags)
    
    @production_tags.setter
    def production_tags(self, value: List[str]):
        """Set production tags from list."""
        self._production_tags = json.dumps(value)


# Pydantic schemas for API responses

class ProjectBase(BaseModel):
    """Base project schema."""
    project_path: str
    project_name: str
    key_signature: Optional[str] = None
    bpm: Optional[int] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    signal_score: int = 0
    diamond_tier_keywords: List[str] = []
    gold_tier_keywords: List[str] = []
    time_spent_days: Optional[int] = None
    backup_count: int = 0
    cluster_id: Optional[str] = None
    audio_preview_path: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Schema for project API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    signal_score: int
    triage_status: str
    hygiene_status: str
    cluster_id: Optional[str]
    time_spent_days: Optional[int]
    diamond_tier_keywords: List[str]
    gold_tier_keywords: List[str]
    audio_preview_path: Optional[str]
    backup_count: int
    created_at: datetime
    updated_at: datetime


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    triage_status: Optional[str] = None
    hygiene_status: Optional[str] = None


class StudioProjectResponse(BaseModel):
    """Schema for studio project API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    project: ProjectResponse
    genre: str
    production_tags: List[str]
    priority_order: int
    notes: Optional[str]


class StudioProjectUpdate(BaseModel):
    """Schema for updating studio project."""
    genre: Optional[str] = None
    production_tags: Optional[List[str]] = None
    priority_order: Optional[int] = None
    notes: Optional[str] = None

