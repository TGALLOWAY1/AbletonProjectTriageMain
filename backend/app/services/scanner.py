"""Phase 1: Deep Scan service for discovering Ableton projects."""

import os
import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass, field
import logging

from app.config import settings
from app.services.scorer import (
    calculate_signal_score, 
    extract_keywords_from_filename,
    ScoringFactors
)
from app.utils.xml_parser import AbletonProjectParser, analyze_dependency_health

logger = logging.getLogger(__name__)


@dataclass
class ScanError:
    """Represents an error encountered during scanning."""
    path: str
    error: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ScanProgress:
    """Tracks the progress of a scan operation."""
    status: str = "idle"  # idle, scanning, completed, error
    current_path: Optional[str] = None
    files_scanned: int = 0
    projects_found: int = 0
    errors: List[ScanError] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class ScannedProject:
    """Represents a discovered Ableton project."""
    project_path: str  # Path to the project folder (not the .als file)
    project_name: str  # Folder name
    project_type: str = "PROJECT"  # "PROJECT" or "BUCKET"
    champion_file: str = ""  # The main .als file (newest)
    version_count: int = 0  # Number of .als files in the folder
    versions: List[str] = field(default_factory=list)  # List of other .als filenames
    key_signature: Optional[str] = None
    bpm: Optional[int] = None
    diamond_tier_keywords: List[str] = field(default_factory=list)
    gold_tier_keywords: List[str] = field(default_factory=list)
    time_spent_days: Optional[int] = None
    backup_count: int = 0
    cluster_id: Optional[str] = None
    audio_preview_path: Optional[str] = None
    signal_score: int = 0
    hygiene_report: Optional[Dict[str, Any]] = None


# Regex patterns for filename parsing
KEY_PATTERN = re.compile(
    r'\b([A-G][b#]?)\s*(m|min|minor|maj|major)?\b',
    re.IGNORECASE
)
BPM_PATTERN = re.compile(r'\b(\d{2,3})\s*(?:bpm)?\b', re.IGNORECASE)
VERSION_PATTERN = re.compile(
    r'[_\s\-](?:v|ver|version)?(\d+)|[_\s\-](final|master|render|mix)',
    re.IGNORECASE
)


