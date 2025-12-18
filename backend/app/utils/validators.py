"""Path and permission validators."""

import os
from pathlib import Path
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


def validate_path_access(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a path exists and is accessible.
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        expanded = os.path.expanduser(path)
        p = Path(expanded)
        
        if not p.exists():
            return False, f"Path does not exist: {path}"
        
        if not os.access(expanded, os.R_OK):
            return False, f"No read permission: {path}"
        
        return True, None
        
    except Exception as e:
        return False, f"Error validating path: {e}"


def validate_write_access(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a path is writable.
    
    For non-existent paths, checks the parent directory.
    
    Args:
        path: Path to validate
        
    Returns:
        Tuple of (is_writable, error_message)
    """
    try:
        expanded = os.path.expanduser(path)
        p = Path(expanded)
        
        # If path exists, check direct write access
        if p.exists():
            if not os.access(expanded, os.W_OK):
                return False, f"No write permission: {path}"
            return True, None
        
        # Check parent directory for write access
        parent = p.parent
        while not parent.exists() and parent != parent.parent:
            parent = parent.parent
        
        if not os.access(str(parent), os.W_OK):
            return False, f"No write permission on parent: {parent}"
        
        return True, None
        
    except Exception as e:
        return False, f"Error validating write access: {e}"


def validate_ableton_project_path(path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a path is a valid Ableton project.
    
    Args:
        path: Path to the .als file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        p = Path(path)
        
        if not p.exists():
            return False, "File does not exist"
        
        if not p.suffix.lower() == '.als':
            return False, "Not an Ableton Live Set file (.als)"
        
        if not os.access(str(p), os.R_OK):
            return False, "No read permission"
        
        # Check if it's a valid gzip file (Ableton format)
        import gzip
        try:
            with gzip.open(p, 'rb') as f:
                f.read(10)  # Read a small amount to verify
        except gzip.BadGzipFile:
            # Might be older XML format, try reading as text
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    header = f.read(100)
                    if '<Ableton' not in header and '<?xml' not in header:
                        return False, "Not a valid Ableton project file"
            except:
                return False, "Cannot read file"
        
        return True, None
        
    except Exception as e:
        return False, f"Error validating project: {e}"


def get_safe_scan_paths(paths: List[str]) -> List[str]:
    """
    Filter a list of paths to only include safe, accessible ones.
    
    Args:
        paths: List of paths to validate
        
    Returns:
        List of valid, accessible paths
    """
    safe_paths = []
    
    for path in paths:
        is_valid, error = validate_path_access(path)
        if is_valid:
            safe_paths.append(os.path.expanduser(path))
        else:
            logger.warning(f"Skipping path: {error}")
    
    return safe_paths


def is_system_directory(path: str) -> bool:
    """
    Check if a path is a system directory that should be skipped.
    
    Args:
        path: Path to check
        
    Returns:
        True if this is a system directory
    """
    system_dirs = [
        '/System',
        '/Library',
        '/private',
        '/bin',
        '/sbin',
        '/usr',
        '/var',
        '/etc',
        '/tmp',
        '/cores',
    ]
    
    # Also check for user Library but allow some subdirs
    expanded = os.path.expanduser(path)
    
    for sys_dir in system_dirs:
        if expanded.startswith(sys_dir):
            return True
    
    # Check for ~/Library but not ~/Library/Application Support/Ableton
    home_library = os.path.expanduser('~/Library')
    if expanded.startswith(home_library):
        # Allow Ableton-related paths
        allowed = [
            os.path.join(home_library, 'Application Support', 'Ableton'),
            os.path.join(home_library, 'Preferences', 'Ableton'),
        ]
        if not any(expanded.startswith(a) for a in allowed):
            return True
    
    return False


def estimate_scan_size(path: str) -> dict:
    """
    Estimate the size and file count of a directory for scanning.
    
    Args:
        path: Path to analyze
        
    Returns:
        Dictionary with estimated counts
    """
    expanded = os.path.expanduser(path)
    
    if not os.path.exists(expanded):
        return {"exists": False, "files": 0, "directories": 0, "als_files": 0}
    
    file_count = 0
    dir_count = 0
    als_count = 0
    
    try:
        for root, dirs, files in os.walk(expanded):
            # Limit the walk to prevent very long operations
            if file_count > 10000:
                break
            
            dir_count += len(dirs)
            file_count += len(files)
            als_count += sum(1 for f in files if f.endswith('.als'))
            
            # Skip directories we don't have permission for
            dirs[:] = [d for d in dirs if os.access(os.path.join(root, d), os.R_OK)]
            
    except PermissionError:
        pass
    
    return {
        "exists": True,
        "files": file_count,
        "directories": dir_count,
        "als_files": als_count,
        "truncated": file_count >= 10000
    }

