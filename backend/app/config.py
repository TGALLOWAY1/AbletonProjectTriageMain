"""Application configuration management."""

from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Ableton Triage Assistant"
    debug: bool = False
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8765
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/ableton_triage.db"
    
    # Paths
    data_dir: Path = Path("./data")
    manifests_dir: Path = Path("./data/manifests")
    rollback_dir: Path = Path("./data/rollback")
    
    # Scan settings
    default_scan_paths: List[str] = []
    skip_hidden_dirs: bool = True
    
    # Keyword tiers for signal scoring
    diamond_keywords: List[str] = [
        "RENDER", "FINAL", "BANGER", "MASTER", "FINISHED", "COMPLETE"
    ]
    gold_keywords: List[str] = [
        "MUST USE", "GOOD DRUMS", "FIRE", "KEEPER", "PROMISING", "WIP"
    ]
    
    # Signal scoring weights
    diamond_weight: int = 30
    gold_weight: int = 15
    time_spent_multiplier: int = 2
    time_spent_cap: int = 40
    backup_bonus: int = 10
    backup_threshold: int = 5
    version_weight: int = 5
    version_cap: int = 20
    base_score: int = 20
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


def ensure_directories():
    """Ensure all required directories exist."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.manifests_dir.mkdir(parents=True, exist_ok=True)
    settings.rollback_dir.mkdir(parents=True, exist_ok=True)