class Scanner:
    """
    Ableton project scanner for Phase 1: Deep Scan.
    
    Discovers .als files, extracts metadata from filenames,
    analyzes backup folders, and calculates signal scores.
    """
    
    # Default scan timeout: 30 minutes
    SCAN_TIMEOUT_SECONDS = 30 * 60

    def __init__(self):
        self.progress = ScanProgress()
        self._cancel_requested = False

    def cancel(self):
        """Request cancellation of the current scan."""
        self._cancel_requested = True

    async def scan_directories(
        self,
        paths: List[str],
        timeout_seconds: Optional[int] = None,
    ) -> AsyncGenerator[ScannedProject, None]:
        """
        Scan directories for Ableton projects.

        Args:
            paths: List of directory paths to scan
            timeout_seconds: Maximum scan duration (default 30 min)

        Yields:
            ScannedProject objects as they are discovered
        """
        self.progress = ScanProgress(
            status="scanning",
            started_at=datetime.now().isoformat()
        )
        self._cancel_requested = False
        timeout = timeout_seconds or self.SCAN_TIMEOUT_SECONDS
        scan_start = datetime.now()

        try:
            for base_path in paths:
                base_path = os.path.expanduser(base_path)

                if not os.path.exists(base_path):
                    self.progress.errors.append(ScanError(
                        path=base_path,
                        error="Path does not exist"
                    ))
                    continue

                async for project in self._scan_directory(base_path):
                    if self._cancel_requested:
                        self.progress.status = "cancelled"
                        return

                    # Check timeout
                    elapsed = (datetime.now() - scan_start).total_seconds()
                    if elapsed > timeout:
                        self.progress.status = "completed"
                        self.progress.completed_at = datetime.now().isoformat()
                        self.progress.errors.append(ScanError(
                            path=base_path,
                            error=f"Scan timed out after {int(elapsed)}s"
                        ))
                        logger.warning(f"Scan timed out after {int(elapsed)}s")
                        return

                    yield project

            self.progress.status = "completed"
            self.progress.completed_at = datetime.now().isoformat()

        except Exception as e:
            logger.error(f"Scan error: {e}")
            self.progress.status = "error"
            self.progress.errors.append(ScanError(
                path="",
                error=str(e)
            ))
    
    def _get_project_type(self, dirnames: List[str], filenames: List[str]) -> str:
        """
        Determine if a folder is a PROJECT_FOLDER, LOOSE_CONTAINER, or CATEGORY_FOLDER.
        
        Args:
            dirnames: List of subdirectory names
            filenames: List of filenames in the current directory
            
        Returns:
            "PROJECT_FOLDER", "LOOSE_CONTAINER", or "CATEGORY_FOLDER"
        """
        # 1. STRONG INDICATOR: Has standard Ableton structure
        has_samples = "Samples" in dirnames
        has_backup = "Backup" in dirnames
        has_project_info = "Project Info" in dirnames
        
        if has_samples or has_backup or has_project_info:
            return "PROJECT_FOLDER"
        
        # 2. LOOSE FILE INDICATOR: Just contains .als files
        als_files = [f for f in filenames if f.endswith('.als')]
        if als_files:
            return "LOOSE_CONTAINER"
            
        return "CATEGORY_FOLDER"
    
    def _find_champion_file(self, folder_path: str, filenames: List[str]) -> Tuple[Optional[str], List[str]]:
        """
        Find the champion (newest) .als file and list all versions.
        
        Args:
            folder_path: Path to the folder containing .als files
            filenames: List of filenames in the folder
            
        Returns:
            Tuple of (champion_file_path, list_of_other_version_filenames)
        """
        als_files = [f for f in filenames if f.endswith('.als')]
        
        if not als_files:
            return None, []
        
        # Get full paths and modification times
        file_data = []
        for f in als_files:
            full_path = os.path.join(folder_path, f)
            try:
                mtime = os.path.getmtime(full_path)
                file_data.append((full_path, f, mtime))
            except (OSError, FileNotFoundError):
                # File might be an iCloud ghost or inaccessible
                logger.warning(f"Cannot access file (possibly offline): {full_path}")
                continue
        
        if not file_data:
            return None, []
        
        # Sort by modification time (newest first)
        file_data.sort(key=lambda x: x[2], reverse=True)
        
        champion_path, champion_name = file_data[0][0], file_data[0][1]
        other_versions = [f[1] for f in file_data[1:]]
        
        return champion_path, other_versions
    
    async def _scan_directory(
        self, 
        directory: str
    ) -> AsyncGenerator[ScannedProject, None]:
        """
        Smart recursive scan using os.walk with project folder detection.
        Stops recursion when a PROJECT_FOLDER is found.
        """
        try:
            # Use os.walk for smart traversal
            for root, dirnames, filenames in os.walk(directory):
                if self._cancel_requested:
                    return
                
                self.progress.current_path = root
                self.progress.files_scanned += 1
                
                # Yield control periodically to keep UI responsive
                if self.progress.files_scanned % 100 == 0:
                    await asyncio.sleep(0)
                
                folder_name = os.path.basename(root)
                
                # IGNORE SYSTEM FOLDERS
                if folder_name.startswith('.') or folder_name in ["__MACOSX", "Library", "System", "node_modules", "__pycache__"]:
                    # Also skip recursion into these folders
                    dirnames[:] = []
                    continue
                
                try:
                    # ANALYZE THE FOLDER
                    folder_type = self._get_project_type(dirnames, filenames)
                    
                    if folder_type == "PROJECT_FOLDER":
                        # It's a proper project folder - process it
                        project = await self._process_project_folder(root, filenames)
                        if project:
                            self.progress.projects_found += 1
                            yield project
                        
                        # STOP RECURSION: Don't look inside 'Samples' or 'Backup'
                        dirnames[:] = []
                        
                    elif folder_type == "LOOSE_CONTAINER":
                        # It's a bucket folder with loose .als files
                        project = await self._process_bucket_folder(root, filenames)
                        if project:
                            self.progress.projects_found += 1
                            yield project
                        
                        # Continue recursion to find nested projects
                        
                    # else: CATEGORY_FOLDER - just continue recursion
                    
                except PermissionError:
                    self.progress.errors.append(ScanError(
                        path=root,
                        error="Permission denied"
                    ))
                    # Skip this directory
                    dirnames[:] = []
                except Exception as e:
                    logger.warning(f"Error processing folder {root}: {e}")
                    self.progress.errors.append(ScanError(
                        path=root,
                        error=str(e)
                    ))
                    
        except PermissionError:
            self.progress.errors.append(ScanError(
                path=directory,
                error="Permission denied"
            ))
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            self.progress.errors.append(ScanError(
                path=directory,
                error=str(e)
            ))
    
    async def _process_project_folder(
        self, 
        folder_path: str, 
        filenames: List[str]
    ) -> Optional[ScannedProject]:
        """
        Process a PROJECT_FOLDER: find champion file and process only that.
        
        Args:
            folder_path: Path to the project folder
            filenames: List of filenames in the folder (not including subdirectories)
        """
        folder_name = os.path.basename(folder_path)
        project_dir = Path(folder_path)
        
        # Find champion file and versions
        champion_path, other_versions = self._find_champion_file(folder_path, filenames)
        
        if not champion_path:
            logger.warning(f"No accessible .als files found in project folder: {folder_path}")
            return None
        
        champion_name = os.path.basename(champion_path)
        champion_stem = Path(champion_path).stem
        
        # Parse champion filename for metadata
        key_signature = self._extract_key(champion_stem)
        bpm = self._extract_bpm(champion_stem)
        diamond_kw, gold_kw = extract_keywords_from_filename(champion_stem)
        
        # Analyze backup folder
        backup_info = self._analyze_backup_folder(project_dir)
        
        # Find audio preview
        audio_preview = self._find_audio_preview(project_dir)
        
        # Generate cluster ID from folder name (not filename)
        cluster_id = self._generate_cluster_id(folder_name)
        
        # Perform dependency hygiene check on CHAMPION ONLY
        hygiene_report = None
        try:
            parser = AbletonProjectParser(champion_path)
            if parser.parse() and parser.xml_root is not None:
                hygiene_report = analyze_dependency_health(
                    parser.xml_root,
                    str(project_dir.resolve())
                )
        except (OSError, FileNotFoundError) as e:
            # iCloud ghost file or offline file
            logger.warning(f"File appears to be offline/unavailable: {champion_path}")
            return None
        except Exception as e:
            logger.warning(f"Failed to analyze dependency health for {champion_path}: {e}")
        
        # Calculate signal score
        scoring_factors = ScoringFactors(
            diamond_keywords=diamond_kw,
            gold_keywords=gold_kw,
            time_spent_days=backup_info.get('time_spent_days'),
            backup_count=backup_info.get('backup_count', 0),
            cluster_size=len(other_versions) + 1  # Include champion in count
        )
        signal_score = calculate_signal_score(scoring_factors)
        
        return ScannedProject(
            project_path=folder_path,  # Folder path, not file path
            project_name=folder_name,  # Folder name
            project_type="PROJECT",
            champion_file=champion_name,
            version_count=len(other_versions) + 1,
            versions=other_versions,
            key_signature=key_signature,
            bpm=bpm,
            diamond_tier_keywords=diamond_kw,
            gold_tier_keywords=gold_kw,
            time_spent_days=backup_info.get('time_spent_days'),
            backup_count=backup_info.get('backup_count', 0),
            cluster_id=cluster_id,
            audio_preview_path=audio_preview,
            signal_score=signal_score,
            hygiene_report=hygiene_report,
        )
    
    async def _process_bucket_folder(
        self, 
        folder_path: str, 
        filenames: List[str]
    ) -> Optional[ScannedProject]:
        """
        Process a BUCKET folder (loose .als files): treat newest as champion.
        
        Args:
            folder_path: Path to the bucket folder
            filenames: List of filenames in the folder
        """
        folder_name = os.path.basename(folder_path)
        project_dir = Path(folder_path)
        
        # Find champion file and versions
        champion_path, other_versions = self._find_champion_file(folder_path, filenames)
        
        if not champion_path:
            return None
        
        champion_name = os.path.basename(champion_path)
        champion_stem = Path(champion_path).stem
        
        # Parse champion filename for metadata
        key_signature = self._extract_key(champion_stem)
        bpm = self._extract_bpm(champion_stem)
        diamond_kw, gold_kw = extract_keywords_from_filename(champion_stem)
        
        # Buckets don't have backup folders typically, but check anyway
        backup_info = self._analyze_backup_folder(project_dir)
        
        # Find audio preview
        audio_preview = self._find_audio_preview(project_dir)
        
        # Generate cluster ID from folder name
        cluster_id = self._generate_cluster_id(folder_name)
        
        # Perform dependency hygiene check on CHAMPION ONLY
        hygiene_report = None
        try:
            parser = AbletonProjectParser(champion_path)
            if parser.parse() and parser.xml_root is not None:
                hygiene_report = analyze_dependency_health(
                    parser.xml_root,
                    str(project_dir.resolve())
                )
        except (OSError, FileNotFoundError) as e:
            # iCloud ghost file or offline file
            logger.warning(f"File appears to be offline/unavailable: {champion_path}")
            return None
        except Exception as e:
            logger.warning(f"Failed to analyze dependency health for {champion_path}: {e}")
        
        # Calculate signal score (buckets are typically lower priority)
        scoring_factors = ScoringFactors(
            diamond_keywords=diamond_kw,
            gold_keywords=gold_kw,
            time_spent_days=backup_info.get('time_spent_days'),
            backup_count=backup_info.get('backup_count', 0),
            cluster_size=len(other_versions) + 1
        )
        signal_score = calculate_signal_score(scoring_factors)
        
        return ScannedProject(
            project_path=folder_path,  # Folder path
            project_name=folder_name,  # Folder name
            project_type="BUCKET",
            champion_file=champion_name,
            version_count=len(other_versions) + 1,
            versions=other_versions,
            key_signature=key_signature,
            bpm=bpm,
            diamond_tier_keywords=diamond_kw,
            gold_tier_keywords=gold_kw,
            time_spent_days=backup_info.get('time_spent_days'),
            backup_count=backup_info.get('backup_count', 0),
            cluster_id=cluster_id,
            audio_preview_path=audio_preview,
            signal_score=signal_score,
            hygiene_report=hygiene_report,
        )
    
    def _extract_key(self, filename: str) -> Optional[str]:
        """Extract musical key from filename."""
        match = KEY_PATTERN.search(filename)
        if match:
            key = match.group(1).upper()
            modifier = match.group(2)
            if modifier and modifier.lower() in ('m', 'min', 'minor'):
                return f"{key}m"
            return key
        return None
    
    def _extract_bpm(self, filename: str) -> Optional[int]:
        """Extract BPM from filename."""
        match = BPM_PATTERN.search(filename)
        if match:
            bpm = int(match.group(1))
            # Validate reasonable BPM range
            if 60 <= bpm <= 200:
                return bpm
        return None
    
    def _analyze_backup_folder(self, project_dir: Path) -> Dict[str, Any]:
        """
        Analyze the Backup folder to calculate "sweat equity".
        
        Returns:
            Dict with 'backup_count' and 'time_spent_days'
        """
        backup_dir = project_dir / "Backup"
        
        if not backup_dir.exists():
            return {'backup_count': 0, 'time_spent_days': None}
        
        try:
            backup_files = list(backup_dir.glob("*.als"))
            backup_count = len(backup_files)
            
            if backup_count == 0:
                return {'backup_count': 0, 'time_spent_days': None}
            
            # Calculate time span from oldest to newest backup
            timestamps = []
            for bf in backup_files:
                try:
                    timestamps.append(bf.stat().st_mtime)
                except Exception:
                    pass

            if len(timestamps) >= 2:
                oldest = min(timestamps)
                newest = max(timestamps)
                days = (newest - oldest) / (60 * 60 * 24)
                time_spent_days = max(1, int(days))
            else:
                time_spent_days = 1
            
            return {
                'backup_count': backup_count,
                'time_spent_days': time_spent_days
            }
            
        except Exception as e:
            logger.warning(f"Error analyzing backup folder: {e}")
            return {'backup_count': 0, 'time_spent_days': None}
    
    def _find_audio_preview(self, project_dir: Path) -> Optional[str]:
        """Find an audio preview file (.wav or .mp3) in the project folder."""
        audio_extensions = {'.wav', '.wave', '.mp3', '.aif', '.aiff'}
        preferred_keywords = ['render', 'export', 'mix', 'master']

        # Collect all audio files (case-insensitive extension matching)
        audio_files = [
            f for f in project_dir.iterdir()
            if f.is_file() and f.suffix.lower() in audio_extensions
        ]

        if not audio_files:
            return None

        # Prefer files with priority keywords in name
        for f in audio_files:
            name_lower = f.name.lower()
            if any(kw in name_lower for kw in preferred_keywords):
                return str(f)

        # Otherwise return first found
        return str(audio_files[0])
    
    def _generate_cluster_id(self, filename: str) -> str:
        """
        Generate a cluster ID for grouping project versions.
        
        Strips version numbers and common suffixes to create a base name
        that can group related projects together.
        Handles: v1, v2, version 1, version 2, etc.
        """
        # Normalize the filename
        cluster_name = filename.lower()
        
        # Remove version patterns: v1, v2, version 1, version 2, ver 1, etc.
        cluster_name = re.sub(
            r'[_\s\-]*(?:v|ver|version)[_\s\-]*\d+',
            '',
            cluster_name,
            flags=re.IGNORECASE
        )
        
        # Remove standalone numbers that might be versions (but keep BPM)
        # Only remove if followed by common version suffixes
        cluster_name = re.sub(
            r'[_\s\-](\d+)(?=[_\s\-]*(?:final|master|render|mix|export|bounce|als|$))',
            '',
            cluster_name,
            flags=re.IGNORECASE
        )
        
        # Remove common suffixes
        cluster_name = re.sub(
            r'[_\s\-]*(?:final|master|render|mix|export|bounce)\d*',
            '',
            cluster_name,
            flags=re.IGNORECASE
        )
        
        # Remove trailing underscores/hyphens/spaces
        cluster_name = re.sub(r'[_\s\-]+$', '', cluster_name)
        cluster_name = re.sub(r'^[_\s\-]+', '', cluster_name)
        
        return cluster_name.strip()


