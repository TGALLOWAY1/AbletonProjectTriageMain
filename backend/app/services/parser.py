"""Ableton file parsing service."""

from typing import Dict, Any, Optional
from pathlib import Path

from app.utils.xml_parser import AbletonProjectParser, validate_project_dependencies


async def parse_project_file(als_path: str) -> Dict[str, Any]:
    """
    Parse an Ableton project file and extract metadata.
    
    Args:
        als_path: Path to the .als file
        
    Returns:
        Dictionary with project information
    """
    parser = AbletonProjectParser(als_path)
    
    if not parser.parse():
        return {
            "success": False,
            "error": "Failed to parse project file",
            "path": als_path
        }
    
    info = parser.get_project_info()
    
    return {
        "success": True,
        "path": als_path,
        "name": Path(als_path).stem,
        "track_count": info["track_count"],
        "plugins": info["plugins"],
        "bpm": info["bpm"],
        "external_refs_count": info["external_refs_count"],
        "has_external_dependencies": info["has_external_dependencies"],
    }


async def validate_for_migration(als_path: str) -> Dict[str, Any]:
    """
    Validate that a project is safe to migrate.
    
    Checks for external dependencies that would break
    if the project is moved.
    
    Args:
        als_path: Path to the .als file
        
    Returns:
        Validation result dictionary
    """
    return validate_project_dependencies(als_path)


async def get_external_references(als_path: str) -> Dict[str, Any]:
    """
    Get all external file references from a project.
    
    Args:
        als_path: Path to the .als file
        
    Returns:
        Dictionary with external references
    """
    parser = AbletonProjectParser(als_path)
    
    if not parser.parse():
        return {
            "success": False,
            "error": "Failed to parse project file",
            "references": []
        }
    
    refs = parser.get_external_file_references()
    project_dir = Path(als_path).parent
    
    # Categorize references
    internal = []
    external = []
    missing = []
    
    for ref in refs:
        ref_path = Path(ref)
        
        try:
            ref_path.relative_to(project_dir)
            # It's relative to project dir - internal
            if ref_path.exists():
                internal.append(str(ref_path))
            else:
                missing.append(str(ref_path))
        except ValueError:
            # It's external
            if ref_path.exists():
                external.append(str(ref_path))
            else:
                missing.append(str(ref_path))
    
    return {
        "success": True,
        "total": len(refs),
        "internal": internal,
        "external": external,
        "missing": missing,
        "safe_to_migrate": len(external) == 0
    }

