"""Tests for the migration service."""

import pytest
import tempfile
import json
from pathlib import Path

from app.utils.file_ops import (
    SafeFileOperations,
    cleanup_empty_directories,
)


class TestSafeFileOperations:
    """Tests for SafeFileOperations class."""
    
    def test_move_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source = tmpdir / "source.txt"
            dest = tmpdir / "dest.txt"
            
            source.write_text("test content")
            
            ops = SafeFileOperations(str(tmpdir / "manifest.json"))
            result = ops.move(str(source), str(dest))
            
            assert result is True
            assert not source.exists()
            assert dest.exists()
            assert dest.read_text() == "test content"
    
    def test_move_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source_dir = tmpdir / "source_dir"
            dest_dir = tmpdir / "dest_dir"
            
            source_dir.mkdir()
            (source_dir / "file.txt").write_text("content")
            
            ops = SafeFileOperations(str(tmpdir / "manifest.json"))
            result = ops.move(str(source_dir), str(dest_dir))
            
            assert result is True
            assert not source_dir.exists()
            assert dest_dir.exists()
            assert (dest_dir / "file.txt").exists()
    
    def test_move_nonexistent_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            ops = SafeFileOperations(str(tmpdir / "manifest.json"))
            result = ops.move(str(tmpdir / "nonexistent"), str(tmpdir / "dest"))
            
            assert result is False
    
    def test_copy_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source = tmpdir / "source.txt"
            dest = tmpdir / "dest.txt"
            
            source.write_text("test content")
            
            ops = SafeFileOperations(str(tmpdir / "manifest.json"))
            result = ops.copy(str(source), str(dest))
            
            assert result is True
            assert source.exists()  # Source still exists
            assert dest.exists()
            assert dest.read_text() == "test content"
    
    def test_save_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            manifest_path = tmpdir / "manifest.json"
            
            # Create some files to operate on
            source = tmpdir / "source.txt"
            dest = tmpdir / "dest.txt"
            source.write_text("test")
            
            ops = SafeFileOperations(str(manifest_path))
            ops.move(str(source), str(dest))
            saved_path = ops.save_manifest()
            
            assert Path(saved_path).exists()
            
            with open(saved_path) as f:
                manifest = json.load(f)
            
            assert "operations" in manifest
            assert len(manifest["operations"]) == 1
            assert manifest["operations"][0]["operation_type"] == "move"


class TestRollback:
    """Tests for rollback functionality."""
    
    def test_rollback_move(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            original = tmpdir / "original.txt"
            moved = tmpdir / "moved.txt"
            manifest_path = tmpdir / "manifest.json"
            
            original.write_text("original content")
            
            # Perform move
            ops = SafeFileOperations(str(manifest_path))
            ops.move(str(original), str(moved))
            ops.save_manifest()
            
            # Verify move happened
            assert not original.exists()
            assert moved.exists()
            
            # Rollback
            results = SafeFileOperations.rollback_from_manifest(str(manifest_path))
            
            assert results["rolled_back"] == 1
            assert results["failed"] == 0
            assert original.exists()
            assert not moved.exists()
    
    def test_rollback_copy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source = tmpdir / "source.txt"
            copied = tmpdir / "copied.txt"
            manifest_path = tmpdir / "manifest.json"
            
            source.write_text("content")
            
            # Perform copy
            ops = SafeFileOperations(str(manifest_path))
            ops.copy(str(source), str(copied))
            ops.save_manifest()
            
            # Verify copy
            assert source.exists()
            assert copied.exists()
            
            # Rollback should remove the copy
            results = SafeFileOperations.rollback_from_manifest(str(manifest_path))
            
            assert results["rolled_back"] == 1
            assert source.exists()  # Original still there
            assert not copied.exists()  # Copy removed


class TestCleanup:
    """Tests for cleanup utilities."""
    
    def test_cleanup_empty_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create nested empty directories
            (tmpdir / "a" / "b" / "c").mkdir(parents=True)
            (tmpdir / "a" / "b" / "d").mkdir(parents=True)
            
            # Create a directory with a file (shouldn't be removed)
            (tmpdir / "keep").mkdir()
            (tmpdir / "keep" / "file.txt").write_text("keep me")
            
            removed = cleanup_empty_directories(str(tmpdir / "a"))
            
            assert removed >= 3  # a, b, c, d all empty
            assert not (tmpdir / "a").exists()
            assert (tmpdir / "keep").exists()
    
    def test_cleanup_nonexistent_path(self):
        removed = cleanup_empty_directories("/nonexistent/path")
        assert removed == 0


class TestCreateParents:
    """Tests for parent directory creation."""
    
    def test_move_creates_parents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            source = tmpdir / "source.txt"
            dest = tmpdir / "a" / "b" / "c" / "dest.txt"
            
            source.write_text("content")
            
            ops = SafeFileOperations()
            result = ops.move(str(source), str(dest), create_parents=True)
            
            assert result is True
            assert dest.exists()
            assert dest.parent.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