def cluster_projects(projects: List[ScannedProject]) -> Dict[str, List[ScannedProject]]:
    """
    Group projects by their cluster ID.
    
    Args:
        projects: List of scanned projects
        
    Returns:
        Dictionary mapping cluster_id to list of projects in that cluster
    """
    clusters: Dict[str, List[ScannedProject]] = {}
    
    for project in projects:
        cluster_id = project.cluster_id or project.project_name.lower()
        if cluster_id not in clusters:
            clusters[cluster_id] = []
        clusters[cluster_id].append(project)
    
    return clusters


def update_cluster_scores(projects: List[ScannedProject]) -> List[ScannedProject]:
    """
    Update signal scores based on cluster sizes.
    
    Projects with multiple versions get a bonus to their signal score.
    """
    clusters = cluster_projects(projects)
    
    for cluster_id, cluster_projects_list in clusters.items():
        cluster_size = len(cluster_projects_list)
        
        if cluster_size > 1:
            for project in cluster_projects_list:
                # Recalculate score with cluster size
                factors = ScoringFactors(
                    diamond_keywords=project.diamond_tier_keywords,
                    gold_keywords=project.gold_tier_keywords,
                    time_spent_days=project.time_spent_days,
                    backup_count=project.backup_count,
                    cluster_size=cluster_size
                )
                project.signal_score = calculate_signal_score(factors)
    
    return projects


