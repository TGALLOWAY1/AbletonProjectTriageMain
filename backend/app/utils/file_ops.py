"""Safe file operations with rollback capability."""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import logging

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FileOperation:
    """Represents a single file operation."""
    operation_type: str  # 'move', 'copy', 'delete'
    source: str
    destination: Optional[str] = None
    timestamp: str = ""
    success: bool = False
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class SafeFileOperations:
    """
    Provides safe file operations with manifest-based rollback capability.
    
    All operations are logged to a manifest file that can be used
    to reverse the changes if needed.
    """
    
    def __init__(self, manifest_path: Optional[str] = None):
        """
        Initialize with optional manifest path.
        
        Args:
            manifest_path: Path to save the operation manifest.
                          If None, uses default location.
        """
        if manifest_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.manifest_path = settings.manifests_dir / f"ops_{timestamp}.json"
        else:
            self.manifest_path = Path(manifest_path)
        
        self.operations: List[FileOperation] = []
    
    def move(self, source: str, destination: str, create_parents: bool = True) -> bool:
        """
        Safely move a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
            create_parents: Create parent directories if they don't exist
            
        Returns:
            True if successful, False otherwise
        """
        op = FileOperation(
            operation_type="move",
            source=source,
            destination=destination
        )
        
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                op.error = "Source does not exist"
                op.success = False
                self.operations.append(op)
                return False
            
            if create_parents:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use shutil.move for both files and directories
            shutil.move(str(source_path), str(dest_path))
            
            op.success = True
            self.operations.append(op)
            logger.info(f"Moved: {source} -> {destination}")
            return True
            
        except Exception as e:
            op.error = str(e)
            op.success = False
            self.operations.append(op)
            logger.error(f"Failed to move {source}: {e}")
            return False
    
    def copy(self, source: str, destination: str, create_parents: bool = True) -> bool:
        """
        Safely copy a file or directory.
        
        Args:
            source: Source path
            destination: Destination path
            create_parents: Create parent directories if they don't exist
            
        Returns:
            True if successful, False otherwise
        """
        op = FileOperation(
            operation_type="copy",
            source=source,
            destination=destination
        )
        
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                op.error = "Source does not exist"
                op.success = False
                self.operations.append(op)
                return False
            
            if create_parents:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.is_dir():
                shutil.copytree(str(source_path), str(dest_path))
            else:
                shutil.copy2(str(source_path), str(dest_path))
            
            op.success = True
            self.operations.append(op)
            logger.info(f"Copied: {source} -> {destination}")
            return True
            
        except Exception as e:
            op.error = str(e)
            op.success = False
            self.operations.append(op)
            logger.error(f"Failed to copy {source}: {e}")
            return False
    
    def delete(self, path: str) -> bool:
        """
        Safely delete a file or directory.
        
        Note: For safety, this moves to a trash location rather than
        permanently deleting. Use force_delete for permanent deletion.
        
        Args:
            path: Path to delete
            
        Returns:
            True if successful, False otherwise
        """
        trash_path = settings.rollback_dir / "trash" / datetime.now().strftime("%Y%m%d") / Path(path).name
        return self.move(path, str(trash_path))
    
    def force_delete(self, path: str) -> bool:
        """
        Permanently delete a file or directory.
        
        Warning: This cannot be undone!
        
        Args:
            path: Path to delete
            
        Returns:
            True if successful, False otherwise
        """
        op = FileOperation(
            operation_type="delete",
            source=path
        )
        
        try:
            target = Path(path)
            
            if not target.exists():
                op.error = "Path does not exist"
                op.success = False
                self.operations.append(op)
                return False
            
            if target.is_dir():
                shutil.rmtree(str(target))
            else:
                target.unlink()
            
            op.success = True
            self.operations.append(op)
            logger.info(f"Deleted: {path}")
            return True
            
        except Exception as e:
            op.error = str(e)
            op.success = False
            self.operations.append(op)
            logger.error(f"Failed to delete {path}: {e}")
            return False
    
    def save_manifest(self) -> str:
        """
        Save the operation manifest to disk.
        
        Returns:
            Path to the saved manifest file
        """
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        manifest_data = {
            "timestamp": datetime.now().isoformat(),
            "operations": [asdict(op) for op in self.operations],
            "summary": {
                "total": len(self.operations),
                "successful": sum(1 for op in self.operations if op.success),
                "failed": sum(1 for op in self.operations if not op.success),
            }
        }
        
        with open(self.manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"Saved manifest: {self.manifest_path}")
        return str(self.manifest_path)
    
    @classmethod
    def rollback_from_manifest(cls, manifest_path: str) -> Dict[str, Any]:
        """
        Rollback operations using a manifest file.
        
        Args:
            manifest_path: Path to the manifest file
            
        Returns:
            Dictionary with rollback results
        """
        with open(manifest_path, 'r') as f:
            manifest_data = json.load(f)
        
        results = {
            "rolled_back": 0,
            "failed": 0,
            "errors": []
        }
        
        # Process operations in reverse order
        for op_data in reversed(manifest_data.get("operations", [])):
            if not op_data.get("success"):
                continue
            
            try:
                if op_data["operation_type"] == "move":
                    # Reverse the move
                    source = op_data["destination"]
                    destination = op_data["source"]
                    
                    if Path(source).exists():
                        Path(destination).parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(source, destination)
                        results["rolled_back"] += 1
                        logger.info(f"Rolled back: {source} -> {destination}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Cannot rollback - not found: {source}")
                
                elif op_data["operation_type"] == "copy":
                    # Remove the copied file
                    dest = op_data["destination"]
                    if Path(dest).exists():
                        if Path(dest).is_dir():
                            shutil.rmtree(dest)
                        else:
                            Path(dest).unlink()
                        results["rolled_back"] += 1
                        logger.info(f"Rolled back copy: removed {dest}")
                    else:
                        results["failed"] += 1
                        results["errors"].append(f"Cannot rollback copy - not found: {dest}")
                        
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(str(e))
                logger.error(f"Rollback error: {e}")
        
        return results


def cleanup_empty_directories(root_path: str) -> int:
    """
    Remove empty directories recursively.
    
    Args:
        root_path: Root path to start cleaning from
        
    Returns:
        Number of directories removed
    """
    removed = 0
    root = Path(root_path)
    
    if not root.exists():
        return 0
    
    # Walk bottom-up
    for dirpath, dirnames, filenames in os.walk(str(root), topdown=False):
        if not dirnames and not filenames:
            try:
                os.rmdir(dirpath)
                removed += 1
                logger.info(f"Removed empty directory: {dirpath}")
            except Exception as e:
                logger.warning(f"Could not remove {dirpath}: {e}")
    
    return removed