def select_best_project_from_cluster(cluster: List[ScannedProject]) -> ScannedProject:
    """
    Select the best project from a cluster based on multiple criteria.
    
    Priority order:
    1. Highest signal score
    2. Most backups (indicates more work invested)
    3. Longest time spent (more development time)
    4. Largest project size (if available)
    5. Has audio preview
    6. Most recent (by filename containing "final", "master", etc.)
    
    Args:
        cluster: List of projects in the same cluster
        
    Returns:
        The best project from the cluster
    """
    if len(cluster) == 1:
        return cluster[0]
    
    def get_project_size(project: ScannedProject) -> int:
        """Get project folder size in bytes."""
        try:
            project_dir = Path(project.project_path).parent
            if project_dir.exists():
                total = 0
                for f in project_dir.rglob('*'):
                    if f.is_file():
                        total += f.stat().st_size
                return total
        except Exception:
            pass
        return 0
    
    def has_final_keywords(project: ScannedProject) -> bool:
        """Check if project name suggests it's a final version."""
        name_lower = project.project_name.lower()
        final_keywords = ['final', 'master', 'render', 'complete', 'finished']
        return any(kw in name_lower for kw in final_keywords)
    
    # Sort by multiple criteria
    best = max(cluster, key=lambda p: (
        p.signal_score,  # Highest score first
        p.backup_count,  # Most backups
        p.time_spent_days or 0,  # Longest time
        get_project_size(p),  # Largest size
        1 if p.audio_preview_path else 0,  # Has preview
        1 if has_final_keywords(p) else 0,  # Final keywords
    ))
    
    return best


def deduplicate_clusters(projects: List[ScannedProject]) -> List[ScannedProject]:
    """
    Deduplicate projects by cluster, keeping only the best one from each cluster.
    
    Args:
        projects: List of all scanned projects
        
    Returns:
        List with only the best project from each cluster
    """
    clusters = cluster_projects(projects)
    deduplicated = []
    
    for cluster_id, cluster_projects_list in clusters.items():
        if len(cluster_projects_list) > 1:
            # Multiple versions - keep only the best
            best = select_best_project_from_cluster(cluster_projects_list)
            deduplicated.append(best)
        else:
            # Single project - keep it
            deduplicated.append(cluster_projects_list[0])
    
    return deduplicated

